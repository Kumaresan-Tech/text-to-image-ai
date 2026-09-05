"use client";

import { useState, useEffect } from "react";
import { usePromptStore } from "@/stores/promptStore";
import { History, Clock, Copy, ArrowRight, CheckCircle2, ShieldCheck, ShieldAlert } from "lucide-react";

interface PromptHistoryProps {
  onSelect: (prompt: string, negative?: string) => void;
}

export function PromptHistory({ onSelect }: PromptHistoryProps) {
  const { history, loadHistory } = usePromptStore();
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadHistory(filter || undefined);
    }
  }, [isOpen, filter]);

  const filtered = filter ? history.filter((h) => h.action === filter) : history;

  const actionLabels: Record<string, string> = {
    enhance: "Enhanced",
    optimize: "Optimized",
    negative: "Negative",
    suggest: "Suggested",
    safety_check: "Safety Check",
  };

  return (
    <div className="space-y-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        <History className="h-3 w-3" />
        {isOpen ? "Hide" : "Show"} prompt history
        {history.length > 0 && (
          <span className="text-[10px] bg-secondary rounded-full px-1.5">{history.length}</span>
        )}
      </button>

      {isOpen && (
        <div className="space-y-3">
          {/* Filter */}
          <div className="flex gap-1 flex-wrap">
            <button
              onClick={() => setFilter(null)}
              className={`text-[10px] px-2 py-0.5 rounded-full ${
                !filter ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
              }`}
            >
              All
            </button>
            {Object.entries(actionLabels).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`text-[10px] px-2 py-0.5 rounded-full ${
                  filter === key ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* List */}
          {filtered.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">No history yet</p>
          ) : (
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {filtered.map((item) => (
                <div
                  key={item.id}
                  className="p-2.5 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors group"
                >
                  <div className="flex items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs leading-relaxed line-clamp-2">{item.original_prompt}</p>
                      {item.enhanced_prompt && item.enhanced_prompt !== item.original_prompt && (
                        <div className="mt-1.5 flex items-center gap-1 text-[10px] text-primary/70">
                          <ArrowRight className="h-2.5 w-2.5" />
                          <span className="line-clamp-1">{item.enhanced_prompt}</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      {item.is_safe ? (
                        <ShieldCheck className="h-3 w-3 text-green-500/60" />
                      ) : (
                        <ShieldAlert className="h-3 w-3 text-amber-500/60" />
                      )}
                      <button
                        onClick={() => onSelect(item.enhanced_prompt || item.original_prompt, item.negative_prompt || undefined)}
                        className="opacity-0 group-hover:opacity-100 text-[10px] text-primary hover:underline transition-opacity"
                      >
                        Use
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-1.5 text-[10px] text-muted-foreground/60">
                    <span className="bg-secondary rounded px-1">{actionLabels[item.action] || item.action}</span>
                    {item.model_target && <span>{item.model_target}</span>}
                    {item.created_at && (
                      <span className="flex items-center gap-0.5">
                        <Clock className="h-2 w-2" />
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    )}
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
