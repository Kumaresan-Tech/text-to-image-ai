"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { PromptInput } from "@/components/generate/PromptInput";
import { ParamsPanel } from "@/components/generate/ParamsPanel";
import { ImageGrid } from "@/components/generate/ImageGrid";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";
import { useGenerationStore } from "@/stores/generationStore";
import { AlertCircle } from "lucide-react";

const DEFAULT_PARAMS = {
  width: 1024,
  height: 1024,
  steps: 4,
  cfg_scale: 0.0,
  sampler: "DPM++ 2M Karras",
  seed: -1,
  model: "hf-flux",
  negative_prompt: "",
  is_public: false,
  num_images: 1,
};

function GenerateContent() {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");

  const { images, isGenerating, progress, progressMessage, error, resetError } = useGenerationStore();

  useEffect(() => {
    if (images.length === 0) {
      fetch("/api/studio/history")
        .then((r) => r.json())
        .then((data) => {
          if (data.images && data.images.length > 0) {
            const mapped = data.images.map((img: any) => ({
              id: img.filename,
              user_id: "",
              prompt: img.filename.replace(/aura_\d+_\d+\.png/, "FLUX Studio Creation").replace(/\.png$/, ""),
              image_url: img.url,
              thumbnail_url: img.url,
              width: 1024,
              height: 1024,
              steps: 4,
              cfg_scale: 0.0,
              sampler: "DPM++ 2M Karras",
              model: "FLUX.1 Schnell",
              is_public: true,
              likes_count: 0,
              created_at: img.created_at,
            }));
            useGenerationStore.setState({ images: mapped });
          }
        })
        .catch(() => {});
    }
  }, []);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    useGenerationStore.getState().submitGeneration(prompt, { ...params, negative_prompt: negativePrompt });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 flex items-center gap-3 glass rounded-xl px-4 py-3 text-sm border border-destructive/30"
        >
          <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
          <span className="flex-1">{error}</span>
          <button onClick={resetError} className="text-xs text-muted-foreground hover:text-foreground">
            Dismiss
          </button>
        </motion.div>
      )}

      <div className="grid lg:grid-cols-[1fr_340px] gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-4"
        >
          <ImageGrid
            images={images}
            isGenerating={isGenerating}
            progressMessage={progressMessage}
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="space-y-4 lg:sticky lg:top-20 lg:self-start"
        >
          <PromptInput
            prompt={prompt}
            negativePrompt={negativePrompt}
            currentModel={params.model}
            onPromptChange={setPrompt}
            onNegativeChange={setNegativePrompt}
            onGenerate={handleGenerate}
          />
          <ParamsPanel params={params} onChange={setParams} />
        </motion.div>
      </div>
    </div>
  );
}

export default function GeneratePage() {
  return (
    <ProtectedRoute allowGuest={true}>
      <GenerateContent />
    </ProtectedRoute>
  );
}
