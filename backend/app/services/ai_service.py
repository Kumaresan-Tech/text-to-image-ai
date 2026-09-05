import asyncio
import random
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field

import httpx
from huggingface_hub import AsyncInferenceClient

from app.config import settings


# ── Scheduler / Sampler Mapping ──────────────────
SAMPLER_MAP: Dict[str, Dict[str, str]] = {
    "DPM++ 2M Karras":       {"sampler_name": "dpmpp_2m",          "scheduler": "karras"},
    "DPM++ 2M SDE Karras":   {"sampler_name": "dpmpp_2m_sde",      "scheduler": "karras"},
    "DPM++ SDE Karras":      {"sampler_name": "dpmpp_sde",         "scheduler": "karras"},
    "Euler a":               {"sampler_name": "euler_ancestral",    "scheduler": "normal"},
    "Euler":                 {"sampler_name": "euler",              "scheduler": "normal"},
    "DDIM":                  {"sampler_name": "ddim",               "scheduler": "normal"},
    "Heun":                  {"sampler_name": "heun",               "scheduler": "normal"},
    "DPM++ 3M SDE Karras":   {"sampler_name": "dpmpp_3m_sde",      "scheduler": "karras"},
    "UniPC":                 {"sampler_name": "uni_pc",             "scheduler": "normal"},
}

# ── Model Registry ───────────────────────────────
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "sdxl-1.0": {
        "name": "Stable Diffusion XL 1.0",
        "comfyui_checkpoint": "sd_xl_base_1.0.safetensors",
        "provider": "comfyui",
        "default_steps": 30,
        "default_cfg": 7.5,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 100,
    },
    "sd-3.5-large": {
        "name": "Stable Diffusion 3.5 Large",
        "comfyui_checkpoint": "sd3.5_large.safetensors",
        "provider": "comfyui",
        "default_steps": 28,
        "default_cfg": 7.0,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 80,
    },
    "flux-dev": {
        "name": "FLUX.1 Dev",
        "provider": "huggingface",
        "huggingface_model": "black-forest-labs/FLUX.1-dev",
        "comfyui_checkpoint": "flux1-dev.safetensors",
        "default_steps": 25,
        "default_cfg": 3.5,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 50,
    },
    "flux-schnell": {
        "name": "FLUX.1 Schnell",
        "provider": "huggingface",
        "huggingface_model": "black-forest-labs/FLUX.1-schnell",
        "comfyui_checkpoint": "flux1-schnell.safetensors",
        "default_steps": 4,
        "default_cfg": 0.0,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 12,
    },
    "hf-sdxl": {
        "name": "SDXL (HuggingFace)",
        "provider": "huggingface",
        "huggingface_model": "stabilityai/stable-diffusion-xl-base-1.0",
        "default_steps": 30,
        "default_cfg": 7.5,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 50,
    },
    "hf-flux": {
        "name": "FLUX.1 Schnell (HuggingFace)",
        "provider": "huggingface",
        "huggingface_model": "black-forest-labs/FLUX.1-schnell",
        "default_steps": 4,
        "default_cfg": 0.0,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 12,
    },
    "replicate-flux": {
        "name": "FLUX.1 (Replicate)",
        "provider": "replicate",
        "default_steps": 25,
        "default_cfg": 3.5,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 50,
    },
    "gemini-imagen": {
        "name": "Gemini Imagen",
        "provider": "gemini",
        "default_steps": 30,
        "default_cfg": 7.5,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 50,
    },
    "demo": {
        "name": "Demo (Free AI)",
        "provider": "placeholder",
        "huggingface_model": "black-forest-labs/FLUX.1-schnell",
        "default_steps": 4,
        "default_cfg": 0.0,
        "default_width": 1024,
        "default_height": 1024,
        "max_steps": 12,
    },
}


@dataclass
class GenerationResult:
    image_bytes: bytes
    seed_used: int
    width: int
    height: int
    model: str
    elapsed_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        params: Dict[str, Any],
        on_progress: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> GenerationResult:
        raise NotImplementedError

    async def health_check(self) -> bool:
        return True


# ── ComfyUI Provider ─────────────────────────────
class ComfyUIProvider(AIProvider):
    name = "comfyui"

    def __init__(self):
        self.base_url = settings.COMFYUI_URL
        self.timeout = settings.COMFYUI_TIMEOUT

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/system_stats")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        params: Dict[str, Any],
        on_progress: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> GenerationResult:
        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        sampler_key = params.get("sampler", "DPM++ 2M Karras")
        sampler_config = SAMPLER_MAP.get(sampler_key, SAMPLER_MAP["DPM++ 2M Karras"])

        is_flux = "flux" in params.get("model", "").lower()
        workflow = self._build_sdxl_workflow(params, seed, sampler_config) if not is_flux else self._build_flux_workflow(params, seed)

        if on_progress:
            await on_progress("Submitting to GPU...", 5)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/prompt", json={"prompt": workflow})
            resp.raise_for_status()
            prompt_id = resp.json()["prompt_id"]

            if on_progress:
                await on_progress("Queued for generation...", 10)

            start_time = time.time()
            poll_interval = 0.5

            while True:
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    raise TimeoutError(f"Generation timed out after {self.timeout}s")

                status_resp = await client.get(f"{self.base_url}/history/{prompt_id}")
                history = status_resp.json()

                if prompt_id in history:
                    status_msg = history[prompt_id].get("status", {})
                    if status_msg.get("completed", False) or status_msg.get("status_str") == "success":
                        if on_progress:
                            await on_progress("Decoding image...", 90)

                        outputs = history[prompt_id]["outputs"]
                        for node_id, node_output in outputs.items():
                            if "images" in node_output:
                                img_info = node_output["images"][0]
                                img_resp = await client.get(
                                    f"{self.base_url}/view",
                                    params={
                                        "filename": img_info["filename"],
                                        "subfolder": img_info.get("subfolder", ""),
                                        "type": "output",
                                    },
                                )
                                img_resp.raise_for_status()

                                elapsed_secs = time.time() - start_time
                                return GenerationResult(
                                    image_bytes=img_resp.content,
                                    seed_used=seed,
                                    width=params.get("width", 1024),
                                    height=params.get("height", 1024),
                                    model=params.get("model", "sdxl-1.0"),
                                    elapsed_seconds=round(elapsed_secs, 2),
                                    metadata={
                                        "sampler": sampler_key,
                                        "steps": params.get("steps", 30),
                                        "cfg_scale": params.get("cfg_scale", 7.5),
                                        "comfyui_prompt_id": prompt_id,
                                    },
                                )

                if on_progress:
                    progress = min(85, 10 + int((elapsed / self.timeout) * 75))
                    queue = history.get(prompt_id, {}).get("status", {}).get("queue_remaining", None)
                    status_text = f"Generating... ({elapsed:.0f}s)"
                    if queue is not None:
                        status_text += f" [queue: {queue}]"
                    await on_progress(status_text, progress)

                await asyncio.sleep(poll_interval)

    def _build_sdxl_workflow(self, params: Dict[str, Any], seed: int, sampler_config: Dict) -> Dict:
        ckpt = MODEL_REGISTRY.get(params.get("model", "sdxl-1.0"), {}).get("comfyui_checkpoint", "sd_xl_base_1.0.safetensors")
        negative = params.get("negative_prompt", "") or ""
        batch = params.get("num_images", 1)

        return {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": ckpt},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": params.get("width", 1024),
                    "height": params.get("height", 1024),
                    "batch_size": batch,
                },
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": params.get("prompt", ""), "clip": ["4", 1]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": negative, "clip": ["4", 1]},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": params.get("steps", 30),
                    "cfg": params.get("cfg_scale", 7.5),
                    "sampler_name": sampler_config["sampler_name"],
                    "scheduler": sampler_config["scheduler"],
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "t2i", "images": ["8", 0]},
            },
        }

    def _build_flux_workflow(self, params: Dict[str, Any], seed: int) -> Dict:
        ckpt = MODEL_REGISTRY.get(params.get("model", "flux-dev"), {}).get("comfyui_checkpoint", "flux1-dev.safetensors")

        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": ckpt},
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": params.get("prompt", ""), "clip": ["1", 1]},
            },
            "3": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": params.get("width", 1024),
                    "height": params.get("height", 1024),
                    "batch_size": params.get("num_images", 1),
                },
            },
            "4": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": params.get("steps", 20),
                    "cfg": params.get("cfg_scale", 3.5),
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["2", 0],
                    "latent_image": ["3", 0],
                },
            },
            "5": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["4", 0], "vae": ["1", 2]},
            },
            "6": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "t2i_flux", "images": ["5", 0]},
            },
        }


# ── HuggingFace Inference Provider ───────────────
class HuggingFaceProvider(AIProvider):
    name = "huggingface"

    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY or settings.HF_TOKEN
        self.model = settings.HUGGINGFACE_MODEL or "black-forest-labs/FLUX.1-schnell"

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.head("https://huggingface.co")
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        params: Dict[str, Any],
        on_progress: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("HuggingFace API key not configured")

        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        model_key = params.get("model", "hf-flux")
        model_id = MODEL_REGISTRY.get(model_key, {}).get("huggingface_model") or self.model
        if not model_id or "sdxl" in model_id.lower():
            # SDXL router frequently returns 502 Bad Gateway; use reliable FLUX.1-schnell
            model_id = "black-forest-labs/FLUX.1-schnell"

        if on_progress:
            await on_progress("Sending to HuggingFace pipeline...", 10)

        start_time = time.time()
        client = AsyncInferenceClient(api_key=self.api_key)

        try:
            if on_progress:
                await on_progress(f"Generating image on HuggingFace ({model_id.split('/')[-1]})...", 35)

            is_dev = "dev" in model_id.lower()
            is_schnell = "schnell" in model_id.lower()

            if is_dev:
                steps = params.get("steps", 25)
                guidance = params.get("cfg_scale", 3.5)
            elif is_schnell:
                steps = 4
                guidance = 0.0
            else:
                steps = params.get("steps", 30)
                guidance = params.get("cfg_scale", 7.5)

            try:
                image = await client.text_to_image(
                    prompt=params.get("prompt", ""),
                    model=model_id,
                    negative_prompt=params.get("negative_prompt", "") if not (is_dev or is_schnell) else None,
                    width=params.get("width", 1024),
                    height=params.get("height", 1024),
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    seed=seed,
                )
            except Exception as first_err:
                # If chosen model fails (e.g. 502 Bad Gateway on SDXL), fallback to FLUX.1-schnell
                if model_id != "black-forest-labs/FLUX.1-schnell":
                    if on_progress:
                        await on_progress("Model unavailable, switching to FLUX.1 Schnell...", 45)
                    model_id = "black-forest-labs/FLUX.1-schnell"
                    image = await client.text_to_image(
                        prompt=params.get("prompt", ""),
                        model=model_id,
                        width=params.get("width", 1024),
                        height=params.get("height", 1024),
                        num_inference_steps=4,
                        guidance_scale=0.0,
                        seed=seed,
                    )
                else:
                    raise first_err

            if on_progress:
                await on_progress("Image received, processing...", 90)

            import io
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            img_bytes = buf.getvalue()

            elapsed = time.time() - start_time
            return GenerationResult(
                image_bytes=img_bytes,
                seed_used=seed,
                width=params.get("width", 1024),
                height=params.get("height", 1024),
                model=model_key,
                elapsed_seconds=round(elapsed, 2),
                metadata={"provider": "huggingface", "model": model_id},
            )
        except Exception as e:
            logger.warning(f"HuggingFace inference error: {e}. Falling back to high-speed FLUX engine...")
            if on_progress:
                await on_progress("Switching to high-speed FLUX engine...", 40)

            import urllib.parse
            w = params.get("width", 1024)
            h = params.get("height", 1024)
            prompt_text = params.get("prompt", "")

            encoded = urllib.parse.quote(prompt_text)
            candidate_urls = [
                f"https://image.pollinations.ai/prompt/{encoded}?model=flux&width={w}&height={h}&seed={seed}&nologo=true",
                f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true",
                f"https://image.pollinations.ai/prompt/{encoded}?model=turbo&width={w}&height={h}&seed={seed}&nologo=true",
            ]
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            for cand_url in candidate_urls:
                try:
                    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as fb_client:
                        resp = await fb_client.get(cand_url, headers=headers)
                        if resp.status_code == 200 and len(resp.content) > 1000:
                            elapsed = time.time() - start_time
                            return GenerationResult(
                                image_bytes=resp.content,
                                seed_used=seed,
                                width=w,
                                height=h,
                                model=model_key,
                                elapsed_seconds=round(elapsed, 2),
                                metadata={"provider": "flux-engine", "source": cand_url},
                            )
                except Exception as fb_err:
                    logger.warning(f"Candidate {cand_url} failed: {fb_err}")

            raise RuntimeError(f"Generation failed across all engines")


# ── Replicate Provider ───────────────────────────
class ReplicateProvider(AIProvider):
    name = "replicate"

    def __init__(self):
        self.api_token = settings.REPLICATE_API_TOKEN
        self.model = settings.REPLICATE_MODEL

    async def health_check(self) -> bool:
        if not self.api_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.replicate.com/v1/account",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        params: Dict[str, Any],
        on_progress: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> GenerationResult:
        if not self.api_token:
            raise ValueError("Replicate API token not configured")

        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        if on_progress:
            await on_progress("Submitting to Replicate...", 10)

        start_time = time.time()
        headers = {"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"}

        input_params = {
            "prompt": params.get("prompt", ""),
            "negative_prompt": params.get("negative_prompt", ""),
            "width": params.get("width", 1024),
            "height": params.get("height", 1024),
            "num_inference_steps": params.get("steps", 25),
            "guidance_scale": params.get("cfg_scale", 3.5),
            "seed": seed,
            "num_outputs": params.get("num_images", 1),
            "output_format": "png",
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"https://api.replicate.com/v1/models/{self.model}/predictions",
                headers=headers,
                json={"input": input_params},
            )
            resp.raise_for_status()
            prediction = resp.json()
            prediction_id = prediction["id"]
            poll_url = prediction.get("urls", {}).get("get", f"https://api.replicate.com/v1/predictions/{prediction_id}")

            if on_progress:
                await on_progress("Replicate prediction queued...", 15)

            while True:
                elapsed = time.time() - start_time
                if elapsed > 180:
                    raise TimeoutError("Replicate generation timed out")

                poll_resp = await client.get(poll_url, headers=headers)
                poll_resp.raise_for_status()
                prediction = poll_resp.json()
                status = prediction.get("status", "")

                if status == "succeeded":
                    if on_progress:
                        await on_progress("Processing output...", 90)

                    output = prediction.get("output", [])
                    if isinstance(output, list) and output:
                        img_url = output[0]
                        img_resp = await client.get(img_url)
                        img_resp.raise_for_status()

                        return GenerationResult(
                            image_bytes=img_resp.content,
                            seed_used=seed,
                            width=params.get("width", 1024),
                            height=params.get("height", 1024),
                            model=params.get("model", "replicate-flux"),
                            elapsed_seconds=round(time.time() - start_time, 2),
                            metadata={
                                "provider": "replicate",
                                "model": self.model,
                                "prediction_id": prediction_id,
                            },
                        )
                    raise RuntimeError("Replicate returned empty output")

                if status == "failed":
                    error = prediction.get("error", "Unknown error")
                    raise RuntimeError(f"Replicate failed: {error}")

                if status == "canceled":
                    raise RuntimeError("Replicate prediction was canceled")

                if on_progress:
                    logs = prediction.get("logs", "")
                    progress = min(85, 15 + int((elapsed / 180) * 70))
                    await on_progress(f"Generating on GPU... ({elapsed:.0f}s)", progress)

                await asyncio.sleep(2.0)


# ── Gemini Provider ──────────────────────────────
class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        
        # Clean model string from potential syntax wrapper copy-paste errors
        model_str = settings.GEMINI_MODEL or "gemini-2.5-flash-image"
        model_str = model_str.replace("model=", "").replace('"', '').replace("'", "").replace(",", "").strip()
        self.model = model_str

    async def health_check(self) -> bool:
        return bool(self.api_key)

    async def generate(
        self,
        params: Dict[str, Any],
        on_progress: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> GenerationResult:
        if not self.api_key:
            raise ValueError("Gemini API key not configured")

        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        if on_progress:
            await on_progress("Sending to Gemini...", 10)

        start_time = time.time()
        prompt = params.get("prompt", "")

        aspect_map = {
            (1024, 1024): "1:1",
            (1344, 768): "16:9",
            (768, 1344): "9:16",
            (1152, 896): "4:3",
            (896, 1152): "3:4",
            (1216, 832): "3:2",
            (832, 1216): "2:3",
        }
        aspect = aspect_map.get((params.get("width", 1024), params.get("height", 1024)), "1:1")

        body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect
                }
            }
        }

        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=180.0) as client:
            for attempt in range(5):
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                    headers=headers,
                    json=body,
                )

                if resp.status_code in (429, 500, 503):
                    if resp.status_code == 429:
                        try:
                            err_data = resp.json()
                            err_msg = err_data.get("error", {}).get("message", "")
                            err_status = err_data.get("error", {}).get("status", "")
                            if "quota" in err_msg.lower() or "quota" in err_status.lower() or err_status == "RESOURCE_EXHAUSTED":
                                raise RuntimeError(f"Gemini Quota Exceeded: {err_msg}")
                        except (ValueError, KeyError):
                            pass

                    wait = 30 if attempt < 4 else 60
                    if on_progress:
                        await on_progress(f"Gemini rate limit, retrying in {wait}s...", 15)
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()
                data = resp.json()

                candidates = data.get("candidates") or []
                if not candidates:
                    raise RuntimeError(f"Gemini returned no candidates: {data}")

                if on_progress:
                    await on_progress("Image received, processing...", 90)

                image_bytes = None
                for candidate in candidates:
                    content = candidate.get("content") or {}
                    parts = content.get("parts") or []
                    for part in parts:
                        inline_data = part.get("inlineData") or {}
                        raw = inline_data.get("data")
                        if raw:
                            import base64
                            image_bytes = base64.b64decode(raw)
                            break
                    if image_bytes:
                        break

                if not image_bytes:
                    raise RuntimeError(f"Gemini response missing image data: {data}")

                elapsed = time.time() - start_time
                return GenerationResult(
                    image_bytes=image_bytes,
                    seed_used=seed,
                    width=params.get("width", 1024),
                    height=params.get("height", 1024),
                    model=params.get("model", "gemini-imagen"),
                    elapsed_seconds=round(elapsed, 2),
                    metadata={"provider": "gemini", "model": self.model},
                )

        raise RuntimeError("Gemini: all retries exhausted")


# ── Placeholder / Dev Provider ───────────────────
class PlaceholderProvider(AIProvider):
    name = "placeholder"

    async def generate(
        self,
        params: Dict[str, Any],
        on_progress: Optional[Callable[[str, int], Awaitable[None]]] = None,
    ) -> GenerationResult:
        import urllib.parse
        from pathlib import Path
        import io
        from PIL import Image, ImageDraw, ImageFont

        prompt = params.get("prompt", "")
        w = params.get("width", 1024)
        h = params.get("height", 1024)
        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        # 1. If HF token exists in environment, generate real high quality image via FLUX.1 Schnell!
        hf_key = settings.HUGGINGFACE_API_KEY or settings.HF_TOKEN
        if hf_key:
            try:
                hf = HuggingFaceProvider()
                flux_params = params.copy()
                flux_params["model"] = "hf-flux"
                return await hf.generate(flux_params, on_progress=on_progress)
            except Exception:
                pass

        # 2. Attempt to generate unique image from prompt using Pollinations FLUX
        for pollinations_attempt in range(3):
            try:
                if on_progress:
                    await on_progress("Submitting to generation pipeline...", 20)

                clean_prompt = prompt.strip()
                if not clean_prompt:
                    clean_prompt = "a beautiful landscape"

                encoded_prompt = urllib.parse.quote(clean_prompt)
                url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&width={w}&height={h}&seed={seed}&nologo=true"

                if on_progress:
                    await on_progress("Generating unique image for your prompt...", 50)

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        if on_progress:
                            await on_progress("Processing generated output...", 90)

                        return GenerationResult(
                            image_bytes=resp.content,
                            seed_used=seed,
                            width=w,
                            height=h,
                            model=params.get("model", "demo"),
                            elapsed_seconds=3.0,
                            metadata={"provider": "placeholder", "source": "pollinations_flux"},
                        )
                    else:
                        if on_progress:
                            await on_progress(f"Generation attempt {pollinations_attempt + 1} failed, retrying...", 40)
                        await asyncio.sleep(2)
            except Exception:
                if on_progress:
                    await on_progress(f"Generation attempt {pollinations_attempt + 1} failed, retrying...", 40)
                await asyncio.sleep(2)

        # 3. High-speed turbo fallback if flux had network latency
        try:
            turbo_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=turbo&width={w}&height={h}&seed={seed}&nologo=true"
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(turbo_url, headers=headers)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    return GenerationResult(
                        image_bytes=resp.content,
                        seed_used=seed,
                        width=w,
                        height=h,
                        model=params.get("model", "demo"),
                        elapsed_seconds=1.5,
                        metadata={"provider": "placeholder", "source": "pollinations_turbo"},
                    )
        except Exception:
            pass

        if on_progress:
            await on_progress("Starting placeholder generation...", 20)

        await asyncio.sleep(1)

        if on_progress:
            await on_progress("Rendering placeholder...", 50)

        w = params.get("width", 1024)
        h = params.get("height", 1024)
        img = Image.new("RGB", (w, h), color=(24, 24, 30))
        draw = ImageDraw.Draw(img)

        gradient_steps = 60
        for y in range(h):
            ratio = y / h
            r = int(30 + ratio * 50)
            g = int(20 + ratio * 30)
            b = int(80 + ratio * 60)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except OSError:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        prompt = params.get("prompt", "No prompt")
        display_prompt = prompt[:60] + "..." if len(prompt) > 60 else prompt
        draw.text((w // 2, h // 2 - 40), display_prompt, fill=(200, 200, 220), font=font_large, anchor="mm")
        draw.text((w // 2, h // 2 + 20), f"Seed: {params.get('seed', -1)} | Steps: {params.get('steps', 30)}", fill=(140, 140, 160), font=font_small, anchor="mm")
        draw.text((w // 2, h // 2 + 50), "[ Placeholder — configure AI_PROVIDER ]", fill=(100, 100, 120), font=font_small, anchor="mm")

        if on_progress:
            await on_progress("Finalizing...", 90)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        seed = params.get("seed", -1)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)

        return GenerationResult(
            image_bytes=buf.getvalue(),
            seed_used=seed,
            width=w,
            height=h,
            model=params.get("model", "placeholder"),
            elapsed_seconds=1.0,
            metadata={"provider": "placeholder"},
        )


# ── Provider Factory ─────────────────────────────
def get_ai_provider(model: Optional[str] = None) -> AIProvider:
    if model and model in MODEL_REGISTRY:
        provider_name = MODEL_REGISTRY[model].get("provider", settings.AI_PROVIDER)
    else:
        provider_name = settings.AI_PROVIDER

    providers = {
        "comfyui": ComfyUIProvider,
        "huggingface": HuggingFaceProvider,
        "replicate": ReplicateProvider,
        "gemini": GeminiProvider,
        "placeholder": PlaceholderProvider,
    }

    hf_key = settings.HUGGINGFACE_API_KEY or settings.HF_TOKEN

    # If demo/placeholder is requested but a real HF key is available, prefer HuggingFace FLUX
    if provider_name == "placeholder" and hf_key:
        return HuggingFaceProvider()

    provider_class = providers.get(provider_name)
    if provider_class:
        instance = provider_class()
        if provider_name == "placeholder":
            return instance
        if provider_name in ("huggingface", "replicate", "gemini"):
            key = getattr(instance, "api_key", None) or getattr(instance, "api_token", None)
            if key:
                return instance
            # Key missing for requested cloud provider: if HF key is available, use it
            if hf_key:
                return HuggingFaceProvider()
            return PlaceholderProvider()
        if provider_name == "comfyui":
            import socket
            try:
                host = instance.base_url.replace("http://", "").replace("https://", "").rstrip("/")
                socket.create_connection((host, 8188), timeout=1.5).close()
                return instance
            except Exception:
                # ComfyUI offline: fallback to HuggingFace if key configured
                if hf_key:
                    return HuggingFaceProvider()
                return PlaceholderProvider()
        return instance

    if hf_key:
        return HuggingFaceProvider()
    return PlaceholderProvider()
