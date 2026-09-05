from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas import ImageResponse, ImageListResponse
from app.services.image_service import get_public_gallery

router = APIRouter(prefix="/api/gallery", tags=["gallery"])


@router.get("", response_model=ImageListResponse)
async def gallery(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, max_length=200),
    model: Optional[str] = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    images, total = await get_public_gallery(db, page, per_page, q=q, model_filter=model)
    return ImageListResponse(
        images=[ImageResponse.model_validate(img) for img in images],
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
    )
