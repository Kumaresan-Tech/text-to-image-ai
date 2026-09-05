import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const possibleDirs = [
      path.resolve(process.cwd(), "..", "outputs"),
      path.resolve(process.cwd(), "outputs"),
      path.resolve("/tmp", "outputs"),
    ];

    const targetDir = possibleDirs.find((d) => fs.existsSync(d));

    if (!targetDir) {
      return NextResponse.json({ images: [] });
    }

    const files = fs.readdirSync(targetDir);
    const pngFiles = files
      .filter((f) => (f.endsWith(".png") || f.endsWith(".jpg")) && f !== "generated_image.png")
      .map((f) => {
        const fullPath = path.join(targetDir, f);
        const stat = fs.statSync(fullPath);
        return {
          filename: f,
          url: `/outputs/${f}`,
          mtime: stat.mtimeMs,
          created_at: new Date(stat.mtimeMs).toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          }),
        };
      })
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, 30);

    return NextResponse.json({ images: pngFiles });
  } catch (error: any) {
    return NextResponse.json({ images: [], error: error.message }, { status: 500 });
  }
}
