from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.schemas import (
    PromptEnhanceRequest, PromptEnhanceResponse, PromptHistoryResponse, PromptHistoryItem,
    PROMPT_ACTIONS,
)
from app.dependencies import get_current_user
from app.services.prompt_service import enhance_prompt, get_prompt_history

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.post("/enhance", response_model=PromptEnhanceResponse)
async def enhance(
    body: PromptEnhanceRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.action not in PROMPT_ACTIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {body.action}. Must be one of: {', '.join(PROMPT_ACTIONS)}",
        )

    result = await enhance_prompt(
        db=db,
        user_id=str(user.id),
        prompt=body.prompt,
        model_target=body.model_target,
        action=body.action,
    )

    return PromptEnhanceResponse(
        original=result["original"],
        enhanced=result.get("enhanced", result["original"]),
        negative=result.get("negative", ""),
        tips=result.get("tips", []),
        suggestions=result.get("suggestions"),
        is_safe=result.get("is_safe", True),
        safety_flags=result.get("safety_flags", []),
    )


@router.get("/history", response_model=PromptHistoryResponse)
async def history(
    action: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = await get_prompt_history(db, str(user.id), action=action, limit=limit)
    return PromptHistoryResponse(
        items=[PromptHistoryItem(**item) for item in items],
        total=len(items),
    )


@router.get("/templates")
async def prompt_templates():
    return {
        "categories": [
            {
                "name": "Portraits",
                "prompts": [
                    "Portrait of a [subject], [style] style, [lighting], [mood]",
                    "Close-up portrait with dramatic lighting, shallow depth of field",
                    "Environmental portrait in a [location], natural light, candid",
                ],
            },
            {
                "name": "Landscapes",
                "prompts": [
                    "Breathtaking [landscape] at [time of day], [weather], panoramic view",
                    "Aerial view of [location], golden hour, cinematic composition",
                    "Minimalist landscape with [element], soft pastel colors",
                ],
            },
            {
                "name": "Sci-Fi",
                "prompts": [
                    "Futuristic [subject] in a cyberpunk city, neon lights, rain",
                    "Space station orbiting [planet], volumetric lighting, detailed",
                    "Mecha robot in [environment], dynamic pose, detailed metal textures",
                ],
            },
            {
                "name": "Fantasy",
                "prompts": [
                    "Ethereal [creature] in a magical forest, glowing particles, mystical",
                    "Ancient castle on a floating island, dramatic clouds, epic scale",
                    "Dragon soaring over a medieval kingdom, golden sunset, detailed scales",
                ],
            },
            {
                "name": "Photography",
                "prompts": [
                    "Professional photo of [subject], 85mm lens, f/1.4, natural light",
                    "Street photography in [city], rainy night, reflections, cinematic",
                    "Macro photography of [object], extreme detail, studio lighting",
                ],
            },
            {
                "name": "Abstract",
                "prompts": [
                    "Abstract [concept] visualization, vibrant colors, flowing shapes",
                    "Geometric patterns inspired by [theme], metallic textures, 3D render",
                    "Fluid art with [color palette], organic shapes, high contrast",
                ],
            },
        ],
    }


@router.get("/negative-templates")
async def negative_prompt_templates():
    return {
        "universal": "blurry, low quality, watermark, text, logo, deformed, bad anatomy, extra limbs",
        "photorealistic": "cartoon, anime, drawing, painting, illustration, CGI, render, artificial",
        "anime": "photorealistic, 3d render, photograph, real life, uncanny valley",
        "no_people": "person, human, face, hands, fingers, body, skin",
        "clean": "noise, artifacts, jpeg artifacts, chromatic aberration, lens flare",
    }
