"use client";

import { create } from "zustand";
import { generateApi, imagesApi } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

interface GeneratedImage {
  id: string;
  user_id: string;
  prompt: string;
  negative_prompt?: string;
  image_url: string;
  thumbnail_url?: string;
  width: number;
  height: number;
  steps: number;
  cfg_scale: number;
  sampler: string;
  seed?: number;
  model: string;
  is_public: boolean;
  likes_count: number;
  created_at: string;
}

interface GenerationJob {
  jobId: string;
  status: string;
  progress: number;
  message: string;
  imageIds: string[];
}

interface GenerationState {
  images: GeneratedImage[];
  activeJob: GenerationJob | null;
  isGenerating: boolean;
  progress: number;
  progressMessage: string;
  error: string | null;
  generationHistory: GenerationJob[];

  submitGeneration: (prompt: string, params: any) => Promise<void>;
  cancelGeneration: () => Promise<void>;
  resetError: () => void;
  reset: () => void;
  _pollFallback: (jobId: string, token: string) => Promise<void>;
}

export const useGenerationStore = create<GenerationState>((set, get) => ({
  images: [],
  activeJob: null,
  isGenerating: false,
  progress: 0,
  progressMessage: "",
  error: null,
  generationHistory: [],

  submitGeneration: async (prompt: string, params: any) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

    // Direct Studio Engine runner (combines frontend with studio board backend)
    const runStudioGeneration = async () => {
      set({ isGenerating: true, progress: 25, progressMessage: "Connecting to FLUX.1 Engine...", error: null });

      let studioModel = "flux-schnell";
      if (params.model?.includes("dev")) studioModel = "flux-dev";
      else if (params.model?.includes("demo")) studioModel = "demo";

      const progressTimer = setTimeout(() => {
        set({ progress: 65, progressMessage: "Rendering image with high-definition textures..." });
      }, 2000);

      try {
        const res = await fetch("/api/studio/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt,
            style: params.style || "cinematic",
            model: studioModel,
            width: params.width || 1024,
            height: params.height || 1024,
          }),
        });
        clearTimeout(progressTimer);
        const data = await res.json();
        if (data.success && data.image_url) {
          const newImg: GeneratedImage = {
            id: data.filename || `aura_${Date.now()}`,
            user_id: "",
            prompt: data.final_prompt || prompt,
            image_url: data.image_url,
            thumbnail_url: data.image_url,
            width: data.width || params.width || 1024,
            height: data.height || params.height || 1024,
            steps: params.steps || (studioModel === "flux-dev" ? 25 : 4),
            cfg_scale: params.cfg_scale || (studioModel === "flux-dev" ? 3.5 : 0.0),
            sampler: params.sampler || "DPM++ 2M Karras",
            seed: -1,
            model: data.model || studioModel,
            is_public: true,
            likes_count: 0,
            created_at: new Date().toISOString(),
          };

          const currentCredits = useAuthStore.getState().user?.credits ?? 100;
          if (currentCredits > 0) {
            useAuthStore.getState().updateCredits(currentCredits - 1);
          }

          set((state) => ({
            images: [newImg, ...state.images],
            isGenerating: false,
            progress: 100,
            progressMessage: "Complete!",
            activeJob: null,
          }));
          return;
        } else {
          throw new Error(data.error || "Studio generation returned no image");
        }
      } catch (studioErr: any) {
        clearTimeout(progressTimer);
        set({
          isGenerating: false,
          progress: 0,
          error: studioErr.message || "Generation failed",
          activeJob: null,
        });
      }
    };

    const isLocalSession = !token || token.startsWith("aura_local_token_");
    if (isLocalSession) {
      await runStudioGeneration();
      return;
    }

    set({ isGenerating: true, progress: 0, progressMessage: "Submitting...", error: null });

    try {
      const result = await generateApi.submit({ prompt, ...params }, token);
      const jobId = result.job_id;

      set({
        activeJob: { jobId, status: "PENDING", progress: 0, message: "Job submitted", imageIds: [] },
        progress: 2,
        progressMessage: "Job submitted, connecting to stream...",
      });

      const eventSource = new EventSource(
        `${process.env.NEXT_PUBLIC_API_URL}/api/generate/${jobId}/stream?token=${token}`
      );

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const updates: Partial<GenerationState> = {
            progress: data.progress || 0,
            progressMessage: data.message || "",
          };

          if (data.image_id && data.image_url) {
            updates.images = [
              {
                id: data.image_id,
                image_url: data.image_url,
                prompt,
                width: params.width,
                height: params.height,
                steps: params.steps,
                cfg_scale: params.cfg_scale,
                sampler: params.sampler,
                seed: params.seed,
                model: params.model,
                user_id: "",
                is_public: params.is_public,
                likes_count: 0,
                created_at: new Date().toISOString(),
              },
              ...get().images,
            ];
          }

          if (data.status === "COMPLETED") {
            eventSource.close();
            updates.isGenerating = false;
            updates.progress = 100;
            updates.progressMessage = "Complete!";
            updates.activeJob = null;
          }

          if (data.status === "FAILED" || data.status === "CANCELLED") {
            eventSource.close();
            updates.isGenerating = false;
            updates.error = data.message || "Generation failed";
            updates.activeJob = null;
          }

          set(updates);
        } catch (e) {
          console.error("SSE parse error:", e);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        const current = get();
        if (current.isGenerating) {
          set({ progressMessage: "Connection lost, polling..." });
          get()._pollFallback(jobId, token);
        }
      };
    } catch (err: any) {
      console.warn("Backend submission failed, falling back to Studio Engine:", err);
      await runStudioGeneration();
    }
  },

  _pollFallback: async (jobId: string, token: string) => {
    let attempts = 0;
    const maxAttempts = 120;

    const poll = async () => {
      if (attempts >= maxAttempts || !get().isGenerating) return;

      try {
        const job = await generateApi.getStatus(jobId, token);
        set({ progress: Math.min(95, 10 + (attempts / maxAttempts) * 85) });

        if (job.status === "COMPLETED" && job.image_url) {
          set((state) => ({
            images: [
              {
                id: job.image_id,
                image_url: job.image_url,
                prompt: job.prompt,
                width: job.params?.width || 1024,
                height: job.params?.height || 1024,
                steps: job.params?.steps || 30,
                cfg_scale: job.params?.cfg_scale || 7.5,
                sampler: job.params?.sampler || "DPM++ 2M Karras",
                seed: job.params?.seed,
                model: job.params?.model || "demo",
                user_id: "",
                is_public: job.params?.is_public || false,
                likes_count: 0,
                created_at: new Date().toISOString(),
              },
              ...state.images,
            ],
            isGenerating: false,
            progress: 100,
            progressMessage: "Complete!",
            activeJob: null,
          }));
          return;
        }

        if (job.status === "FAILED") {
          set({ isGenerating: false, error: job.error_message || "Generation failed", activeJob: null });
          return;
        }

        attempts++;
        setTimeout(poll, 2000);
      } catch {
        attempts++;
        setTimeout(poll, 3000);
      }
    };

    poll();
  },

  cancelGeneration: async () => {
    const { activeJob } = get();
    if (!activeJob) return;

    const token = localStorage.getItem("token");
    if (token) {
      try {
        await generateApi.cancel(activeJob.jobId, token);
      } catch {}
    }

    set({ isGenerating: false, activeJob: null, progress: 0, progressMessage: "Cancelled" });
  },

  resetError: () => set({ error: null }),

  reset: () =>
    set({
      images: [],
      activeJob: null,
      isGenerating: false,
      progress: 0,
      progressMessage: "",
      error: null,
    }),
}));
