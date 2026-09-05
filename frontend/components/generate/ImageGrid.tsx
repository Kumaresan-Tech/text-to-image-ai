"use client";

import { useState } from "react";
import { Loader2, Download, Heart, X, Copy, Maximize2, Settings2, Clock, Share2, Trash2 } from "lucide-react";

export interface ImageItem {
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
  likes_count?: number;
  created_at: string;
  is_favorited?: boolean;
  tags?: string[];
  is_public?: boolean;
}

interface ImageGridProps {
  images: ImageItem[];
  isGenerating?: boolean;
  progressMessage?: string;
  onFavorite?: (id: string) => void;
  onShare?: (id: string) => void;
  onDelete?: (id: string) => void;
  onDownload?: (image: ImageItem) => void;
}

export function ImageGrid({
  images,
  isGenerating,
  progressMessage,
  onFavorite,
  onShare,
  onDelete,
  onDownload,
}: ImageGridProps) {
  const [selected, setSelected] = useState<ImageItem | null>(null);
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  if (isGenerating && images.length === 0) {
    return (
      <div className="glass rounded-xl h-96 flex flex-col items-center justify-center gap-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">{progressMessage || "Generating your image..."}</p>
      </div>
    );
  }

  if (images.length === 0) {
    return (
      <div className="glass rounded-xl h-96 flex flex-col items-center justify-center gap-4">
        <div className="w-20 h-20 rounded-2xl bg-primary/5 flex items-center justify-center">
          <Maximize2 className="h-8 w-8 text-primary/20" />
        </div>
        <div className="text-center space-y-1">
          <p className="text-sm font-medium text-muted-foreground">Ready to create</p>
          <p className="text-xs text-muted-foreground/60">Write a prompt and click Generate</p>
        </div>
      </div>
    );
  }

  function copyPrompt(prompt: string) {
    navigator.clipboard.writeText(prompt);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  }

  async function downloadImage(img: ImageItem) {
    if (onDownload) {
      onDownload(img);
      return;
    }
    try {
      const res = await fetch(img.image_url);
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = blobUrl;
      a.download = `aura-${img.id}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);
    } catch {
      const a = document.createElement("a");
      a.href = img.image_url;
      a.download = `aura-${img.id}.png`;
      a.target = "_blank";
      a.click();
    }
  }

  return (
    <>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {images.map((img) => (
          <div
            key={img.id}
            className="glass rounded-xl overflow-hidden cursor-pointer group relative"
            onClick={() => setSelected(img)}
          >
            <img
              src={img.image_url}
              alt={img.prompt}
              className="w-full aspect-square object-cover transition-transform group-hover:scale-[1.02]"
              loading="lazy"
            />

            {/* Hover overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              {/* Action buttons (top-right) */}
              <div className="absolute top-2 right-2 flex gap-1">
                {onFavorite && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onFavorite(img.id); }}
                    className={`h-7 w-7 rounded-full backdrop-blur-sm flex items-center justify-center transition-colors ${
                      img.is_favorited
                        ? "bg-red-500/80 text-white"
                        : "bg-black/40 text-white/70 hover:bg-black/60 hover:text-white"
                    }`}
                    title={img.is_favorited ? "Remove from favorites" : "Add to favorites"}
                  >
                    <Heart className={`h-3.5 w-3.5 ${img.is_favorited ? "fill-current" : ""}`} />
                  </button>
                )}
                {onShare && (
                  <button
                    onClick={(e) => { e.stopPropagation(); onShare(img.id); }}
                    className="h-7 w-7 rounded-full bg-black/40 backdrop-blur-sm text-white/70 hover:bg-black/60 hover:text-white flex items-center justify-center transition-colors"
                    title="Share"
                  >
                    <Share2 className="h-3.5 w-3.5" />
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); downloadImage(img); }}
                  className="h-7 w-7 rounded-full bg-black/40 backdrop-blur-sm text-white/70 hover:bg-black/60 hover:text-white flex items-center justify-center transition-colors"
                  title="Download"
                >
                  <Download className="h-3.5 w-3.5" />
                </button>
              </div>

              {/* Bottom info */}
              <div className="absolute bottom-0 left-0 right-0 p-3 space-y-1">
                <p className="text-xs text-white/90 line-clamp-2">{img.prompt}</p>
                <div className="flex items-center gap-3 text-[10px] text-white/50">
                  <span>{img.width}x{img.height}</span>
                  <span>{img.steps} steps</span>
                  <span className="flex items-center gap-0.5">
                    <Heart className="h-2.5 w-2.5" /> {img.likes_count || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox Modal */}
      {selected && (
        <div
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center p-4 md:p-8"
          onClick={() => setSelected(null)}
        >
          <div className="relative max-w-5xl w-full flex flex-col lg:flex-row gap-4" onClick={(e) => e.stopPropagation()}>
            {/* Image */}
            <div className="flex-1 relative">
              <img
                src={selected.image_url}
                alt={selected.prompt}
                className="w-full max-h-[75vh] object-contain rounded-xl"
              />
              <button
                onClick={() => setSelected(null)}
                className="absolute top-2 right-2 h-8 w-8 rounded-full bg-black/60 hover:bg-black/80 flex items-center justify-center text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Metadata Panel */}
            <div className="lg:w-80 glass rounded-xl p-4 space-y-4 max-h-[75vh] overflow-y-auto">
              <div>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Prompt</h3>
                <p className="text-sm leading-relaxed">{selected.prompt}</p>
              </div>

              {selected.negative_prompt && (
                <div>
                  <h3 className="text-xs font-semibold text-destructive/80 uppercase tracking-wider mb-2">Negative</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{selected.negative_prompt}</p>
                </div>
              )}

              <div className="border-t border-border pt-3 space-y-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                  <Settings2 className="h-3 w-3" /> Parameters
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { label: "Model", value: selected.model },
                    { label: "Size", value: `${selected.width}x${selected.height}` },
                    { label: "Steps", value: selected.steps },
                    { label: "CFG", value: selected.cfg_scale },
                    { label: "Sampler", value: selected.sampler?.split(" ")[0] },
                    { label: "Seed", value: selected.seed ?? "random" },
                  ].map(({ label, value }) => (
                    <div key={label} className="bg-secondary/30 rounded-md px-2 py-1.5">
                      <span className="text-muted-foreground">{label}: </span>
                      <span className="font-mono">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {selected.tags && selected.tags.length > 0 && (
                <div className="border-t border-border pt-3">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-1">
                    {selected.tags.map((tag) => (
                      <span key={tag} className="h-6 px-2 rounded-full bg-secondary/50 text-[10px] text-muted-foreground">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {new Date(selected.created_at).toLocaleString()}
              </div>

              {/* Action buttons */}
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => downloadImage(selected)}
                  className="flex-1 flex items-center justify-center gap-1.5 h-9 rounded-lg bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white text-sm font-semibold shadow transition-colors"
                >
                  <Download className="h-3.5 w-3.5" /> Download HD PNG
                </button>
                <button
                  onClick={() => copyPrompt(selected.prompt)}
                  className="h-9 w-9 rounded-lg border border-input bg-background flex items-center justify-center hover:bg-accent transition-colors"
                  title="Copy prompt"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
                {onFavorite && (
                  <button
                    onClick={() => onFavorite(selected.id)}
                    className={`h-9 w-9 rounded-lg border flex items-center justify-center transition-colors ${
                      selected.is_favorited
                        ? "border-red-500 bg-red-500/10 text-red-500"
                        : "border-input bg-background hover:bg-accent"
                    }`}
                    title={selected.is_favorited ? "Unfavorite" : "Favorite"}
                  >
                    <Heart className={`h-3.5 w-3.5 ${selected.is_favorited ? "fill-current" : ""}`} />
                  </button>
                )}
                {onShare && (
                  <button
                    onClick={() => onShare(selected.id)}
                    className="h-9 w-9 rounded-lg border border-input bg-background flex items-center justify-center hover:bg-accent transition-colors"
                    title="Share"
                  >
                    <Share2 className="h-3.5 w-3.5" />
                  </button>
                )}
                {onDelete && (
                  <button
                    onClick={() => { onDelete(selected.id); setSelected(null); }}
                    className="h-9 w-9 rounded-lg border border-destructive/30 bg-destructive/5 text-destructive flex items-center justify-center hover:bg-destructive/10 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
