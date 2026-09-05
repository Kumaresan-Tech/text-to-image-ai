"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import { ImageGrid, ImageItem } from "@/components/generate/ImageGrid";
import { ImageToolbar, ImageFilters } from "@/components/history/ImageToolbar";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { ShareDialog } from "@/components/shared/ShareDialog";
import { useAuth } from "@/hooks/useAuth";
import { imagesApi } from "@/lib/api";
import { LayoutGrid, BarChart3, Heart, Share2, Globe, Image as ImageIcon } from "lucide-react";

function MyImagesContent() {
  const { token } = useAuth();
  const [images, setImages] = useState<ImageItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("all");
  const [stats, setStats] = useState({ total_images: 0, total_favorites: 0, total_public: 0, total_shares: 0 });

  const [filters, setFilters] = useState<ImageFilters>({
    q: "",
    model: "",
    sampler: "",
    dateFrom: "",
    dateTo: "",
    isFavorited: null,
    sortBy: "created_at",
    sortOrder: "desc",
  });

  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [shareTarget, setShareTarget] = useState<string | null>(null);

  const loadImages = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filters.q) params.q = filters.q;
      if (filters.model) params.model = filters.model;
      if (filters.sampler) params.sampler = filters.sampler;
      if (filters.dateFrom) params.date_from = filters.dateFrom;
      if (filters.dateTo) params.date_to = filters.dateTo;
      if (filters.isFavorited) params.is_favorited = "true";
      params.sort_by = filters.sortBy;
      params.sort_order = filters.sortOrder;

      const data = await imagesApi.list(page, 20, token, params);
      setImages(data.images);
      setHasNext(data.has_next);
      setTotal(data.total);
    } catch {
    } finally {
      setLoading(false);
    }
  }, [page, filters, token]);

  const loadStats = useCallback(async () => {
    if (!token) return;
    try {
      const data = await imagesApi.stats(token);
      setStats(data);
    } catch {
    }
  }, [token]);

  useEffect(() => { loadImages(); }, [loadImages]);
  useEffect(() => { loadStats(); }, [loadStats]);

  useEffect(() => {
    setPage(1);
  }, [filters, activeTab]);

  async function handleFavorite(id: string) {
    if (!token) return;
    try {
      const result = await imagesApi.favorite(id, token);
      setImages((prev) =>
        prev.map((img) =>
          img.id === id
            ? { ...img, is_favorited: result.is_favorited, likes_count: result.favorites_count }
            : img
        )
      );
      loadStats();
    } catch {
    }
  }

  async function handleDelete(id: string) {
    if (!token) return;
    try {
      await imagesApi.remove(id, token);
      setImages((prev) => prev.filter((img) => img.id !== id));
      setTotal((prev) => prev - 1);
      loadStats();
      setDeleteTarget(null);
    } catch {
    }
  }

  function handleDownload(img: ImageItem) {
    const a = document.createElement("a");
    a.href = img.image_url;
    a.download = `ai-image-${img.id.slice(0, 8)}.png`;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  function handleTabChange(tab: string) {
    setActiveTab(tab);
    if (tab === "favorites") {
      setFilters((f) => ({ ...f, isFavorited: true }));
    } else {
      setFilters((f) => ({ ...f, isFavorited: null }));
    }
  }

  const statCards = [
    { icon: ImageIcon, label: "Total", value: stats.total_images, color: "text-primary" },
    { icon: Heart, label: "Favorites", value: stats.total_favorites, color: "text-red-500" },
    { icon: Globe, label: "Public", value: stats.total_public, color: "text-green-500" },
    { icon: Share2, label: "Shared", value: stats.total_shares, color: "text-blue-500" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold">Image History</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage and organize your generated images</p>
        </div>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {statCards.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.1 + i * 0.06, duration: 0.35 }}
            whileHover={{ y: -2 }}
            className="glass rounded-xl p-3 flex items-center gap-3"
          >
            <div className="h-9 w-9 rounded-lg bg-secondary/30 flex items-center justify-center">
              <s.icon className={`h-4 w-4 ${s.color}`} />
            </div>
            <div>
              <p className="text-lg font-semibold">{s.value}</p>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{s.label}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <ImageToolbar
        filters={filters}
        onFiltersChange={setFilters}
        total={total}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />

      {loading ? (
        <div className="glass rounded-xl h-64 flex items-center justify-center">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ImageGrid
          images={images}
          onFavorite={handleFavorite}
          onShare={setShareTarget}
          onDelete={setDeleteTarget}
          onDownload={handleDownload}
        />
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

      <ConfirmDialog
        open={!!deleteTarget}
        title="Delete Image"
        message="This action cannot be undone. The image will be permanently removed from your account."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={() => deleteTarget && handleDelete(deleteTarget)}
        onCancel={() => setDeleteTarget(null)}
      />

      {shareTarget && token && (
        <ShareDialog
          open={!!shareTarget}
          imageId={shareTarget}
          token={token}
          onClose={() => setShareTarget(null)}
        />
      )}
    </div>
  );
}

export default function MyImagesPage() {
  return (
    <ProtectedRoute>
      <MyImagesContent />
    </ProtectedRoute>
  );
}
