"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Wand2,
  Download,
  Maximize2,
  Copy,
  Check,
  RefreshCw,
  Dice5,
  Image as ImageIcon,
  Zap,
  Sliders,
  Clock,
  CheckCircle2,
  AlertCircle,
  X,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface StylePreset {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const STYLE_PRESETS: StylePreset[] = [
  { id: "cinematic", name: "Cinematic", icon: "🎬", description: "35mm, volumetric rim light, 8k" },
  { id: "photorealistic", name: "Photorealism", icon: "📸", description: "Raw photo, 85mm lens, f/1.4" },
  { id: "cyberpunk", name: "Cyberpunk", icon: "⚡", description: "Neon caustics, wet reflections" },
  { id: "fantasy", name: "Fantasy Art", icon: "✨", description: "Volumetric glow, bioluminescence" },
  { id: "anime", name: "Anime / Manga", icon: "🌸", description: "Makoto Shinkai style, vibrant" },
  { id: "3d_render", name: "3D Octane", icon: "🧊", description: "Isometric render, ray tracing" },
];

const ASPECT_RATIOS = [
  { id: "1:1", label: "1:1", name: "Square", width: 1024, height: 1024 },
  { id: "16:9", label: "16:9", name: "Landscape", width: 1344, height: 768 },
  { id: "9:16", label: "9:16", name: "Portrait", width: 768, height: 1344 },
  { id: "4:3", label: "4:3", name: "Classic", width: 1152, height: 896 },
  { id: "3:2", label: "3:2", name: "Photo", width: 1216, height: 832 },
];

const SURPRISE_PROMPTS = [
  "A majestic cybernetic snow leopard with glowing sapphire circuits perched on a neon-lit Tokyo skyscraper at night",
  "Close-up cinematic macro photography of a mystical enchanted mushroom with glowing bioluminescent spores in a twilight mossy forest",
  "A high-end futuristic concept supercar speeding along a coastal highway at golden hour, motion blur, hyperrealistic reflection",
  "An ethereal celestial deity weaving galaxies with stardust and golden nebula threads, cosmic fantasy masterpiece",
  "An ancient Japanese temple immersed in floating pink sakura petals, foggy mountain morning light, serene water reflections",
  "A retro 80s synthwave anime pilot inside a detailed glowing mech cockpit looking down at a cyberpunk metropolis",
];

interface GeneratedStudioImage {
  id: string;
  url: string;
  prompt: string;
  style: string;
  model: string;
  width: number;
  height: number;
  elapsedSeconds?: number;
  seed?: number;
  createdAt: string;
}

export default function NativeStudioPage() {
  const [prompt, setPrompt] = useState("");
  const [selectedStyle, setSelectedStyle] = useState("cinematic");
  const [selectedRatio, setSelectedRatio] = useState("1:1");
  const [selectedModel, setSelectedModel] = useState("flux-schnell");
  const [seed, setSeed] = useState(-1);

  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressStep, setProgressStep] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [enhancedDiff, setEnhancedDiff] = useState<string | null>(null);

  const [currentImage, setCurrentImage] = useState<GeneratedStudioImage | null>(null);
  const [history, setHistory] = useState<GeneratedStudioImage[]>([]);
  const [copied, setCopied] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeRatio = ASPECT_RATIOS.find((r) => r.id === selectedRatio) || ASPECT_RATIOS[0];

  // Load past history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch("/api/studio/history");
      const data = await res.json();
      if (data.images && data.images.length > 0) {
        const mapped: GeneratedStudioImage[] = data.images.map((img: any) => ({
          id: img.filename,
          url: img.url,
          prompt: img.filename.replace(/^aura_\d+_\d+\.png$/, "Studio Artwork").replace(/\.png$/, ""),
          style: "cinematic",
          model: "FLUX.1 Schnell",
          width: 1024,
          height: 1024,
          createdAt: img.created_at,
        }));
        setHistory(mapped);
        if (!currentImage && mapped.length > 0) {
          setCurrentImage(mapped[0]);
        }
      }
    } catch {
      // Ignore if no past history
    }
  };

  const handleRandomPrompt = () => {
    const random = SURPRISE_PROMPTS[Math.floor(Math.random() * SURPRISE_PROMPTS.length)];
    setPrompt(random);
    setEnhancedDiff(null);
  };

  const handleEnhance = async () => {
    if (!prompt.trim()) return;
    setIsEnhancing(true);
    setError(null);

    try {
      const res = await fetch("/api/studio/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, style: selectedStyle }),
      });
      const data = await res.json();
      if (data.enhanced_prompt) {
        setEnhancedDiff(data.enhanced_prompt);
        setPrompt(data.enhanced_prompt);
      }
    } catch (err: any) {
      setError("Failed to enhance prompt: " + err.message);
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim() || isGenerating) return;
    setIsGenerating(true);
    setError(null);
    setProgressStep(1);
    setProgressMessage("Analyzing prompt & loading neural weights...");

    const step2Timer = setTimeout(() => {
      setProgressStep(2);
      setProgressMessage("Generating high-resolution FLUX latents...");
    }, 1200);

    const step3Timer = setTimeout(() => {
      setProgressStep(3);
      setProgressMessage("Rendering fine textures, lighting & volumetric depth...");
    }, 3200);

    try {
      const res = await fetch("/api/studio/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          style: selectedStyle,
          model: selectedModel,
          width: activeRatio.width,
          height: activeRatio.height,
          seed: seed > 0 ? seed : undefined,
        }),
      });

      clearTimeout(step2Timer);
      clearTimeout(step3Timer);

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || "Generation failed");
      }

      const newImage: GeneratedStudioImage = {
        id: data.filename || `aura_${Date.now()}`,
        url: data.image_url,
        prompt: data.final_prompt || prompt,
        style: selectedStyle,
        model: data.model || "FLUX.1 Schnell",
        width: data.width,
        height: data.height,
        elapsedSeconds: data.elapsed_seconds,
        seed: data.seed,
        createdAt: "Just now",
      };

      setCurrentImage(newImage);
      setHistory((prev) => [newImage, ...prev]);
    } catch (err: any) {
      setError(err.message || "Failed to generate image");
    } finally {
      clearTimeout(step2Timer);
      clearTimeout(step3Timer);
      setIsGenerating(false);
      setProgressStep(0);
    }
  };

  const handleCopyPrompt = () => {
    if (!currentImage) return;
    navigator.clipboard.writeText(currentImage.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!currentImage) return;
    const a = document.createElement("a");
    a.href = currentImage.url;
    a.download = currentImage.id.endsWith(".png") ? currentImage.id : `${currentImage.id}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-[#070A11] text-slate-100 flex flex-col antialiased">
      {/* Top Banner */}
      <div className="border-b border-white/10 bg-[#0C101D]/90 backdrop-blur px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-purple-600 to-cyan-500 p-0.5 flex items-center justify-center shadow-lg shadow-purple-500/25">
            <div className="h-full w-full bg-[#0C101D] rounded-[10px] flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-white">AuraCraft AI Studio</h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                Unified Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">FLUX.1 Schnell & Dev • Gemini 3.6 Flash Intelligence</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchHistory}
            className="border-white/10 hover:bg-white/5 text-slate-300 gap-1.5 text-xs h-8"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sync History</span>
          </Button>

          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-xs font-semibold">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Active
          </div>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 grid lg:grid-cols-[460px_1fr] gap-6 items-start">
        {/* LEFT PANEL: Controls & Inputs */}
        <div className="space-y-5">
          {/* Prompt Card */}
          <div className="rounded-2xl bg-[#0F1424]/80 border border-white/10 p-5 shadow-xl backdrop-blur-xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Wand2 className="h-3.5 w-3.5 text-purple-400" /> Image Prompt
              </label>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={handleRandomPrompt}
                  className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1 px-2 py-1 rounded-md hover:bg-white/5 transition"
                  title="Insert a creative surprise prompt"
                >
                  <Dice5 className="h-3.5 w-3.5" /> Surprise Me
                </button>

                {prompt && (
                  <button
                    type="button"
                    onClick={() => {
                      setPrompt("");
                      setEnhancedDiff(null);
                    }}
                    className="text-xs text-slate-500 hover:text-red-400 p-1 rounded transition"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>

            <div className="relative">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                    e.preventDefault();
                    handleGenerate();
                  }
                }}
                rows={4}
                placeholder="Describe your imagination in detail... (e.g., A cybernetic samurai standing in a rainy neo-Tokyo street with neon reflections, 8k masterpiece)"
                className="w-full bg-[#080B15]/90 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-purple-500/60 focus:ring-1 focus:ring-purple-500/30 transition resize-none leading-relaxed"
              />
            </div>

            {/* Gemini Magic Enhance Button */}
            <div className="mt-3 flex items-center justify-between">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleEnhance}
                disabled={isEnhancing || !prompt.trim()}
                className="relative overflow-hidden text-xs font-semibold gap-1.5 bg-gradient-to-r from-purple-500/15 via-cyan-500/15 to-purple-500/15 border-purple-500/30 hover:border-purple-500/60 text-purple-300 hover:text-white transition shadow-sm h-8"
              >
                {isEnhancing ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                    <span>Gemini is Enhancing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
                    <span>✨ Gemini Magic Enhance</span>
                  </>
                )}
              </Button>

              <span className="text-[11px] text-slate-500">Ctrl + Enter to run</span>
            </div>

            {enhancedDiff && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-3 p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-xs text-purple-200 flex items-start gap-2"
              >
                <CheckCircle2 className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                <span className="leading-snug">
                  Enhanced with cinematic lighting, camera specs & micro-textures!
                </span>
              </motion.div>
            )}
          </div>

          {/* Style Presets */}
          <div className="rounded-2xl bg-[#0F1424]/80 border border-white/10 p-5 shadow-xl backdrop-blur-xl">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-3">
              Artistic Style Preset
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {STYLE_PRESETS.map((preset) => {
                const isActive = selectedStyle === preset.id;
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => setSelectedStyle(preset.id)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isActive
                        ? "bg-purple-600/20 border-purple-500 text-white shadow-lg shadow-purple-500/20"
                        : "bg-[#080B15]/60 border-white/5 text-slate-400 hover:border-white/20 hover:text-slate-200"
                    }`}
                  >
                    <div className="text-xl mb-1">{preset.icon}</div>
                    <div className="text-xs font-semibold">{preset.name}</div>
                    <div className="text-[10px] text-slate-500 line-clamp-1 mt-0.5">{preset.description}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dimensions & Model */}
          <div className="rounded-2xl bg-[#0F1424]/80 border border-white/10 p-5 shadow-xl backdrop-blur-xl space-y-4">
            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2.5">
                Aspect Ratio
              </label>
              <div className="grid grid-cols-5 gap-1.5">
                {ASPECT_RATIOS.map((ratio) => {
                  const isActive = selectedRatio === ratio.id;
                  return (
                    <button
                      key={ratio.id}
                      type="button"
                      onClick={() => setSelectedRatio(ratio.id)}
                      className={`py-2 px-1.5 rounded-lg border text-center transition ${
                        isActive
                          ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold shadow-sm"
                          : "bg-[#080B15]/60 border-white/5 text-slate-400 hover:border-white/20 hover:text-slate-200 text-xs"
                      }`}
                    >
                      <div className="text-xs">{ratio.label}</div>
                      <div className="text-[9px] text-slate-500">{ratio.name}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2">
                Generation Model
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedModel("flux-schnell")}
                  className={`p-2.5 rounded-xl border text-left transition ${
                    selectedModel === "flux-schnell"
                      ? "bg-purple-500/20 border-purple-500 text-white"
                      : "bg-[#080B15]/60 border-white/5 text-slate-400 hover:border-white/20"
                  }`}
                >
                  <div className="text-xs font-bold flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-cyan-400" /> FLUX.1 Schnell
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Ultra-fast, razor sharp</div>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedModel("flux-dev")}
                  className={`p-2.5 rounded-xl border text-left transition ${
                    selectedModel === "flux-dev"
                      ? "bg-purple-500/20 border-purple-500 text-white"
                      : "bg-[#080B15]/60 border-white/5 text-slate-400 hover:border-white/20"
                  }`}
                >
                  <div className="text-xs font-bold flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-purple-400" /> FLUX.1 Dev
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">8K Pro master quality</div>
                </button>
              </div>
            </div>
          </div>

          {/* Error display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-200 text-xs flex items-center gap-2.5"
            >
              <AlertCircle className="h-4 w-4 text-red-400 shrink-0" />
              <span className="flex-1">{error}</span>
              <button onClick={() => setError(null)} className="text-slate-400 hover:text-white">
                <X className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          )}

          {/* Main Action Button */}
          <Button
            type="button"
            onClick={handleGenerate}
            disabled={isGenerating || !prompt.trim()}
            className="w-full h-12 text-sm font-bold uppercase tracking-wider rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white shadow-xl shadow-purple-600/30 hover:shadow-purple-600/50 transition-all duration-300 disabled:opacity-50"
          >
            {isGenerating ? (
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 animate-spin text-cyan-300" />
                <span>Generating Artwork...</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                <span>Create Image</span>
              </div>
            )}
          </Button>
        </div>

        {/* RIGHT PANEL: Interactive Preview Canvas & Gallery */}
        <div className="space-y-6">
          {/* Main Canvas Card */}
          <div className="rounded-2xl bg-[#0F1424]/80 border border-white/10 p-5 shadow-2xl backdrop-blur-xl relative overflow-hidden flex flex-col min-h-[520px]">
            {/* Canvas Header Bar */}
            <div className="flex items-center justify-between pb-3 border-b border-white/5 mb-4">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <ImageIcon className="h-4 w-4 text-cyan-400" />
                <span>Studio Viewport</span>
                {currentImage?.elapsedSeconds && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                    ⚡ {currentImage.elapsedSeconds}s
                  </span>
                )}
              </div>

              {currentImage && (
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopyPrompt}
                    className="h-8 px-2.5 text-xs text-slate-300 hover:text-white hover:bg-white/10 gap-1"
                    title="Copy full prompt"
                  >
                    {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                    <span>{copied ? "Copied!" : "Prompt"}</span>
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setLightboxOpen(true)}
                    className="h-8 px-2 text-slate-300 hover:text-white hover:bg-white/10"
                    title="Full-resolution zoom"
                  >
                    <Maximize2 className="h-3.5 w-3.5" />
                  </Button>

                  <Button
                    size="sm"
                    onClick={handleDownload}
                    className="h-8 px-3 text-xs bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 gap-1.5"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download</span>
                  </Button>
                </div>
              )}
            </div>

            {/* Viewport Center */}
            <div className="flex-1 flex items-center justify-center relative rounded-xl bg-[#080B15]/90 border border-white/5 overflow-hidden min-h-[440px]">
              {isGenerating ? (
                <div className="flex flex-col items-center justify-center p-8 text-center max-w-sm">
                  {/* Glowing Pulse Ring */}
                  <div className="relative mb-6">
                    <div className="h-20 w-20 rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 animate-spin blur-md opacity-75" />
                    <div className="h-20 w-20 rounded-full bg-[#0F1424] absolute inset-0 m-auto flex items-center justify-center border border-white/20">
                      <Sparkles className="h-8 w-8 text-cyan-400 animate-pulse" />
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-white mb-2">Crafting Your Vision</h3>
                  <p className="text-xs text-slate-400 mb-5 leading-relaxed">{progressMessage}</p>

                  {/* Step indicators */}
                  <div className="w-full flex items-center gap-1.5">
                    {[1, 2, 3].map((step) => (
                      <div
                        key={step}
                        className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
                          progressStep >= step ? "bg-gradient-to-r from-purple-500 to-cyan-400" : "bg-white/10"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              ) : currentImage ? (
                <div className="relative w-full h-full flex items-center justify-center group p-2">
                  <img
                    src={currentImage.url}
                    alt={currentImage.prompt}
                    className="max-h-[580px] w-auto max-w-full object-contain rounded-lg shadow-2xl transition duration-300 group-hover:scale-[1.005]"
                  />
                </div>
              ) : (
                <div className="text-center p-8 max-w-sm">
                  <div className="h-16 w-16 mx-auto mb-4 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-500">
                    <ImageIcon className="h-8 w-8" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-1">Canvas is Ready</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Type a prompt or choose "Surprise Me", select an art style, and click Create Image to begin.
                  </p>
                </div>
              )}
            </div>

            {/* Prompt details bar */}
            {currentImage && !isGenerating && (
              <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-slate-400">
                <span className="line-clamp-1 italic max-w-md">"{currentImage.prompt}"</span>
                <span className="text-[11px] text-slate-500 shrink-0 ml-2">
                  {currentImage.width}×{currentImage.height} • {currentImage.model}
                </span>
              </div>
            )}
          </div>

          {/* History Gallery */}
          {history.length > 0 && (
            <div className="rounded-2xl bg-[#0F1424]/80 border border-white/10 p-5 shadow-xl backdrop-blur-xl">
              <div className="flex items-center justify-between mb-3.5">
                <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-cyan-400" /> Recent Studio Creations ({history.length})
                </h2>
                <span className="text-[11px] text-slate-500">Click any image to load</span>
              </div>

              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
                {history.slice(0, 12).map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      setCurrentImage(item);
                      setPrompt(item.prompt);
                    }}
                    className={`group relative aspect-square rounded-xl overflow-hidden border transition-all ${
                      currentImage?.id === item.id
                        ? "border-cyan-400 ring-2 ring-cyan-400/30 scale-[1.02]"
                        : "border-white/10 hover:border-white/30 hover:scale-[1.03]"
                    }`}
                  >
                    <img
                      src={item.url}
                      alt={item.prompt}
                      className="w-full h-full object-cover transition duration-300 group-hover:brightness-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent opacity-0 group-hover:opacity-100 transition p-1.5 flex items-end">
                      <span className="text-[9px] text-white font-medium line-clamp-1">{item.prompt}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Lightbox Zoom Modal */}
      <AnimatePresence>
        {lightboxOpen && currentImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setLightboxOpen(false)}
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4 sm:p-8"
          >
            <button
              onClick={() => setLightboxOpen(false)}
              className="absolute top-5 right-5 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition"
            >
              <X className="h-6 w-6" />
            </button>

            <div
              onClick={(e) => e.stopPropagation()}
              className="max-w-5xl max-h-[90vh] flex flex-col items-center gap-4"
            >
              <img
                src={currentImage.url}
                alt={currentImage.prompt}
                className="max-h-[80vh] w-auto max-w-full rounded-xl shadow-2xl object-contain"
              />
              <div className="flex items-center gap-3">
                <Button
                  size="sm"
                  onClick={handleDownload}
                  className="bg-cyan-500 hover:bg-cyan-400 text-black font-semibold gap-1.5 text-xs"
                >
                  <Download className="h-3.5 w-3.5" /> Download Full PNG
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyPrompt}
                  className="border-white/20 text-white hover:bg-white/10 text-xs"
                >
                  {copied ? "Copied!" : "Copy Prompt"}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
