import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import PromptHistory


# ── Safety Filter ────────────────────────────────
BLOCKED_TERMS = [
    "gore", "blood", "nude", "nsfw", "porn", "sexual",
    "child abuse", "self-harm", "violence", "terror",
    "weapon", "drug", "meth", "explosive",
]

SENSITIVE_TERMS = [
    "naked", "sexy", "violence", "blood", "weapon", "gun",
    "knife", "death", "kill", "murder", "corpse",
]

SAFETY_SYSTEM_PROMPT = """You are a content safety classifier for an AI image generation platform.

Analyze the user's prompt and return a JSON object with:
{
  "is_safe": true/false,
  "flags": ["list of specific concerns"],
  "reason": "brief explanation if unsafe"
}

Flag as unsafe:
- Explicit sexual content or nudity
- Graphic violence or gore
- Content depicting minors inappropriately
- Self-harm or suicide promotion
- Hate speech or discriminatory content
- Real person impersonation for malicious purposes

Do NOT flag:
- Artistic nudity in classical art style
- Mild fantasy violence (swords, battles)
- Dark but artistic themes
- Horror art (non-graphic)

Return ONLY the JSON object, no other text."""


def quick_safety_check(prompt: str) -> Dict[str, Any]:
    lower = prompt.lower()
    flags = []
    for term in BLOCKED_TERMS:
        if term in lower:
            flags.append(f"blocked:{term}")

    for term in SENSITIVE_TERMS:
        if term in lower:
            flags.append(f"sensitive:{term}")

    return {
        "is_safe": len(flags) == 0,
        "flags": flags,
        "needs_llm_check": len(flags) > 0,
    }


# ── LLM Client ──────────────────────────────────
class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    async def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if self.provider == "gemini" or (settings.GEMINI_API_KEY and not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY):
            return await self._gemini_chat(system_prompt, user_prompt, temperature)
        elif self.provider == "openai":
            return await self._openai_chat(system_prompt, user_prompt, temperature)
        elif self.provider == "anthropic":
            return await self._anthropic_chat(system_prompt, user_prompt, temperature)
        else:
            if settings.GEMINI_API_KEY:
                return await self._gemini_chat(system_prompt, user_prompt, temperature)
            return await self._openai_chat(system_prompt, user_prompt, temperature)

    async def _gemini_chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY.")

        model = getattr(settings, "GEMINI_LLM_MODEL", "gemini-3.6-flash") or "gemini-3.6-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

        headers = {
            "x-goog-api-key": settings.GEMINI_API_KEY,
            "Content-Type": "application/json",
        }

        body = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1000,
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            return ""

    async def _openai_chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": 1000,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _anthropic_chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not configured. Set ANTHROPIC_API_KEY.")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": 1000,
                    "temperature": temperature,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]


llm = LLMClient()


# ── Enhancement Templates ────────────────────────
ENHANCE_SYSTEM_PROMPT = """You are an expert AI image prompt engineer. Your job is to improve user prompts for text-to-image AI models like Stable Diffusion XL and FLUX.

Rules:
- Enhance the prompt with specific artistic details: lighting, composition, style, camera angle, mood
- Add quality modifiers: "masterpiece", "best quality", "highly detailed", "8k", "sharp focus"
- Keep the original creative intent
- Make the prompt more vivid and descriptive
- Add relevant art style keywords when appropriate
- Keep it under 400 words
- Do NOT change the subject/scene, only enhance it
- Do NOT add any harmful content

Return ONLY the enhanced prompt text, nothing else."""

OPTIMIZE_SD_SYSTEM = """You are a Stable Diffusion prompt optimizer. Transform the user's prompt into an optimal SD XL format.

SD prompt structure: [Subject] [Medium] [Style] [Artist reference] [Quality tags] [Lighting] [Color] [Composition]

Quality tags to include: masterpiece, best quality, highly detailed, sharp focus, 8k uhd
Negative terms to suggest: blurry, low quality, watermark, text, deformed, bad anatomy

Return a JSON object:
{
  "enhanced_prompt": "the optimized prompt",
  "negative_prompt": "suggested negative prompt",
  "tips": ["brief optimization tips applied"]
}"""

OPTIMIZE_FLUX_SYSTEM = """You are a FLUX.1 prompt optimizer. FLUX works best with natural, descriptive language rather than keyword stuffing.

Rules:
- Write in natural sentences, not comma-separated tags
- Be specific and descriptive about visual elements
- Describe lighting, atmosphere, and mood naturally
- Include camera/lens details when relevant
- Avoid keyword lists; write descriptive phrases
- FLUX handles text well — mention any text that should appear

Return a JSON object:
{
  "enhanced_prompt": "the optimized prompt",
  "negative_prompt": "suggested negative prompt",
  "tips": ["brief optimization tips applied"]
}"""

NEGATIVE_PROMPT_SYSTEM = """You are a negative prompt generator for AI image generation. Given a positive prompt, generate an effective negative prompt.

Rules:
- Include common artifacts: blurry, low quality, watermark, text, logo
- Add model-specific negatives: bad anatomy, deformed, disfigured, extra limbs
- Add style-specific negatives based on the prompt content
- Keep it concise but comprehensive (under 200 words)
- Separate terms with commas

Return ONLY the negative prompt text, nothing else."""

SUGGEST_SYSTEM = """You are a creative prompt idea generator for AI text-to-image models. Generate 5 diverse, creative prompt ideas based on the user's interest or theme.

Each prompt should be:
- Detailed and specific (2-4 sentences)
- Visually interesting and varied
- Covering different styles (photorealistic, anime, oil painting, digital art, etc.)
- Include lighting, composition, and mood details

Return a JSON array of 5 strings, each being a complete prompt. Nothing else."""


# ── Core Enhancement Functions ───────────────────
async def enhance_prompt(
    db: AsyncSession,
    user_id: str,
    prompt: str,
    model_target: str = "sdxl-1.0",
    action: str = "enhance",
) -> Dict[str, Any]:
    result = {"original": prompt, "enhanced": prompt, "negative": "", "tips": [], "is_safe": True, "safety_flags": []}

    safety = quick_safety_check(prompt)
    result["is_safe"] = safety["is_safe"]
    result["safety_flags"] = safety["flags"]

    if action == "safety_check" or safety.get("needs_llm_check"):
        try:
            safety_resp = await llm.chat(SAFETY_SYSTEM_PROMPT, prompt, temperature=0.1)
            safety_data = _parse_json(safety_resp)
            if safety_data:
                result["is_safe"] = safety_data.get("is_safe", True)
                result["safety_flags"] = safety_data.get("flags", [])
        except Exception:
            pass

    if action == "safety_check":
        _save_history(db, user_id, prompt, None, None, "safety_check", model_target, result["is_safe"], result["safety_flags"])
        return result

    try:
        if action == "optimize":
            system = OPTIMIZE_SD_SYSTEM if "flux" not in model_target.lower() else OPTIMIZE_FLUX_SYSTEM
            resp = await llm.chat(system, prompt, temperature=0.7)
            data = _parse_json(resp)
            if data:
                result["enhanced"] = data.get("enhanced_prompt", prompt)
                result["negative"] = data.get("negative_prompt", "")
                result["tips"] = data.get("tips", [])
        elif action == "negative":
            neg = await llm.chat(NEGATIVE_PROMPT_SYSTEM, prompt, temperature=0.5)
            result["negative"] = neg.strip().strip('"')
        elif action == "suggest":
            resp = await llm.chat(SUGGEST_SYSTEM, prompt, temperature=0.9)
            suggestions = _parse_json(resp)
            if isinstance(suggestions, list):
                result["suggestions"] = suggestions
        else:
            resp = await llm.chat(ENHANCE_SYSTEM_PROMPT, prompt, temperature=0.7)
            result["enhanced"] = resp.strip().strip('"')

    except ValueError:
        result["enhanced"] = _rule_based_enhance(prompt)
        result["tips"] = ["Used rule-based enhancement (LLM not configured)"]
    except Exception as e:
        result["enhanced"] = _rule_based_enhance(prompt)
        result["tips"] = [f"LLM error: {str(e)[:100]}", "Used rule-based fallback"]

    _save_history(db, user_id, prompt, result.get("enhanced"), result.get("negative"), action, model_target, result["is_safe"], result["safety_flags"])
    return result


async def get_prompt_history(
    db: AsyncSession,
    user_id: str,
    action: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    q = select(PromptHistory).where(PromptHistory.user_id == user_id)
    if action:
        q = q.where(PromptHistory.action == action)
    q = q.order_by(desc(PromptHistory.created_at)).limit(limit)
    result = await db.execute(q)
    records = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "original_prompt": r.original_prompt,
            "enhanced_prompt": r.enhanced_prompt,
            "negative_prompt": r.negative_prompt,
            "action": r.action,
            "model_target": r.model_target,
            "is_safe": r.is_safe,
            "used": r.used,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


async def mark_prompt_used(db: AsyncSession, history_id: str) -> None:
    result = await db.execute(select(PromptHistory).where(PromptHistory.id == history_id))
    record = result.scalar_one_or_none()
    if record:
        record.used = True
        await db.flush()


# ── Helpers ──────────────────────────────────────
def _parse_json(text: str) -> Optional[Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def _rule_based_enhance(prompt: str) -> str:
    quality_tags = [
        "masterpiece", "best quality", "highly detailed",
        "sharp focus", "8k uhd", "photorealistic",
    ]
    style_tags = ["professional photography", "cinematic lighting", "volumetric lighting"]

    enhanced = prompt.rstrip(".")
    existing = set(enhanced.lower().split())

    additions = []
    for tag in quality_tags:
        if tag.split()[0] not in existing:
            additions.append(tag)
    if not any(t in existing for t in ["lighting", "light", "cinematic"]):
        additions.append("cinematic lighting")

    if additions:
        enhanced = f"{enhanced}, {', '.join(additions[:4])}"

    return enhanced


def _save_history(
    db: AsyncSession,
    user_id: str,
    original: str,
    enhanced: Optional[str],
    negative: Optional[str],
    action: str,
    model_target: str,
    is_safe: bool,
    safety_flags: List[str],
) -> None:
    record = PromptHistory(
        user_id=user_id,
        original_prompt=original[:2000],
        enhanced_prompt=enhanced[:2000] if enhanced else None,
        negative_prompt=negative[:2000] if negative else None,
        action=action,
        model_target=model_target,
        is_safe=is_safe,
        safety_flags=safety_flags if safety_flags else None,
    )
    db.add(record)
