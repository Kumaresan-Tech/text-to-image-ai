"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wand2, Loader2, Copy, Check, Shield, ShieldAlert } from "lucide-react";
import { usePromptStore } from "@/stores/promptStore";

export function QuickEnhance() {
  const [prompt, setPrompt] = useState("");
  const [copied, setCopied] = useState(false);
  const { isEnhancing, lastResult, enhance } = usePromptStore();

  const handleEnhance = (action: string) => {
    if (!prompt.trim()) return;
    enhance(prompt, action, "sdxl-1.0");
  };

  function copyResult(text: string) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className="glass rounded-xl p-5 space-y-4"
    >
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
          <Wand2 className="h-4 w-4 text-purple-500" />
        </div>
        <div>
          <h3 className="text-sm font-semibold">Quick Enhance</h3>
          <p className="text-[10px] text-muted-foreground">Improve prompts with AI</p>
        </div>
      </div>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter a basic prompt to enhance..."
        className="w-full h-20 rounded-lg bg-background border border-border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground/40"
        disabled={isEnhancing}
      />

      <div className="flex gap-1.5">
        {[
          { action: "enhance", label: "Enhance", color: "bg-primary" },
          { action: "optimize", label: "Optimize", color: "bg-blue-500" },
          { action: "negative", label: "Negative", color: "bg-destructive" },
        ].map((btn) => (
          <button
            key={btn.action}
            onClick={() => handleEnhance(btn.action)}
            disabled={!prompt.trim() || isEnhancing}
            className={`flex-1 h-8 rounded-lg text-xs font-medium text-white transition-all disabled:opacity-50 ${btn.color}`}
          >
            {isEnhancing ? (
              <Loader2 className="h-3 w-3 animate-spin mx-auto" />
            ) : (
              btn.label
            )}
          </button>
        ))}
      </div>

      {/* Result */}
      <AnimatePresence>
        {lastResult && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="bg-secondary/30 rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Enhanced</span>
                <div className="flex items-center gap-1.5">
                  {lastResult.is_safe ? (
                    <span className="flex items-center gap-0.5 text-[10px] text-green-500">
                      <Shield className="h-2.5 w-2.5" /> Safe
                    </span>
                  ) : (
                    <span className="flex items-center gap-0.5 text-[10px] text-yellow-500">
                      <ShieldAlert className="h-2.5 w-2.5" /> Flagged
                    </span>
                  )}
                  <button
                    onClick={() => copyResult(lastResult.enhanced)}
                    className="h-5 w-5 rounded flex items-center justify-center hover:bg-background transition-colors"
                  >
                    {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3 text-muted-foreground" />}
                  </button>
                </div>
              </div>
              <p className="text-xs leading-relaxed">{lastResult.enhanced}</p>
            </div>

            {lastResult.negative && (
              <div className="bg-destructive/5 rounded-lg p-3 space-y-1">
                <span className="text-[10px] text-destructive/80 uppercase tracking-wider">Negative</span>
                <p className="text-xs text-muted-foreground leading-relaxed">{lastResult.negative}</p>
              </div>
            )}

            {lastResult.tips && lastResult.tips.length > 0 && (
              <div className="space-y-1">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Tips</span>
                <ul className="space-y-0.5">
                  {lastResult.tips.map((tip, i) => (
                    <li key={i} className="text-[10px] text-muted-foreground">• {tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
