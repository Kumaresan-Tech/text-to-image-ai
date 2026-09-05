import os
import sys
import time
import json
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import io
import urllib.parse
import requests
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory, render_template_string

# Ensure console supports UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.route("/api/<path:subpath>", methods=["OPTIONS"])
def handle_options(subpath):
    return "", 204

# Output directories
OUTPUTS_DIR = Path(__file__).parent / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Initialize clients lazily
hf_client = None
gemini_client = None

def get_hf_client():
    global hf_client
    if hf_client is None:
        token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
        if not token:
            raise ValueError("HF_TOKEN is missing from .env. Please configure your Hugging Face token.")
        from huggingface_hub import InferenceClient
        hf_client = InferenceClient(api_key=token)
    return hf_client

def get_gemini_client():
    global gemini_client
    if gemini_client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is missing from .env. Please configure your Gemini key.")
        from google import genai
        gemini_client = genai.Client(api_key=key)
    return gemini_client

# Style Presets for Maximum Quality Output
STYLE_PRESETS = {
    "cinematic": {
        "name": "Cinematic",
        "icon": "🎬",
        "prompt_suffix": "cinematic composition, 35mm photography, dramatic volumetric rim lighting, shallow depth of field, color graded, masterpiece 8k, Unreal Engine 5, hyperrealistic textures",
    },
    "photorealistic": {
        "name": "Photorealism",
        "icon": "📸",
        "prompt_suffix": "extreme photorealism, raw photo, detailed anatomy, subsurface scattering, micro-textures, 85mm portrait lens, f/1.4 aperture, natural softbox lighting, 8k resolution",
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "icon": "⚡",
        "prompt_suffix": "futuristic cyberpunk aesthetic, neon cyan and magenta caustics, wet reflective surfaces, atmospheric fog, intricate high-tech mechanical details, cinematic wide angle, ray tracing",
    },
    "fantasy": {
        "name": "Fantasy Art",
        "icon": "✨",
        "prompt_suffix": "mythical fantasy concept art, ethereal volumetric glow, luminous bioluminescent particles, vivid iridescent colors, ArtStation trending, Octane render, ultra detailed illustration",
    },
    "anime": {
        "name": "Anime / Manga",
        "icon": "🌸",
        "prompt_suffix": "stunning anime visual aesthetic, Makoto Shinkai inspired, vibrant dramatic skies, clean crisp line art, beautiful atmospheric lighting, highly detailed masterpiece 4k",
    },
    "3d_render": {
        "name": "3D Octane",
        "icon": "🧊",
        "prompt_suffix": "3D isometric render, premium clay and glass materials, vibrant pastel lighting, tilt-shift lens, Octane render, ray-traced ambient occlusion, C4D showcase",
    },
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AuraCraft AI — Text-to-Image Studio</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['Inter', 'sans-serif'],
            heading: ['Outfit', 'sans-serif'],
            mono: ['Fira Code', 'monospace'],
          },
          colors: {
            brand: {
              50: '#f5f3ff',
              100: '#ede9fe',
              500: '#8b5cf6',
              600: '#7c3aed',
              700: '#6d28d9',
            },
            cyan: {
              400: '#22d3ee',
              500: '#06b6d4',
            }
          }
        }
      }
    }
  </script>
  <style>
    body {
      background-color: #080B12;
      background-image: 
        radial-gradient(at 0% 0%, rgba(124, 58, 237, 0.15) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.15) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(139, 92, 246, 0.08) 0px, transparent 50%);
      background-attachment: fixed;
    }
    .glass-card {
      background: rgba(16, 22, 36, 0.7);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
    }
    .glass-panel {
      background: rgba(22, 30, 48, 0.6);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .gradient-text {
      background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 50%, #ec4899 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .btn-gradient {
      background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #06b6d4 100%);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .btn-gradient:hover {
      box-shadow: 0 0 25px rgba(124, 58, 237, 0.6);
      transform: translateY(-1px);
    }
    .preset-card.active {
      border-color: #8b5cf6;
      background: rgba(139, 92, 246, 0.18);
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.3);
    }
    .model-pill.active {
      border-color: #a855f7;
      background: rgba(168, 85, 247, 0.2);
      box-shadow: 0 0 15px rgba(168, 85, 247, 0.3);
    }
    .ratio-pill.active {
      border-color: #38bdf8;
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
    }
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); }
    ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.15); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.25); }
  </style>
</head>
<body class="text-slate-100 min-h-screen flex flex-col antialiased selection:bg-purple-500 selection:text-white">

  <!-- TOP HEADER -->
  <header class="border-b border-white/10 bg-[#080B12]/80 backdrop-blur-md sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-cyan-400 p-[1px] shadow-lg shadow-purple-500/20">
          <div class="w-full h-full bg-[#0E1322] rounded-xl flex items-center justify-center">
            <span class="text-xl">✨</span>
          </div>
        </div>
        <div>
          <span class="font-heading font-bold text-xl tracking-tight text-white flex items-center gap-2">
            AuraCraft <span class="gradient-text text-sm font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20">Studio</span>
          </span>
        </div>
      </div>

      <!-- Engine Status Badges -->
      <div class="hidden sm:flex items-center gap-3 text-xs">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>FLUX.1 Schnell: Ready</span>
        </div>
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300">
          <span class="w-2 h-2 rounded-full bg-purple-400"></span>
          <span>Gemini 3.6: Active</span>
        </div>
      </div>
    </div>
  </header>

  <!-- MAIN STUDIO CONTAINER -->
  <main class="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 grid grid-cols-1 lg:grid-cols-12 gap-6">

    <!-- LEFT COLUMN: CONTROLS & PROMPT (5 cols) -->
    <div class="lg:col-span-5 space-y-5">

      <!-- PROMPT CARD -->
      <div class="glass-card rounded-2xl p-5 space-y-4">
        <div class="flex items-center justify-between">
          <label class="font-heading font-semibold text-sm tracking-wide text-slate-200 flex items-center gap-2">
            <span>📝</span> Prompt Description
          </label>
          <button id="enhanceBtn" onclick="enhancePrompt()" class="flex items-center gap-1.5 text-xs font-medium text-purple-300 hover:text-white px-2.5 py-1 rounded-lg bg-purple-500/15 border border-purple-500/30 hover:bg-purple-500/25 transition">
            <span id="enhanceIcon">✨</span>
            <span id="enhanceText">Enhance with Gemini</span>
          </button>
        </div>

        <div class="relative">
          <textarea id="promptInput" rows="4" placeholder="Describe the image you imagine... e.g. A cybernetic snow leopard with glowing runes on a misty mountain ridge, 8k resolution" class="w-full bg-[#0D121F] border border-white/10 rounded-xl p-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition resize-none"></textarea>
          <div class="text-[11px] text-slate-500 text-right mt-1" id="charCount">0 characters</div>
        </div>

        <!-- STYLE PRESETS -->
        <div>
          <label class="font-heading font-semibold text-xs text-slate-300 uppercase tracking-wider block mb-2.5">
            🎨 Artistic Style Presets
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button type="button" onclick="selectStyle('cinematic')" class="preset-card active text-left p-2.5 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.06] transition flex flex-col gap-1" data-style="cinematic">
              <span class="text-base">🎬</span>
              <span class="font-medium text-xs text-slate-200">Cinematic</span>
              <span class="text-[10px] text-slate-400">Movie Lighting</span>
            </button>
            <button type="button" onclick="selectStyle('photorealistic')" class="preset-card text-left p-2.5 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.06] transition flex flex-col gap-1" data-style="photorealistic">
              <span class="text-base">📸</span>
              <span class="font-medium text-xs text-slate-200">Photoreal</span>
              <span class="text-[10px] text-slate-400">8K Macro Lens</span>
            </button>
            <button type="button" onclick="selectStyle('cyberpunk')" class="preset-card text-left p-2.5 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.06] transition flex flex-col gap-1" data-style="cyberpunk">
              <span class="text-base">⚡</span>
              <span class="font-medium text-xs text-slate-200">Cyberpunk</span>
              <span class="text-[10px] text-slate-400">Neon Caustics</span>
            </button>
            <button type="button" onclick="selectStyle('fantasy')" class="preset-card text-left p-2.5 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.06] transition flex flex-col gap-1" data-style="fantasy">
              <span class="text-base">✨</span>
              <span class="font-medium text-xs text-slate-200">Fantasy</span>
              <span class="text-[10px] text-slate-400">Ethereal Glow</span>
            </button>
            <button type="button" onclick="selectStyle('anime')" class="preset-card text-left p-2.5 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.06] transition flex flex-col gap-1" data-style="anime">
              <span class="text-base">🌸</span>
              <span class="font-medium text-xs text-slate-200">Anime</span>
              <span class="text-[10px] text-slate-400">Shinkai Style</span>
            </button>
            <button type="button" onclick="selectStyle('3d_render')" class="preset-card text-left p-2.5 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.06] transition flex flex-col gap-1" data-style="3d_render">
              <span class="text-base">🧊</span>
              <span class="font-medium text-xs text-slate-200">3D Octane</span>
              <span class="text-[10px] text-slate-400">Ray Traced</span>
            </button>
          </div>
        </div>

        <!-- MODEL SELECTOR -->
        <div>
          <label class="font-heading font-semibold text-xs text-slate-300 uppercase tracking-wider block mb-2.5">
            🤖 AI Generator Engine
          </label>
          <div class="grid grid-cols-3 gap-2">
            <button type="button" onclick="selectModel('flux-schnell')" class="model-pill active py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-model="flux-schnell">
              <div class="font-semibold text-purple-300">FLUX Fast</div>
              <div class="text-[10px] text-slate-400">Schnell (4 steps)</div>
            </button>
            <button type="button" onclick="selectModel('flux-dev')" class="model-pill py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-model="flux-dev">
              <div class="font-semibold text-cyan-300">FLUX Dev</div>
              <div class="text-[10px] text-slate-400">Pro 8K (25 steps)</div>
            </button>
            <button type="button" onclick="selectModel('demo')" class="model-pill py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-model="demo">
              <div class="font-semibold text-emerald-300">Demo Free</div>
              <div class="text-[10px] text-slate-400">High Speed AI</div>
            </button>
          </div>
        </div>

        <!-- ASPECT RATIO -->
        <div>
          <label class="font-heading font-semibold text-xs text-slate-300 uppercase tracking-wider block mb-2.5">
            📐 Aspect Ratio & Resolution
          </label>
          <div class="grid grid-cols-4 gap-2">
            <button type="button" onclick="selectRatio('1:1', 1024, 1024)" class="ratio-pill active py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-ratio="1:1">
              <div class="font-semibold">1:1</div>
              <div class="text-[10px] text-slate-400">1024×1024</div>
            </button>
            <button type="button" onclick="selectRatio('16:9', 1280, 720)" class="ratio-pill py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-ratio="16:9">
              <div class="font-semibold">16:9</div>
              <div class="text-[10px] text-slate-400">Landscape</div>
            </button>
            <button type="button" onclick="selectRatio('9:16', 720, 1280)" class="ratio-pill py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-ratio="9:16">
              <div class="font-semibold">9:16</div>
              <div class="text-[10px] text-slate-400">Portrait</div>
            </button>
            <button type="button" onclick="selectRatio('4:3', 1152, 864)" class="ratio-pill py-2 px-2 text-center rounded-xl border border-white/10 text-xs font-medium bg-white/[0.02] hover:bg-white/[0.05] transition" data-ratio="4:3">
              <div class="font-semibold">4:3</div>
              <div class="text-[10px] text-slate-400">Classic</div>
            </button>
          </div>
        </div>

        <!-- GENERATE BUTTON -->
        <button id="generateBtn" onclick="generateImage()" class="w-full btn-gradient text-white font-heading font-semibold py-3.5 px-6 rounded-xl shadow-lg flex items-center justify-center gap-2 text-sm tracking-wide transition mt-2">
          <span id="genBtnIcon">🎨</span>
          <span id="genBtnText">Generate Masterpiece</span>
        </button>
      </div>

    </div>

    <!-- RIGHT COLUMN: SHOWCASE & LIVE CANVAS (7 cols) -->
    <div class="lg:col-span-7 space-y-5 flex flex-col">

      <!-- PREVIEW CANVAS CARD -->
      <div class="glass-card rounded-2xl p-5 flex-1 flex flex-col justify-between relative min-h-[460px]">
        
        <!-- Header status inside preview -->
        <div class="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
          <div class="flex items-center gap-2">
            <span class="font-heading font-medium text-xs text-slate-400">Active Canvas</span>
            <span id="metaBadge" class="hidden text-[11px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">FLUX.1 Schnell • 1024×1024</span>
          </div>

          <div id="imageActions" class="hidden flex items-center gap-2">
            <button onclick="openLightbox()" class="text-xs text-slate-300 hover:text-white px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 transition flex items-center gap-1">
              🔍 Fullscreen
            </button>
            <a id="downloadLink" href="#" download="aura_masterpiece.png" class="text-xs font-medium text-cyan-300 hover:text-white px-2.5 py-1 rounded-lg bg-cyan-500/15 border border-cyan-500/30 hover:bg-cyan-500/25 transition flex items-center gap-1">
              ⬇️ Download PNG
            </a>
          </div>
        </div>

        <!-- Center Image Stage -->
        <div id="stageContainer" class="flex-1 flex items-center justify-center relative rounded-xl overflow-hidden bg-[#0A0E18] border border-white/5 p-2">
          
          <!-- Idle Placeholder -->
          <div id="idleStage" class="text-center p-8 space-y-3">
            <div class="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 mx-auto flex items-center justify-center text-2xl animate-pulse">
              🖼️
            </div>
            <h3 class="font-heading font-semibold text-slate-300 text-base">Your Studio Canvas is Ready</h3>
            <p class="text-xs text-slate-500 max-w-sm mx-auto">
              Enter a prompt or select a style preset on the left, then click Generate to produce an ultra high-quality 8K artwork.
            </p>
          </div>

          <!-- Loading Stage -->
          <div id="loadingStage" class="hidden text-center p-8 space-y-4">
            <div class="relative w-16 h-16 mx-auto">
              <div class="absolute inset-0 rounded-full border-2 border-purple-500/30 border-t-purple-500 animate-spin"></div>
              <div class="absolute inset-2 rounded-full border-2 border-cyan-500/30 border-b-cyan-400 animate-spin" style="animation-direction: reverse;"></div>
              <div class="absolute inset-0 flex items-center justify-center text-xl">✨</div>
            </div>
            <div>
              <div id="loadingStep" class="font-heading font-semibold text-slate-200 text-sm">Rendering image with FLUX.1 Schnell...</div>
              <div id="loadingSubtext" class="text-xs text-slate-400 mt-1">Applying lighting, volumetric textures & style...</div>
            </div>
          </div>

          <!-- Active Image Display -->
          <div id="imageDisplay" class="hidden w-full h-full flex items-center justify-center">
            <img id="activeImg" src="" alt="AI Generated Image" class="max-h-[480px] w-auto object-contain rounded-lg shadow-2xl transition duration-300" />
          </div>

        </div>

        <!-- Prompt readout bar below image -->
        <div id="promptReadout" class="hidden mt-4 pt-3 border-t border-white/5">
          <div class="text-[11px] font-mono text-slate-400 line-clamp-2">
            <span class="text-purple-400 font-semibold">Prompt:</span> <span id="promptTextOutput"></span>
          </div>
        </div>

      </div>

    </div>

  </main>

  <!-- RECENT GENERATIONS GALLERY -->
  <section class="max-w-7xl mx-auto w-full px-4 sm:px-6 pb-12">
    <div class="glass-card rounded-2xl p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="font-heading font-semibold text-sm text-slate-200 flex items-center gap-2">
          <span>📁</span> Studio History & Recent Outputs
        </h3>
        <button onclick="loadHistory()" class="text-xs text-slate-400 hover:text-white transition">
          🔄 Refresh Gallery
        </button>
      </div>

      <div id="galleryGrid" class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 min-h-[120px]">
        <!-- Gallery cards populated via JS -->
      </div>
    </div>
  </section>

  <!-- LIGHTBOX MODAL -->
  <div id="lightbox" class="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl hidden flex items-center justify-center p-4">
    <div class="relative max-w-5xl w-full max-h-[90vh] flex flex-col items-center">
      <button onclick="closeLightbox()" class="absolute top-2 right-2 text-white/70 hover:text-white text-2xl p-2 rounded-lg bg-white/10 hover:bg-white/20 transition z-10">✕</button>
      <img id="lightboxImg" src="" alt="Enlarged Artwork" class="max-h-[85vh] w-auto object-contain rounded-xl shadow-2xl border border-white/10" />
    </div>
  </div>

  <!-- TOAST NOTIFICATION -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 transform translate-y-20 opacity-0 transition duration-300 pointer-events-none">
    <div class="glass-panel px-4 py-3 rounded-xl border border-purple-500/30 text-xs text-white shadow-2xl flex items-center gap-2.5">
      <span id="toastIcon">✨</span>
      <span id="toastMsg">Ready</span>
    </div>
  </div>

  <script>
    let currentStyle = 'cinematic';
    let currentRatio = { ratio: '1:1', w: 1024, h: 1024 };
    let currentModel = 'flux-schnell';

    const promptInput = document.getElementById('promptInput');
    const charCount = document.getElementById('charCount');

    promptInput.addEventListener('input', () => {
      charCount.textContent = `${promptInput.value.length} characters`;
    });

    function showToast(msg, icon = '✨') {
      const toast = document.getElementById('toast');
      document.getElementById('toastMsg').textContent = msg;
      document.getElementById('toastIcon').textContent = icon;
      toast.classList.remove('translate-y-20', 'opacity-0');
      setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
      }, 3500);
    }

    function selectModel(modelKey) {
      currentModel = modelKey;
      document.querySelectorAll('.model-pill').forEach(btn => {
        if (btn.getAttribute('data-model') === modelKey) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      const names = {
        'flux-schnell': 'FLUX.1 Schnell (Fast - 4 steps)',
        'flux-dev': 'FLUX.1 Dev (Pro 8K - 25 steps)',
        'demo': 'Demo Free (High Speed AI)'
      };
      showToast(`Selected Engine: ${names[modelKey] || modelKey}`, '🤖');
    }

    function selectStyle(styleKey) {
      currentStyle = styleKey;
      document.querySelectorAll('.preset-card').forEach(btn => {
        if (btn.getAttribute('data-style') === styleKey) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      showToast(`Selected style: ${styleKey}`, '🎨');
    }

    function selectRatio(ratioStr, w, h) {
      currentRatio = { ratio: ratioStr, w, h };
      document.querySelectorAll('.ratio-pill').forEach(btn => {
        if (btn.getAttribute('data-ratio') === ratioStr) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      showToast(`Resolution set to ${w}×${h} (${ratioStr})`, '📐');
    }

    async function enhancePrompt() {
      const userPrompt = promptInput.value.trim();
      if (!userPrompt) {
        showToast('Please enter a basic prompt first to enhance it!', '⚠️');
        return;
      }

      const enhanceBtn = document.getElementById('enhanceBtn');
      const enhanceText = document.getElementById('enhanceText');
      enhanceBtn.disabled = true;
      enhanceText.textContent = 'Enhancing...';

      try {
        const resp = await fetch('/api/enhance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: userPrompt, style: currentStyle })
        });
        const data = await resp.json();
        if (data.enhanced_prompt) {
          promptInput.value = data.enhanced_prompt;
          charCount.textContent = `${promptInput.value.length} characters`;
          showToast('Prompt enhanced by Gemini 3.6 Flash!', '🚀');
        } else if (data.error) {
          showToast(data.error, '⚠️');
        }
      } catch (err) {
        showToast('Enhancement error: ' + err.message, '❌');
      } finally {
        enhanceBtn.disabled = false;
        enhanceText.textContent = 'Enhance with Gemini';
      }
    }

    async function generateImage() {
      const rawPrompt = promptInput.value.trim();
      if (!rawPrompt) {
        showToast('Please enter an image prompt!', '⚠️');
        return;
      }

      const generateBtn = document.getElementById('generateBtn');
      const genBtnText = document.getElementById('genBtnText');
      const idleStage = document.getElementById('idleStage');
      const loadingStage = document.getElementById('loadingStage');
      const imageDisplay = document.getElementById('imageDisplay');
      const imageActions = document.getElementById('imageActions');
      const metaBadge = document.getElementById('metaBadge');
      const promptReadout = document.getElementById('promptReadout');

      generateBtn.disabled = true;
      const isDev = currentModel === 'flux-dev';
      genBtnText.textContent = isDev ? 'Generating Pro 8K (~15s)...' : 'Generating (~8s)...';
      idleStage.classList.add('hidden');
      imageDisplay.classList.add('hidden');
      loadingStage.classList.remove('hidden');

      try {
        const resp = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: rawPrompt,
            style: currentStyle,
            model: currentModel,
            width: currentRatio.w,
            height: currentRatio.h,
          })
        });

        const data = await resp.json();

        if (data.success) {
          const activeImg = document.getElementById('activeImg');
          activeImg.src = data.image_url + '?t=' + new Date().getTime();
          
          document.getElementById('downloadLink').href = data.image_url;
          document.getElementById('promptTextOutput').textContent = data.final_prompt;
          
          metaBadge.textContent = `${data.model} • ${data.width}×${data.height} • ${data.elapsed_seconds}s`;
          metaBadge.classList.remove('hidden');
          imageActions.classList.remove('hidden');
          promptReadout.classList.remove('hidden');

          loadingStage.classList.add('hidden');
          imageDisplay.classList.remove('hidden');

          showToast('Image generated successfully!', '🎉');
          loadHistory();
        } else {
          showToast(data.error || 'Generation failed', '❌');
          loadingStage.classList.add('hidden');
          idleStage.classList.remove('hidden');
        }
      } catch (err) {
        showToast('Generation error: ' + err.message, '❌');
        loadingStage.classList.add('hidden');
        idleStage.classList.remove('hidden');
      } finally {
        generateBtn.disabled = false;
        genBtnText.textContent = 'Generate Masterpiece';
      }
    }

    async function loadHistory() {
      try {
        const resp = await fetch('/api/history');
        const data = await resp.json();
        const grid = document.getElementById('galleryGrid');
        grid.innerHTML = '';

        if (!data.images || data.images.length === 0) {
          grid.innerHTML = '<div class="col-span-full text-center text-xs text-slate-500 py-6">No previous generations found. Generate an image above!</div>';
          return;
        }

        data.images.forEach(img => {
          const card = document.createElement('div');
          card.className = 'group relative aspect-square rounded-xl overflow-hidden border border-white/10 bg-black/40 cursor-pointer';
          card.innerHTML = `
            <img src="${img.url}" alt="Saved artwork" class="w-full h-full object-cover transition duration-300 group-hover:scale-110" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition p-2 flex items-end justify-between">
              <span class="text-[10px] text-slate-300 font-mono">${img.created_at}</span>
              <a href="${img.url}" download class="text-xs text-cyan-300 hover:text-white">⬇️</a>
            </div>
          `;
          card.addEventListener('click', (e) => {
            if (e.target.tagName !== 'A') {
              viewSavedImage(img.url, img.filename);
            }
          });
          grid.appendChild(card);
        });
      } catch (err) {
        console.error('Failed to load history:', err);
      }
    }

    function viewSavedImage(url, filename) {
      const activeImg = document.getElementById('activeImg');
      activeImg.src = url;
      document.getElementById('downloadLink').href = url;
      document.getElementById('metaBadge').textContent = `Archived • ${filename}`;
      document.getElementById('metaBadge').classList.remove('hidden');
      document.getElementById('imageActions').classList.remove('hidden');
      document.getElementById('idleStage').classList.add('hidden');
      document.getElementById('loadingStage').classList.add('hidden');
      document.getElementById('imageDisplay').classList.remove('hidden');
      showToast('Loaded image from history', '📁');
    }

    function openLightbox() {
      const activeImg = document.getElementById('activeImg');
      if (!activeImg.src) return;
      document.getElementById('lightboxImg').src = activeImg.src;
      document.getElementById('lightbox').classList.remove('hidden');
    }

    function closeLightbox() {
      document.getElementById('lightbox').classList.add('hidden');
    }

    // Load initial history on page load
    loadHistory();
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/outputs/<filename>")
def serve_output(filename):
    return send_from_directory(OUTPUTS_DIR, filename)

@app.route("/api/enhance", methods=["POST"])
def enhance_api():
    data = request.get_json() or {}
    user_prompt = (data.get("prompt") or "").strip()
    style_key = data.get("style", "cinematic")
    
    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    style_info = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    style_hint = style_info["prompt_suffix"]

    instruction = f"""
You are an expert AI image prompt engineer.
Convert the user's simple request into an ultra high-quality, descriptive prompt for an AI image generator (FLUX.1).

Style Directive: {style_info['name']} ({style_hint})

Include:
- Clear subject details and anatomy
- Environment and atmosphere
- Specific cinematic/photographic lighting (e.g. volumetric rays, rim light)
- Camera perspective and lens (e.g. 35mm, macro, wide-angle)
- Textures, color tones, and rich artistic modifiers

Return ONLY the enhanced prompt string without any quotes or explanations.

User Request: {user_prompt}
"""
    try:
        gemini = get_gemini_client()
        response = gemini.models.generate_content(
            model="gemini-3.6-flash",
            contents=instruction
        )
        enhanced = response.text.strip() if response and response.text else user_prompt
        return jsonify({"enhanced_prompt": enhanced})
    except Exception as e:
        # Fallback to appending style keywords
        fallback = f"{user_prompt}, {style_hint}"
        return jsonify({"enhanced_prompt": fallback, "note": f"Gemini fallback: {str(e)[:50]}"})

@app.route("/api/generate", methods=["POST"])
def generate_api():
    data = request.get_json() or {}
    user_prompt = (data.get("prompt") or "").strip()
    style_key = data.get("style", "cinematic")
    model_choice = data.get("model", "flux-schnell")
    width = int(data.get("width", 1024))
    height = int(data.get("height", 1024))

    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Apply style preset keywords if not already present
    style_info = STYLE_PRESETS.get(style_key, STYLE_PRESETS["cinematic"])
    final_prompt = user_prompt
    if style_info["prompt_suffix"].split()[0].lower() not in user_prompt.lower():
        final_prompt = f"{user_prompt}, {style_info['prompt_suffix']}"

    start_time = time.time()
    image = None
    model_display = "FLUX.1 Schnell"

    # Step 1: Attempt Hugging Face if HF_TOKEN is configured and model is FLUX
    if model_choice in ("flux-dev", "flux-schnell") and os.getenv("HF_TOKEN"):
        try:
            client = get_hf_client()
            if model_choice == "flux-dev":
                hf_model = "black-forest-labs/FLUX.1-dev"
                steps = 25
                guidance = 3.5
                model_display = "FLUX.1 Dev (Pro 8K)"
            else:
                hf_model = "black-forest-labs/FLUX.1-schnell"
                steps = 4
                guidance = 0.0
                model_display = "FLUX.1 Schnell (Fast)"

            image = client.text_to_image(
                prompt=final_prompt,
                model=hf_model,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance,
            )
        except Exception as hf_err:
            print(f"[Engine Fallback] Hugging Face error ({hf_err}), switching to high-speed FLUX engine...")
            image = None

    # Step 2: High-speed FLUX generation (for Demo Free, or whenever HF credit is exhausted)
    if image is None:
        if model_choice == "flux-dev":
            poll_model = "flux-realism"
            model_display = "FLUX.1 Dev (Pro 8K)"
        elif model_choice == "flux-schnell":
            poll_model = "flux"
            model_display = "FLUX.1 Schnell (Fast)"
        else:
            poll_model = "turbo"
            model_display = "Demo Free (High Speed AI)"

        encoded_prompt = urllib.parse.quote(final_prompt)
        seed = int(time.time() * 1000) % 2147483647
        candidate_urls = [
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={poll_model}&width={width}&height={height}&seed={seed}&nologo=true",
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true",
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=turbo&width={width}&height={height}&seed={seed}&nologo=true",
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        for cand_url in candidate_urls:
            try:
                resp = requests.get(cand_url, headers=headers, timeout=45)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    image = Image.open(io.BytesIO(resp.content))
                    break
            except Exception:
                continue

        if image is None:
            return jsonify({"error": "AI Engine is temporarily busy. Please retry in a moment."}), 500

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aura_{timestamp}.png"
    file_path = OUTPUTS_DIR / filename

    image.save(file_path, format="PNG")
    image.save(OUTPUTS_DIR / "generated_image.png", format="PNG")

    elapsed = round(time.time() - start_time, 2)

    return jsonify({
        "success": True,
        "filename": filename,
        "image_url": f"/outputs/{filename}",
        "final_prompt": final_prompt,
        "model": model_display,
        "width": width,
        "height": height,
        "elapsed_seconds": elapsed,
    })

@app.route("/api/history", methods=["GET"])
def history_api():
    images = []
    for p in sorted(OUTPUTS_DIR.glob("*.png"), key=os.path.getmtime, reverse=True):
        if p.name == "generated_image.png":
            continue
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%b %d, %H:%M")
        images.append({
            "filename": p.name,
            "url": f"/outputs/{p.name}",
            "created_at": mtime,
        })
    return jsonify({"images": images[:30]})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    print("\n" + "=" * 55)
    print("  🎨 AuraCraft AI — Premium Text-to-Image Dashboard")
    print("=" * 55)
    print(f"  👉 Open Studio Dashboard: http://127.0.0.1:{port}")
    print("  ⚡ Engine: FLUX.1 Schnell + Gemini 3.6 Flash")
    print("=" * 55 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False)
