"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, ArrowRight, Download, Eye, X, Copy, Check, Sparkles } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

interface RecentImage {
  id: string;
  prompt: string;
  image_url: string;
  model: string;
  likes_count: number;
  created_at: string;
}

interface RecentGenerationsProps {
  images: RecentImage[];
}

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.05 } },
};

const itemVariants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.35, ease: "easeOut" } },
  exit: { opacity: 0, scale: 0.9, transition: { duration: 0.2 } },
};

async function downloadImageFile(url: string, filename: string) {
  try {
    const res = await fetch(url);
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = blobUrl;
    a.download = filename.endsWith(".png") ? filename : `${filename}.png`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(blobUrl);
    document.body.removeChild(a);
  } catch {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.endsWith(".png") ? filename : `${filename}.png`;
    a.target = "_blank";
    a.click();
  }
}

export function RecentGenerations({ images }: RecentGenerationsProps) {
  const [selected, setSelected] = useState<RecentImage | null>(null);
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleCopyPrompt = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = async (img: RecentImage) => {
    setIsDownloading(true);
    await downloadImageFile(img.image_url, img.id || `aura_${Date.now()}`);
    setIsDownloading(false);
  };

  if (images.length === 0) {
    return (
      <div className="glass rounded-xl p-8 text-center">
        <p className="text-sm text-muted-foreground">No images generated yet</p>
        <Link
          href="/generate"
          className="mt-3 inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
        >
          Create your first image <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold">Recent Generations</h2>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
              {images.length}
            </span>
          </div>
          <Link
            href="/studio"
            className="text-xs text-primary hover:underline flex items-center gap-1 font-medium transition-colors"
          >
            Open Studio <ArrowRight className="h-3 w-3" />
          </Link>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-2 md:grid-cols-4 gap-3"
        >
          <AnimatePresence mode="popLayout">
            {images.map((img) => (
              <motion.div
                key={img.id}
                variants={itemVariants}
                layout
                whileHover={{ y: -3, transition: { duration: 0.2 } }}
                onClick={() => setSelected(img)}
                className="glass rounded-xl overflow-hidden group cursor-pointer border border-white/5 hover:border-primary/40 transition-colors relative"
              >
                <div className="relative aspect-square overflow-hidden bg-black/40">
                  <img
                    src={img.image_url}
                    alt={img.prompt}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                  
                  {/* Top Action Badge */}
                  <div className="absolute top-2 right-2 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownload(img);
                      }}
                      title="Download HD PNG"
                      className="p-1.5 rounded-lg bg-black/60 hover:bg-primary text-white backdrop-blur-md transition shadow-md"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelected(img);
                      }}
                      title="Quick View"
                      className="p-1.5 rounded-lg bg-black/60 hover:bg-cyan-600 text-white backdrop-blur-md transition shadow-md"
                    >
                      <Eye className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  {/* Bottom Prompt Preview */}
                  <div className="absolute bottom-2 left-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <p className="text-[10px] text-white/95 line-clamp-2 leading-tight font-medium drop-shadow-sm">
                      {img.prompt}
                    </p>
                  </div>
                </div>

                <div className="p-2.5 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] text-primary font-semibold">{img.model}</p>
                    <div className="flex items-center gap-1 mt-0.5 text-[9px] text-muted-foreground">
                      <Clock className="h-2.5 w-2.5" />
                      {img.created_at}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDownload(img);
                    }}
                    className="text-[10px] flex items-center gap-1 text-muted-foreground hover:text-primary transition font-medium px-2 py-1 rounded bg-secondary/40 hover:bg-primary/15"
                  >
                    <Download className="h-3 w-3" />
                    <span>PNG</span>
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* High-Resolution Preview Modal / Lightbox */}
      <AnimatePresence>
        {selected && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
            onClick={() => setSelected(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-[#0c101d] border border-white/10 rounded-2xl max-w-4xl w-full overflow-hidden shadow-2xl flex flex-col md:flex-row max-h-[90vh]"
            >
              {/* Image Preview Container */}
              <div className="md:w-3/5 bg-black flex items-center justify-center p-4 relative min-h-[300px]">
                <img
                  src={selected.image_url}
                  alt={selected.prompt}
                  className="max-h-[75vh] w-auto max-w-full object-contain rounded-lg shadow-lg"
                />
              </div>

              {/* Image Details Sidebar */}
              <div className="md:w-2/5 p-6 flex flex-col justify-between border-t md:border-t-0 md:border-l border-white/10 space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-purple-400" />
                      <span className="text-xs font-semibold text-purple-300 uppercase tracking-wide">
                        {selected.model}
                      </span>
                    </div>
                    <button
                      onClick={() => setSelected(null)}
                      className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>

                  <div>
                    <label className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                      Prompt
                    </label>
                    <div className="mt-1.5 p-3 rounded-xl bg-black/40 border border-white/5 text-xs text-slate-200 relative group">
                      <p className="line-clamp-6 leading-relaxed">{selected.prompt}</p>
                      <button
                        onClick={() => handleCopyPrompt(selected.prompt)}
                        className="mt-2 inline-flex items-center gap-1.5 text-[11px] text-cyan-400 hover:text-cyan-300 font-medium"
                      >
                        {copied ? (
                          <>
                            <Check className="h-3 w-3 text-green-400" />
                            <span className="text-green-400">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span>Copy Prompt</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 rounded-xl bg-white/5">
                      <span className="text-[10px] text-slate-400 block">Resolution</span>
                      <span className="font-semibold text-white">1024 × 1024 HD</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white/5">
                      <span className="text-[10px] text-slate-400 block">Created</span>
                      <span className="font-semibold text-white">{selected.created_at}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 pt-2">
                  <Button
                    onClick={() => handleDownload(selected)}
                    disabled={isDownloading}
                    className="w-full h-11 bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white font-semibold gap-2 shadow-lg shadow-purple-500/20"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download HD Image (.PNG)</span>
                  </Button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
