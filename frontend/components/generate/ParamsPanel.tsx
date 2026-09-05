"use client";

import { useMemo } from "react";
import { RefreshCw, Dice5, Lock, Unlock, Info } from "lucide-react";

interface Params {
  width: number;
  height: number;
  steps: number;
  cfg_scale: number;
  sampler: string;
  seed: number;
  model: string;
  negative_prompt: string;
  is_public: boolean;
  num_images: number;
}

interface ParamsPanelProps {
  params: Params;
  onChange: (params: Params) => void;
}

const SAMPLERS = [
  { label: "DPM++ 2M Karras", desc: "Best quality/speed" },
  { label: "DPM++ 2M SDE Karras", desc: "Higher quality, slower" },
  { label: "DPM++ SDE Karras", desc: "High detail" },
  { label: "Euler a", desc: "Fast, artistic" },
  { label: "Euler", desc: "Fast, clean" },
  { label: "DDIM", desc: "Deterministic" },
  { label: "Heun", desc: "Accurate, slow" },
  { label: "DPM++ 3M SDE Karras", desc: "Ultra quality" },
  { label: "UniPC", desc: "Fast convergence" },
];

const MODELS = [
  { id: "hf-flux", label: "FLUX.1 Schnell (Fast)", desc: "Ultra fast 4-step generation", steps: 4, cfg: 0.0, negative: false },
  { id: "flux-dev", label: "FLUX.1 Dev (Pro Quality)", desc: "Highest detail & photorealism", steps: 25, cfg: 3.5, negative: false },
  { id: "flux-schnell", label: "FLUX.1 Schnell (Direct)", desc: "High quality 4-step generator", steps: 4, cfg: 0.0, negative: false },
  { id: "demo", label: "Demo (Free AI)", desc: "Free cloud generation", steps: 4, cfg: 0.0, negative: false },
  { id: "sdxl-1.0", label: "SDXL 1.0", desc: "Stable, high quality", steps: 30, cfg: 7.5, negative: true },
  { id: "sd-3.5-large", label: "SD 3.5 Large", desc: "Latest SD, better text", steps: 28, cfg: 7.0, negative: true },
  { id: "hf-sdxl", label: "SDXL (HF API)", desc: "Cloud, no GPU needed", steps: 30, cfg: 7.5, negative: true },
  { id: "replicate-flux", label: "FLUX.1 (Replicate)", desc: "Cloud GPU", steps: 25, cfg: 3.5, negative: true },
  { id: "gemini-imagen", label: "Gemini Imagen", desc: "Free Google AI", steps: 30, cfg: 7.5, negative: false },
];

const ASPECT_RATIOS = [
  { label: "1:1", w: 1024, h: 1024 },
  { label: "16:9", w: 1344, h: 768 },
  { label: "9:16", w: 768, h: 1344 },
  { label: "4:3", w: 1152, h: 896 },
  { label: "3:4", w: 896, h: 1152 },
  { label: "3:2", w: 1216, h: 832 },
  { label: "2:3", w: 832, h: 1216 },
];

export function ParamsPanel({ params, onChange }: ParamsPanelProps) {
  const update = (key: keyof Params, value: any) => onChange({ ...params, [key]: value });

  const currentModel = useMemo(() => MODELS.find((m) => m.id === params.model), [params.model]);
  const seedLocked = params.seed >= 0;

  const randomizeSeed = () => update("seed", -1);

  const handleModelChange = (modelId: string) => {
    const model = MODELS.find((m) => m.id === modelId);
    if (!model) return;
    onChange({
      ...params,
      model: modelId,
      steps: model.steps,
      cfg_scale: model.cfg,
    });
  };

  return (
    <div className="glass rounded-xl p-4 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Parameters</h3>
        <span className="text-xs text-muted-foreground">{currentModel?.label}</span>
      </div>

      {/* Model selector */}
      <div className="space-y-2">
        <label className="text-xs text-muted-foreground">Model</label>
        <div className="space-y-1">
          {MODELS.map((m) => (
            <button
              key={m.id}
              onClick={() => handleModelChange(m.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
                params.model === m.id
                  ? "bg-primary/15 text-primary border border-primary/30"
                  : "bg-secondary/50 text-secondary-foreground hover:bg-secondary border border-transparent"
              }`}
            >
              <span className="font-medium">{m.label}</span>
              <span className="ml-2 opacity-60">{m.desc}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Aspect Ratio */}
      <div className="space-y-2">
        <label className="text-xs text-muted-foreground">Aspect Ratio</label>
        <div className="grid grid-cols-4 gap-1">
          {ASPECT_RATIOS.map((r) => (
            <button
              key={r.label}
              onClick={() => { update("width", r.w); update("height", r.h); }}
              className={`text-xs py-1.5 rounded ${
                params.width === r.w && params.height === r.h
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground text-center">{params.width} x {params.height}</p>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <label className="text-xs text-muted-foreground">Steps</label>
          <span className="text-xs font-mono">{params.steps}</span>
        </div>
        <input
          type="range"
          min={1}
          max={currentModel?.steps ? Math.min(currentModel.steps + 20, 100) : 100}
          value={params.steps}
          onChange={(e) => update("steps", +e.target.value)}
          className="w-full accent-primary"
        />
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <span>Fast</span>
          <span>Quality</span>
        </div>
      </div>

      {/* CFG Scale */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <label className="text-xs text-muted-foreground">CFG Scale</label>
          <span className="text-xs font-mono">{params.cfg_scale}</span>
        </div>
        <input
          type="range"
          min={1}
          max={30}
          step={0.5}
          value={params.cfg_scale}
          onChange={(e) => update("cfg_scale", +e.target.value)}
          className="w-full accent-primary"
        />
        <div className="flex justify-between text-[10px] text-muted-foreground">
          <span>Creative</span>
          <span>Precise</span>
        </div>
      </div>

      {/* Sampler */}
      <div className="space-y-2">
        <label className="text-xs text-muted-foreground">Sampler / Scheduler</label>
        <select
          value={params.sampler}
          onChange={(e) => update("sampler", e.target.value)}
          className="w-full h-9 rounded-md border border-input bg-background px-2 text-sm"
        >
          {SAMPLERS.map((s) => (
            <option key={s.label} value={s.label}>{s.label} — {s.desc}</option>
          ))}
        </select>
      </div>

      {/* Seed */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <label className="text-xs text-muted-foreground">Seed</label>
          <button onClick={randomizeSeed} className="text-xs text-primary hover:underline flex items-center gap-1">
            <Dice5 className="h-3 w-3" /> Random
          </button>
        </div>
        <div className="flex gap-1">
          <input
            type="number"
            value={params.seed}
            onChange={(e) => update("seed", +e.target.value)}
            className="flex-1 h-9 rounded-md border border-input bg-background px-2 text-sm font-mono"
            placeholder="-1 = random"
          />
          <button
            onClick={() => update("seed", seedLocked ? -1 : 42)}
            className="h-9 w-9 rounded-md border border-input bg-background flex items-center justify-center"
            title={seedLocked ? "Unlock seed" : "Lock seed"}
          >
            {seedLocked ? <Lock className="h-3.5 w-3.5 text-primary" /> : <Unlock className="h-3.5 w-3.5 text-muted-foreground" />}
          </button>
        </div>
      </div>

      {/* Num Images */}
      <div className="space-y-2">
        <label className="text-xs text-muted-foreground">Images per generation</label>
        <div className="grid grid-cols-4 gap-1">
          {[1, 2, 3, 4].map((n) => (
            <button
              key={n}
              onClick={() => update("num_images", n)}
              className={`text-xs py-1.5 rounded ${
                params.num_images === n
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
        <p className="text-[10px] text-muted-foreground">
          {params.num_images} credit{params.num_images > 1 ? "s" : ""} per generation
        </p>
      </div>

      {/* Public toggle */}
      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          checked={params.is_public}
          onChange={(e) => update("is_public", e.target.checked)}
          className="accent-primary"
        />
        <span className="text-xs">Share publicly in gallery</span>
      </label>
    </div>
  );
}
