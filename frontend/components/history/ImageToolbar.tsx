"use client";

import { useState } from "react";
import { Search, SlidersHorizontal, X, Calendar, ArrowUpDown } from "lucide-react";

export interface ImageFilters {
  q: string;
  model: string;
  sampler: string;
  dateFrom: string;
  dateTo: string;
  isFavorited: boolean | null;
  sortBy: string;
  sortOrder: string;
}

interface ImageToolbarProps {
  filters: ImageFilters;
  onFiltersChange: (filters: ImageFilters) => void;
  total: number;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

const MODELS = [
  { value: "", label: "All Models" },
  { value: "demo", label: "Demo (Free)" },
  { value: "sdxl-1.0", label: "SDXL 1.0" },
  { value: "sd-3.5-large", label: "SD 3.5 Large" },
  { value: "flux-dev", label: "Flux Dev" },
  { value: "flux-schnell", label: "Flux Schnell" },
  { value: "hf-sdxl", label: "HF SDXL" },
  { value: "replicate-flux", label: "Replicate Flux" },
  { value: "gemini-imagen", label: "Gemini Imagen" },
];

const SORT_OPTIONS = [
  { value: "created_at", label: "Date" },
  { value: "likes_count", label: "Likes" },
  { value: "model", label: "Model" },
  { value: "prompt", label: "Prompt" },
];

export function ImageToolbar({ filters, onFiltersChange, total, activeTab, onTabChange }: ImageToolbarProps) {
  const [showFilters, setShowFilters] = useState(false);

  function update(patch: Partial<ImageFilters>) {
    onFiltersChange({ ...filters, ...patch });
  }

  const hasActiveFilters = filters.model || filters.dateFrom || filters.dateTo || filters.isFavorited === true;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {onTabChange && (
          <div className="flex bg-secondary/30 rounded-lg p-0.5 mr-2">
            {["all", "favorites"].map((tab) => (
              <button
                key={tab}
                onClick={() => onTabChange(tab)}
                className={`h-8 px-3 rounded-md text-xs font-medium transition-colors capitalize ${
                  activeTab === tab
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        )}

        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={filters.q}
            onChange={(e) => update({ q: e.target.value })}
            placeholder="Search prompts, models..."
            className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {filters.q && (
            <button
              onClick={() => update({ q: "" })}
              className="absolute right-2 top-1/2 -translate-y-1/2 h-5 w-5 rounded-md hover:bg-muted flex items-center justify-center"
            >
              <X className="h-3 w-3 text-muted-foreground" />
            </button>
          )}
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`h-9 w-9 rounded-lg border flex items-center justify-center transition-colors ${
            showFilters || hasActiveFilters
              ? "border-primary bg-primary/5 text-primary"
              : "border-input bg-background text-muted-foreground hover:bg-accent"
          }`}
        >
          <SlidersHorizontal className="h-4 w-4" />
        </button>

        <span className="text-xs text-muted-foreground whitespace-nowrap">{total} images</span>
      </div>

      {showFilters && (
        <div className="flex flex-wrap items-center gap-2 p-3 rounded-lg bg-secondary/20 border border-border/50">
          <select
            value={filters.model}
            onChange={(e) => update({ model: e.target.value })}
            className="h-8 rounded-md border border-input bg-background px-2 text-xs"
          >
            {MODELS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>

          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3 text-muted-foreground" />
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => update({ dateFrom: e.target.value })}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs"
            />
            <span className="text-[10px] text-muted-foreground">to</span>
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => update({ dateTo: e.target.value })}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs"
            />
          </div>

          <div className="flex items-center gap-1">
            <ArrowUpDown className="h-3 w-3 text-muted-foreground" />
            <select
              value={filters.sortBy}
              onChange={(e) => update({ sortBy: e.target.value })}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs"
            >
              {SORT_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
            <button
              onClick={() => update({ sortOrder: filters.sortOrder === "desc" ? "asc" : "desc" })}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs hover:bg-accent"
            >
              {filters.sortOrder === "desc" ? "↓" : "↑"}
            </button>
          </div>

          {(filters.model || filters.dateFrom || filters.dateTo) && (
            <button
              onClick={() => update({ model: "", dateFrom: "", dateTo: "" })}
              className="h-8 px-2 rounded-md bg-destructive/10 text-destructive text-xs hover:bg-destructive/20 transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}
