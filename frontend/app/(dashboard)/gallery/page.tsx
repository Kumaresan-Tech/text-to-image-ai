"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { ImageGrid, ImageItem } from "@/components/generate/ImageGrid";
import { imagesApi, galleryApi } from "@/lib/api";
import { Search, X, Globe } from "lucide-react";

const MODELS = [
  { value: "", label: "All Models" },
  { value: "demo", label: "Demo (Free)" },
  { value: "sdxl-1.0", label: "SDXL 1.0" },
  { value: "sd-3.5-large", label: "SD 3.5 Large" },
  { value: "flux-dev", label: "Flux Dev" },
  { value: "flux-schnell", label: "Flux Schnell" },
  { value: "hf-sdxl", label: "HF SDXL" },
  { value: "replicate-flux", label: "Replicate Flux" },
  { value: "gemini-imagen", label: "Gemini Imagen" },
];

export default function GalleryPage() {
  const [images, setImages] = useState<ImageItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchGallery = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ page: String(page), per_page: "20" });
      if (searchQuery) qs.set("q", searchQuery);
      if (selectedModel) qs.set("model", selectedModel);

      let fetchedImages: ImageItem[] = [];
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/gallery?${qs}`);
        if (res.ok) {
          const data = await res.json();
          fetchedImages = data.images || [];
          setHasNext(data.has_next);
          setTotal(data.total);
        }
      } catch {}

      if (fetchedImages.length === 0) {
        try {
          const hRes = await fetch("/api/studio/history");
          const hData = await hRes.json();
          fetchedImages = (hData.images || []).map((img: any) => ({
            id: img.filename,
            prompt: img.filename.replace(/aura_\d+_\d+\.png/, "FLUX Studio Creation").replace(/\.png$/, ""),
            image_url: img.url,
            width: 1024,
            height: 1024,
            steps: 4,
            cfg_scale: 0.0,
            sampler: "DPM++ 2M Karras",
            model: "FLUX.1 Schnell",
            likes_count: 0,
            created_at: img.created_at,
            is_public: true,
          }));
          setTotal(fetchedImages.length);
          setHasNext(false);
        } catch {}
      }
      setImages(fetchedImages);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, selectedModel]);

  useEffect(() => { fetchGallery(); }, [fetchGallery]);
  useEffect(() => { setPage(1); }, [searchQuery, selectedModel]);

  function handleFavorite() {
    // Guest users can't favorite — show login prompt
    alert("Please log in to favorite images");
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.1 }}
            className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center"
          >
            <Globe className="h-5 w-5 text-primary" />
          </motion.div>
          <div>
            <h1 className="text-2xl font-bold">Public Gallery</h1>
            <p className="text-sm text-muted-foreground">{total} images shared by the community</p>
          </div>
        </div>
      </motion.div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search gallery..."
            className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 h-5 w-5 rounded-md hover:bg-muted flex items-center justify-center"
            >
              <X className="h-3 w-3 text-muted-foreground" />
            </button>
          )}
        </div>

        <select
          value={selectedModel}
          onChange={(e) => setSelectedModel(e.target.value)}
          className="h-9 rounded-lg border border-input bg-background px-3 text-sm"
        >
          {MODELS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="glass rounded-xl h-64 flex items-center justify-center">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ImageGrid images={images} onFavorite={handleFavorite} />
      )}

      <div className="flex justify-center gap-4 mt-6">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="h-9 px-4 rounded-lg border border-input bg-background text-sm font-medium disabled:opacity-50 hover:bg-accent transition-colors"
        >
          Previous
        </button>
        <span className="h-9 px-4 rounded-lg bg-secondary/30 text-sm text-muted-foreground flex items-center">
          Page {page}
        </span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={!hasNext}
          className="h-9 px-4 rounded-lg border border-input bg-background text-sm font-medium disabled:opacity-50 hover:bg-accent transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
