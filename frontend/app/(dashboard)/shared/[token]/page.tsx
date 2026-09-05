"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { imagesApi } from "@/lib/api";
import { Loader2, Download, Heart, Settings2, Clock, User } from "lucide-react";

interface SharedImage {
  id: string;
  prompt: string;
  negative_prompt?: string;
  image_url: string;
  width: number;
  height: number;
  steps: number;
  cfg_scale: number;
  sampler: string;
  seed?: number;
  model: string;
  likes_count: number;
  created_at: string;
  shared_by?: string;
}

export default function SharedImagePage() {
  const params = useParams();
  const token = params.token as string;
  const [image, setImage] = useState<SharedImage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) loadShared();
  }, [token]);

  async function loadShared() {
    try {
      const data = await imagesApi.getShared(token);
      setImage(data);
    } catch (err: any) {
      setError(err.message || "Failed to load shared image");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !image) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-2">
          <p className="text-lg font-semibold">Image not found</p>
          <p className="text-sm text-muted-foreground">{error || "This share link may have expired"}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="glass rounded-xl overflow-hidden">
          <img
            src={image.image_url}
            alt={image.prompt}
            className="w-full max-h-[70vh] object-contain"
          />
        </div>

        <div className="glass rounded-xl p-5 space-y-4">
          <div>
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Prompt</h3>
            <p className="text-sm leading-relaxed">{image.prompt}</p>
          </div>

          {image.negative_prompt && (
            <div>
              <h3 className="text-xs font-semibold text-destructive/80 uppercase tracking-wider mb-2">Negative</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">{image.negative_prompt}</p>
            </div>
          )}

          <div className="border-t border-border pt-3 space-y-2">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
              <Settings2 className="h-3 w-3" /> Parameters
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              {[
                { label: "Model", value: image.model },
                { label: "Size", value: `${image.width}x${image.height}` },
                { label: "Steps", value: image.steps },
                { label: "CFG", value: image.cfg_scale },
                { label: "Sampler", value: image.sampler?.split(" ")[0] },
                { label: "Seed", value: image.seed ?? "random" },
              ].map(({ label, value }) => (
                <div key={label} className="bg-secondary/30 rounded-md px-2 py-1.5">
                  <span className="text-muted-foreground">{label}: </span>
                  <span className="font-mono">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-border pt-3">
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              {image.shared_by && (
                <span className="flex items-center gap-1">
                  <User className="h-3 w-3" /> {image.shared_by}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(image.created_at).toLocaleDateString()}
              </span>
              <span className="flex items-center gap-1">
                <Heart className="h-3 w-3" /> {image.likes_count}
              </span>
            </div>

            <a
              href={image.image_url}
              download
              className="h-9 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors flex items-center gap-1.5"
            >
              <Download className="h-3.5 w-3.5" /> Download
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
