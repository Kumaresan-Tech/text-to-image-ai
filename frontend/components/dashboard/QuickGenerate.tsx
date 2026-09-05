"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Loader2, X, Wand2, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useGenerationStore } from "@/stores/generationStore";
import Link from "next/link";

const QUICK_MODELS = [
  { id: "hf-flux", label: "Flux Fast (Schnell)" },
  { id: "flux-dev", label: "Flux Dev (High Res)" },
  { id: "demo", label: "Demo Free (FLUX)" },
  { id: "sdxl-1.0", label: "SDXL" },
];

export function QuickGenerate() {
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("hf-flux");
  const { isGenerating, progress, progressMessage, images, submitGeneration, cancelGeneration } = useGenerationStore();

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    const isFast = model === "flux-schnell" || model === "hf-flux" || model === "demo";
    submitGeneration(prompt, {
      model,
      width: 1024,
      height: 1024,
      steps: isFast ? 4 : 25,
      cfg_scale: isFast ? 0.0 : 3.5,
      sampler: "DPM++ 2M Karras",
      seed: -1,
      is_public: false,
      num_images: 1,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className="glass rounded-xl p-5 space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Quick Generate</h3>
            <p className="text-[10px] text-muted-foreground">One prompt, one click</p>
          </div>
        </div>
        <Link href="/generate" className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors">
          Full editor <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {/* Progress bar */}
      <AnimatePresence>
        {isGenerating && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin text-primary" />
                <span className="text-xs text-muted-foreground">{progressMessage}</span>
              </div>
              <span className="text-xs font-mono text-primary">{progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-primary rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Model selector */}
      <div className="flex gap-1.5">
        {QUICK_MODELS.map((m) => (
          <button
            key={m.id}
            onClick={() => setModel(m.id)}
            className={`flex-1 h-8 rounded-lg text-xs font-medium transition-all duration-200 ${
              model === m.id
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/25"
                : "bg-secondary/50 text-secondary-foreground hover:bg-secondary"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Prompt input */}
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="A serene mountain landscape at golden hour, photorealistic..."
        className="w-full h-24 rounded-lg bg-background border border-border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground/40"
        disabled={isGenerating}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            handleGenerate();
          }
        }}
      />

      {/* Generate / Cancel */}
      {isGenerating ? (
        <Button onClick={cancelGeneration} variant="destructive" className="w-full" size="sm">
          <X className="mr-1.5 h-3.5 w-3.5" /> Cancel
        </Button>
      ) : (
        <Button onClick={handleGenerate} className="w-full" size="sm" disabled={!prompt.trim()}>
          <Sparkles className="mr-1.5 h-3.5 w-3.5" /> Generate
        </Button>
      )}

      <p className="text-[10px] text-muted-foreground text-center">Ctrl+Enter to generate</p>
    </motion.div>
  );
}
