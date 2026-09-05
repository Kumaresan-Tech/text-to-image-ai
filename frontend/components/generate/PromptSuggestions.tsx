"use client";

import { useState, useEffect } from "react";
import { usePromptStore } from "@/stores/promptStore";
import { Lightbulb, RefreshCw, Sparkles, ChevronDown, ChevronUp } from "lucide-react";

interface PromptSuggestionsProps {
  onSelect: (prompt: string) => void;
  modelTarget: string;
}

export function PromptSuggestions({ onSelect, modelTarget }: PromptSuggestionsProps) {
  const { suggestions, isEnhancing, enhance } = usePromptStore();
  const [isOpen, setIsOpen] = useState(false);
  const [templates, setTemplates] = useState<any>(null);

  useEffect(() => {
    fetch("/api/prompts/templates")
      .then((r) => r.json())
      .then(setTemplates)
      .catch(() => {});
  }, []);

  const handleGenerateSuggestions = async () => {
    setIsOpen(true);
    try {
      await enhance("Generate 5 creative prompt ideas", "suggest", modelTarget);
    } catch {}
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          <Lightbulb className="h-3 w-3" />
          Prompt ideas & templates
        </button>
        <button
          onClick={handleGenerateSuggestions}
          disabled={isEnhancing}
          className="text-xs text-primary hover:underline flex items-center gap-1"
        >
          <Sparkles className="h-3 w-3" />
          {isEnhancing ? "Generating..." : "AI Ideas"}
        </button>
      </div>

      {isOpen && (
        <div className="space-y-4">
          {/* AI Suggestions */}
          {suggestions.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-primary">AI-Generated Ideas</p>
              <div className="space-y-1.5">
                {suggestions.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => onSelect(s)}
                    className="w-full text-left p-2.5 rounded-lg bg-primary/5 border border-primary/10 text-xs leading-relaxed hover:bg-primary/10 hover:border-primary/20 transition-colors text-left"
                  >
                    <span className="text-primary/60 mr-1.5">{i + 1}.</span>
                    {s.length > 120 ? s.slice(0, 120) + "..." : s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Template Categories */}
          {templates?.categories && (
            <div className="space-y-3">
              {templates.categories.map((cat: any) => (
                <div key={cat.name} className="space-y-1.5">
                  <p className="text-xs font-medium text-muted-foreground">{cat.name}</p>
                  <div className="flex flex-wrap gap-1">
                    {cat.prompts.map((p: string, i: number) => (
                      <button
                        key={i}
                        onClick={() => onSelect(p)}
                        className="text-[11px] px-2 py-1 rounded-md bg-secondary/50 text-secondary-foreground hover:bg-secondary transition-colors"
                      >
                        {p.length > 40 ? p.slice(0, 40) + "..." : p}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
