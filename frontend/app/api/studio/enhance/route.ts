import { NextResponse } from "next/server";

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
  try {
    const body = await req.json();
    const prompt = (body.prompt || "").trim();
    const styleKey = body.style || "cinematic";

    if (!prompt) {
      return NextResponse.json({ error: "Prompt is required" }, { status: 400 });
    }

    const styleInfo = STYLE_PRESETS[styleKey] || STYLE_PRESETS.cinematic;
    const apiKey = process.env.GEMINI_API_KEY || "";

    let enhancedPrompt = prompt;

    if (apiKey) {
      try {
        const instruction = `You are an expert AI image prompt engineer.
Convert the user's request into an ultra high-quality, vivid, and descriptive prompt for an AI image generator (FLUX.1).

Style Directive: ${styleInfo.name} (${styleInfo.suffix})

Ensure the prompt includes:
- Distinct subject features, expression, and realistic anatomy
- Rich atmospheric environment and depth
- Dramatic lighting (e.g. volumetric rays, natural rim light, softbox reflections)
- Camera perspective, lens type (e.g. 35mm, 85mm portrait lens)
- Intricate micro-textures and vivid color palette

Return ONLY the final enhanced prompt text without any quotes, preambles, or markdown formatting.

User Request: ${prompt}`;

        const response = await fetch(
          "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
          {
            method: "POST",
            headers: {
              "x-goog-api-key": apiKey,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              contents: [{ parts: [{ text: instruction }] }],
              generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 350,
              },
            }),
          }
        );

        if (response.ok) {
          const data = await response.json();
          const candidateText =
            data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();
          if (candidateText) {
            enhancedPrompt = candidateText;
          }
        }
      } catch (geminiError) {
        console.warn("Gemini prompt enhancement fallback:", geminiError);
      }
    }

    // Fallback if Gemini wasn't able to enhance
    if (enhancedPrompt === prompt) {
      enhancedPrompt = `${prompt}, ${styleInfo.suffix}`;
    }

    return NextResponse.json({
      success: true,
      enhanced_prompt: enhancedPrompt,
      original_prompt: prompt,
      style: styleKey,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || "Enhancement failed" },
      { status: 500 }
    );
  }
}
