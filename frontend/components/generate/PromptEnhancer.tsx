"use client";

import { useState } from "react";
import { usePromptStore } from "@/stores/promptStore";
import { SafetyBadge } from "./SafetyBadge";
import { Wand2, Zap, Ban, Loader2, CheckCircle2, Copy, ArrowRight } from "lucide-react";

interface PromptEnhancerProps {
  prompt: string;
  currentModel: string;
  onApply: (enhanced: string, negative: string) => void;
}

export function PromptEnhancer({ prompt, currentModel, onApply }: PromptEnhancerProps) {
  const { isEnhancing, isSafetyChecking, lastResult, enhance } = usePromptStore();
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const isLoading = isEnhancing || isSafetyChecking;

  const actions = [
    { id: "enhance", label: "Enhance", icon: Wand2, desc: "Improve with AI details" },
    { id: "optimize", label: "Optimize", icon: Zap, desc: "Model-specific tuning" },
    { id: "negative", label: "Negative", icon: Ban, desc: "Generate negative prompt" },
  ];

  const handleAction = async (action: string) => {
    if (!prompt.trim() || isLoading) return;
    try {
      await enhance(prompt, action, currentModel);
    } catch {}
  };

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 1500);
  };

  return (
    <div className="glass rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-1.5">
          <Wand2 className="h-3.5 w-3.5 text-primary" />
          Prompt Enhancer
        </h3>
        {!isLoading && !lastResult && (
          <span className="text-[10px] text-muted-foreground">Powered by LLM</span>
        )}
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-3 gap-1.5">
        {actions.map(({ id, label, icon: Icon, desc }) => (
          <button
            key={id}
            onClick={() => handleAction(id)}
            disabled={!prompt.trim() || isLoading}
            className="flex flex-col items-center gap-1 p-2.5 rounded-lg bg-secondary/50 hover:bg-secondary border border-transparent hover:border-border text-xs transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            ) : (
              <Icon className="h-4 w-4 text-muted-foreground" />
            )}
            <span className="font-medium">{label}</span>
            <span className="text-[9px] text-muted-foreground/60">{desc}</span>
          </button>
        ))}
      </div>

      {/* Safety status */}
      {lastResult && (
        <div className="flex items-center justify-between">
          <SafetyBadge
            isSafe={lastResult.is_safe}
            flags={lastResult.safety_flags}
            isLoading={isSafetyChecking}
          />
          {!lastResult.is_safe && lastResult.safety_flags.length > 0 && (
            <span className="text-[10px] text-amber-500">
              Review flagged content before generating
            </span>
          )}
        </div>
      )}

      {/* Results */}
      {lastResult && (
        <div className="space-y-3">
          {/* Enhanced prompt */}
          {lastResult.enhanced && lastResult.enhanced !== prompt && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-primary/80">Enhanced</label>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleCopy(lastResult.enhanced, "enhanced")}
                    className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-0.5"
                  >
                    {copiedField === "enhanced" ? (
                      <><CheckCircle2 className="h-2.5 w-2.5 text-green-500" /> Copied</>
                    ) : (
                      <><Copy className="h-2.5 w-2.5" /> Copy</>
                    )}
                  </button>
                </div>
              </div>
              <div className="p-2.5 rounded-lg bg-primary/5 border border-primary/10 text-xs leading-relaxed max-h-32 overflow-y-auto">
                {lastResult.enhanced}
              </div>
              <button
                onClick={() => onApply(lastResult.enhanced, lastResult.negative)}
                className="w-full flex items-center justify-center gap-1.5 text-xs text-primary hover:underline py-1"
              >
                <ArrowRight className="h-3 w-3" />
                Apply to prompt
              </button>
            </div>
          )}

          {/* Negative prompt */}
          {lastResult.negative && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-destructive/80">Negative Prompt</label>
                <button
                  onClick={() => handleCopy(lastResult.negative, "negative")}
                  className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-0.5"
                >
                  {copiedField === "negative" ? (
                    <><CheckCircle2 className="h-2.5 w-2.5 text-green-500" /> Copied</>
                  ) : (
                    <><Copy className="h-2.5 w-2.5" /> Copy</>
                  )}
                </button>
              </div>
              <div className="p-2.5 rounded-lg bg-destructive/5 border border-destructive/10 text-xs leading-relaxed max-h-20 overflow-y-auto">
                {lastResult.negative}
              </div>
              <button
                onClick={() => onApply(lastResult.enhanced || prompt, lastResult.negative)}
                className="w-full flex items-center justify-center gap-1.5 text-xs text-destructive/80 hover:underline py-1"
              >
                <ArrowRight className="h-3 w-3" />
                Apply negative prompt
              </button>
            </div>
          )}

          {/* Tips */}
          {lastResult.tips.length > 0 && (
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Tips applied</label>
              <div className="space-y-1">
                {lastResult.tips.map((tip, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[11px] text-muted-foreground">
                    <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0 mt-0.5" />
                    {tip}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
