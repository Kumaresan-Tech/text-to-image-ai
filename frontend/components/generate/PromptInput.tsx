"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { PromptEnhancer } from "./PromptEnhancer";
import { PromptSuggestions } from "./PromptSuggestions";
import { PromptHistory } from "./PromptHistory";
import { Sparkles, Loader2, X, ChevronDown, ChevronUp, Wand2 } from "lucide-react";
import { useGenerationStore } from "@/stores/generationStore";

interface PromptInputProps {
  prompt: string;
  negativePrompt: string;
  currentModel: string;
  onPromptChange: (v: string) => void;
  onNegativeChange: (v: string) => void;
  onGenerate: () => void;
}

export function PromptInput({ prompt, negativePrompt, currentModel, onPromptChange, onNegativeChange, onGenerate }: PromptInputProps) {
  const [showNegative, setShowNegative] = useState(false);
  const [showEnhancer, setShowEnhancer] = useState(false);
  const { isGenerating, progress, progressMessage, cancelGeneration } = useGenerationStore();

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onGenerate();
      }
    },
    [onGenerate]
  );

  const handleApplyEnhancement = (enhanced: string, negative: string) => {
    if (enhanced) onPromptChange(enhanced);
    if (negative) {
      onNegativeChange(negative);
      setShowNegative(true);
    }
  };

  const handleSelectTemplate = (template: string) => {
    onPromptChange(template);
  };

  return (
    <div className="space-y-4">
      <div className="glass rounded-xl p-4 space-y-4">
        {/* Progress bar */}
        {isGenerating && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                <span className="text-xs text-muted-foreground">{progressMessage || "Generating..."}</span>
              </div>
              <span className="text-xs font-mono text-primary">{progress}%</span>
            </div>
            <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Positive Prompt */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Prompt</label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowEnhancer(!showEnhancer)}
                className={`text-xs flex items-center gap-1 transition-colors ${
                  showEnhancer ? "text-primary" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <Wand2 className="h-3 w-3" />
                Enhance
              </button>
              <span className={`text-xs ${prompt.length > 1800 ? "text-destructive" : "text-muted-foreground"}`}>
                {prompt.length}/2000
              </span>
            </div>
          </div>
          <textarea
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="A cyberpunk city at sunset, neon lights reflecting on wet streets, volumetric fog, 4k..."
            className="w-full h-32 rounded-lg bg-background border border-border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground/40"
            disabled={isGenerating}
          />
          <p className="text-xs text-muted-foreground">
            Ctrl+Enter to generate
          </p>
        </div>

        {/* Negative Prompt */}
        <div>
          <button
            onClick={() => setShowNegative(!showNegative)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {showNegative ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            Negative prompt {showNegative && `(${negativePrompt.length}/2000)`}
          </button>
          {showNegative && (
            <div className="mt-2">
              <textarea
                value={negativePrompt}
                onChange={(e) => onNegativeChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="blurry, low quality, watermark, text, deformed..."
                className="w-full h-20 rounded-lg bg-background border border-border px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground/40"
                disabled={isGenerating}
              />
            </div>
          )}
        </div>

        {/* Generate / Cancel */}
        {isGenerating ? (
          <Button onClick={cancelGeneration} variant="destructive" className="w-full">
            <X className="mr-2 h-4 w-4" /> Cancel Generation
          </Button>
        ) : (
          <Button onClick={onGenerate} className="w-full" disabled={!prompt.trim() || prompt.length > 2000}>
            <Sparkles className="mr-2 h-4 w-4" /> Generate
          </Button>
        )}
      </div>

      {/* Prompt Enhancer Panel */}
      {showEnhancer && (
        <PromptEnhancer
          prompt={prompt}
          currentModel={currentModel}
          onApply={handleApplyEnhancement}
        />
      )}

      {/* Suggestions & History */}
      <div className="glass rounded-xl p-4">
        <PromptSuggestions onSelect={handleSelectTemplate} modelTarget={currentModel} />
      </div>

      <div className="glass rounded-xl p-4">
        <PromptHistory
          onSelect={(enhanced, negative) => {
            onPromptChange(enhanced);
            if (negative) {
              onNegativeChange(negative);
              setShowNegative(true);
            }
          }}
        />
      </div>
    </div>
  );
}
