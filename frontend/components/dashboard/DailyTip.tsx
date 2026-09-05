"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Lightbulb, ChevronRight, ChevronLeft } from "lucide-react";

const tips = [
  {
    title: "Prompt Structure",
    text: "Start with the subject, then add style, lighting, and quality tags. E.g., 'A cat, oil painting, golden hour lighting, 4k'",
  },
  {
    title: "Negative Prompts",
    text: "Use negative prompts to remove unwanted elements: 'blurry, watermark, low quality, text'",
  },
  {
    title: "CFG Scale",
    text: "Lower CFG (3-7) gives more creative results. Higher CFG (7-15) follows the prompt more strictly.",
  },
  {
    title: "Steps",
    text: "Most models reach good quality at 20-30 steps. Flux Schnell only needs 4 steps for great results.",
  },
  {
    title: "Seed Locking",
    text: "Use a fixed seed to make small prompt changes while keeping the composition consistent.",
  },
  {
    title: "Aspect Ratios",
    text: "16:9 works great for landscapes, 9:16 for portraits. Not all models support non-square ratios.",
  },
];

export function DailyTip() {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrent((prev) => (prev + 1) % tips.length);
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const tip = tips[current];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.5 }}
      className="glass rounded-xl p-5 space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-yellow-500/10 flex items-center justify-center">
            <Lightbulb className="h-3.5 w-3.5 text-yellow-500" />
          </div>
          <span className="text-xs font-semibold">Tip of the Day</span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setCurrent((prev) => (prev - 1 + tips.length) % tips.length)}
            className="h-6 w-6 rounded-md bg-secondary/50 hover:bg-secondary flex items-center justify-center transition-colors"
          >
            <ChevronLeft className="h-3 w-3 text-muted-foreground" />
          </button>
          <button
            onClick={() => setCurrent((prev) => (prev + 1) % tips.length)}
            className="h-6 w-6 rounded-md bg-secondary/50 hover:bg-secondary flex items-center justify-center transition-colors"
          >
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
          </button>
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={current}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -10 }}
          transition={{ duration: 0.2 }}
          className="space-y-1"
        >
          <p className="text-xs font-medium text-primary">{tip.title}</p>
          <p className="text-xs text-muted-foreground leading-relaxed">{tip.text}</p>
        </motion.div>
      </AnimatePresence>

      <div className="flex gap-1 justify-center">
        {tips.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrent(i)}
            className={`h-1 rounded-full transition-all duration-300 ${
              i === current ? "w-4 bg-primary" : "w-1 bg-muted-foreground/30"
            }`}
          />
        ))}
      </div>
    </motion.div>
  );
}
