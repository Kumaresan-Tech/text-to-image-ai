"use client";

import { create } from "zustand";
import { promptApi } from "@/lib/api";

interface PromptHistoryItem {
  id: string;
  original_prompt: string;
  enhanced_prompt: string | null;
  negative_prompt: string | null;
  action: string;
  model_target: string | null;
  is_safe: boolean;
  used: boolean;
  created_at: string | null;
}

interface PromptState {
  history: PromptHistoryItem[];
  suggestions: string[];
  isEnhancing: boolean;
  isSafetyChecking: boolean;
  lastResult: {
    enhanced: string;
    negative: string;
    tips: string[];
    is_safe: boolean;
    safety_flags: string[];
  } | null;

  enhance: (prompt: string, action: string, modelTarget: string) => Promise<void>;
  safetyCheck: (prompt: string) => Promise<{ is_safe: boolean; flags: string[] }>;
  loadHistory: (action?: string) => Promise<void>;
  applyEnhanced: (enhanced: string, negative: string) => { enhanced: string; negative: string };
}

export const usePromptStore = create<PromptState>((set, get) => ({
  history: [],
  suggestions: [],
  isEnhancing: false,
  isSafetyChecking: false,
  lastResult: null,

  enhance: async (prompt: string, action: string, modelTarget: string) => {
    const runStudioEnhance = async () => {
      try {
        const res = await fetch("/api/studio/enhance", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt, style: "cinematic" }),
        });
        const data = await res.json();
        const enhanced = data.enhanced_prompt || prompt;
        set({
          isEnhancing: false,
          lastResult: {
            enhanced,
            negative: "low quality, blurry, distorted, bad anatomy, artifacts",
            tips: ["Enhanced by Gemini Flash AI", "Cinematic composition & lighting applied"],
            is_safe: true,
            safety_flags: [],
          },
        });
      } catch {
        set({ isEnhancing: false });
      }
    };

    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token || token.startsWith("aura_local_token_")) {
      await runStudioEnhance();
      return;
    }

    set({ isEnhancing: true, lastResult: null });
    try {
      const result = await promptApi.enhance(
        { prompt, action, model_target: modelTarget },
        token
      );

      const updates: Partial<PromptState> = {
        isEnhancing: false,
        lastResult: {
          enhanced: result.enhanced,
          negative: result.negative,
          tips: result.tips,
          is_safe: result.is_safe,
          safety_flags: result.safety_flags,
        },
      };

      if (result.suggestions) {
        updates.suggestions = result.suggestions;
      }

      set(updates);
      get().loadHistory(action);
    } catch (err: any) {
      console.warn("Backend enhance unavailable, falling back to Gemini Studio:", err);
      await runStudioEnhance();
    }
  },

  safetyCheck: async (prompt: string) => {
    const token = localStorage.getItem("token");
    if (!token) return { is_safe: true, flags: [] };

    set({ isSafetyChecking: true });
    try {
      const result = await promptApi.enhance(
        { prompt, action: "safety_check" },
        token
      );
      set({ isSafetyChecking: false });
      return { is_safe: result.is_safe, flags: result.safety_flags };
    } catch {
      set({ isSafetyChecking: false });
      return { is_safe: true, flags: [] };
    }
  },

  loadHistory: async (action?: string) => {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
      const data = await promptApi.history(action, 20, token);
      set({ history: data.items });
    } catch {}
  },

  applyEnhanced: (enhanced: string, negative: string) => {
    return { enhanced, negative };
  },
}));
