import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

const STYLE_PRESETS: Record<string, { name: string; suffix: string }> = {
  cinematic: {
    name: "Cinematic",
    suffix: "cinematic composition, 35mm photography, dramatic volumetric rim lighting, shallow depth of field, color graded, masterpiece 8k, Unreal Engine 5, hyperrealistic textures",
  },
  photorealistic: {
    name: "Photorealism",
    suffix: "extreme photorealism, raw photo, detailed anatomy, subsurface scattering, micro-textures, 85mm portrait lens, f/1.4 aperture, natural softbox lighting, 8k resolution",
  },
  cyberpunk: {
    name: "Cyberpunk",
    suffix: "futuristic cyberpunk aesthetic, neon cyan and magenta caustics, wet reflective surfaces, atmospheric fog, intricate high-tech mechanical details, cinematic wide angle, ray tracing",
  },
  fantasy: {
    name: "Fantasy Art",
    suffix: "mythical fantasy concept art, ethereal volumetric glow, luminous bioluminescent particles, vivid iridescent colors, ArtStation trending, Octane render, ultra detailed illustration",
  },
  anime: {
    name: "Anime / Manga",
    suffix: "stunning anime visual aesthetic, Makoto Shinkai inspired, vibrant dramatic skies, clean crisp line art, beautiful atmospheric lighting, highly detailed masterpiece 4k",
  },
  "3d_render": {
    name: "3D Octane",
    suffix: "3D isometric render, premium clay and glass materials, vibrant pastel lighting, tilt-shift lens, Octane render, ray-traced ambient occlusion, C4D showcase",
  },
};

export async function POST(req: Request) {
  const startTime = Date.now();
  try {
    const body = await req.json();
    const rawPrompt = (body.prompt || "").trim();
    const styleKey = body.style || "cinematic";
    const width = Number(body.width) || 1024;
    const height = Number(body.height) || 1024;
    const modelChoice = body.model || "flux-schnell";
    const seed = body.seed && body.seed > 0 ? body.seed : Math.floor(Math.random() * 2147483647);

    if (!rawPrompt) {
      return NextResponse.json({ error: "Prompt is required" }, { status: 400 });
    }

    const styleInfo = STYLE_PRESETS[styleKey] || STYLE_PRESETS.cinematic;
    let finalPrompt = rawPrompt;
    if (!finalPrompt.toLowerCase().includes(styleInfo.name.toLowerCase())) {
      finalPrompt = `${rawPrompt}, ${styleInfo.suffix}`;
    }

    const encoded = encodeURIComponent(finalPrompt);

    // Multi-tier resilient generation pipeline
    const candidateUrls = [
      `https://image.pollinations.ai/prompt/${encoded}?model=flux&width=${width}&height=${height}&seed=${seed}&nologo=true`,
      `https://image.pollinations.ai/prompt/${encoded}?width=${width}&height=${height}&nologo=true`,
      `https://image.pollinations.ai/prompt/${encoded}?model=turbo&width=${width}&height=${height}&seed=${seed}&nologo=true`,
    ];

    let imageBuffer: Buffer | null = null;
    let successfulUrl = "";

    const headers = {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    };

    for (const url of candidateUrls) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 40000);

        const res = await fetch(url, {
          headers,
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (res.ok) {
          const arrayBuf = await res.arrayBuffer();
          if (arrayBuf.byteLength > 2000) {
            imageBuffer = Buffer.from(arrayBuf);
            successfulUrl = url;
            break;
          }
        }
      } catch (tierError) {
        console.warn(`Generation candidate error on ${url}:`, tierError);
      }
    }

    if (!imageBuffer) {
      return NextResponse.json(
        { error: "Generation servers are currently overloaded. Please retry in a few seconds." },
        { status: 502 }
      );
    }

    const timestamp = new Date().toISOString().replace(/[-:T.]/g, "").slice(0, 14);
    const filename = `aura_${timestamp}_${Math.floor(Math.random() * 1000)}.png`;

    // Resilient file saving (supports native dev, parent outputs, and container /tmp/outputs)
    const possibleDirs = [
      path.resolve(process.cwd(), "..", "outputs"),
      path.resolve(process.cwd(), "outputs"),
      path.resolve("/tmp", "outputs"),
    ];

    for (const dir of possibleDirs) {
      try {
        if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
        fs.writeFileSync(path.join(dir, filename), imageBuffer);
        fs.writeFileSync(path.join(dir, "generated_image.png"), imageBuffer);
        break;
      } catch {
        // Try next writable candidate
      }
    }

    const elapsedSeconds = Number(((Date.now() - startTime) / 1000).toFixed(2));
    const base64Data = imageBuffer.toString("base64");
    const dataUrl = `data:image/png;base64,${base64Data}`;

    return NextResponse.json({
      success: true,
      filename,
      image_url: dataUrl,
      file_url: `/outputs/${filename}`,
      final_prompt: finalPrompt,
      original_prompt: rawPrompt,
      style: styleKey,
      model: modelChoice === "flux-dev" ? "FLUX.1 Dev (8K Pro)" : "FLUX.1 Schnell",
      width,
      height,
      seed,
      elapsed_seconds: elapsedSeconds,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Image generation failed" },
      { status: 500 }
    );
  }
}
