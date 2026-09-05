from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.config import settings
from app.models import User
from app.schemas import (
    ImageResponse,
    ImageListResponse,
    ImageUpdateRequest,
    ImageShareResponse,
    SharedImageView,
    FavoriteToggleResponse,
)
from app.services.image_service import (
    get_user_images,
    get_image_by_id,
    get_image_tags,
    delete_image,
    update_image,
    toggle_favorite,
    get_user_favorites,
    search_user_images,
    get_favorited_image_ids,
    create_share,
    revoke_share,
    get_image_shares,
    get_user_shares,
    get_shared_image,
    get_user_image_stats,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/images", tags=["images"])


# ── List / Search ───────────────────────────────────
@router.get("", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, max_length=200),
    model: Optional[str] = Query(None, max_length=100),
    sampler: Optional[str] = Query(None, max_length=100),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    is_favorited: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    has_filters = any([q, model, sampler, date_from, date_to, is_favorited])

    if has_filters:
        images, total = await search_user_images(
            db,
            user_id=str(user.id),
            q=q,
            model_filter=model,
            sampler_filter=sampler,
            date_from=date_from,
            date_to=date_to,
            is_favorited=is_favorited,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            per_page=per_page,
        )
    else:
        images, total = await get_user_images(db, str(user.id), page, per_page)

    favorited_ids = await get_favorited_image_ids(db, str(user.id))

    image_responses = []
    for img in images:
        resp = ImageResponse.model_validate(img)
        resp.is_favorited = img.id in favorited_ids
        resp.tags = await get_image_tags(db, img.id)
        image_responses.append(resp)

    return ImageListResponse(
        images=image_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
    )


# ── Stats ───────────────────────────────────────────
@router.get("/stats")
async def image_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await get_user_image_stats(db, str(user.id))


# ── Single image ────────────────────────────────────
@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    image = await get_image_by_id(db, image_id)
    if not image or (image.user_id != user.id and not image.is_public):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    resp = ImageResponse.model_validate(image)
    resp.tags = await get_image_tags(db, image.id)
    return resp


# ── Update (toggle public) ─────────────────────────
@router.patch("/{image_id}", response_model=ImageResponse)
async def update_image_endpoint(
    image_id: str,
    body: ImageUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image = await get_image_by_id(db, image_id)
    if not image or image.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    await update_image(db, image, is_public=body.is_public)
    return ImageResponse.model_validate(image)


# ── Delete ──────────────────────────────────────────
@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_image(image_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    image = await get_image_by_id(db, image_id)
    if not image or image.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    await delete_image(db, image)


# ── Favorites ───────────────────────────────────────
@router.post("/{image_id}/favorite", response_model=FavoriteToggleResponse)
async def toggle_image_favorite(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image = await get_image_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    is_fav, count = await toggle_favorite(db, str(user.id), image_id)
    return FavoriteToggleResponse(is_favorited=is_fav, favorites_count=count)


@router.get("/user/favorites", response_model=ImageListResponse)
async def user_favorites(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    images, total = await get_user_favorites(db, str(user.id), page, per_page)
    favorited_ids = await get_favorited_image_ids(db, str(user.id))

    image_responses = []
    for img in images:
        resp = ImageResponse.model_validate(img)
        resp.is_favorited = img.id in favorited_ids
        resp.tags = await get_image_tags(db, img.id)
        image_responses.append(resp)

    return ImageListResponse(
        images=image_responses,
        total=total,
        page=page,
        per_page=per_page,
        has_next=(page * per_page) < total,
    )


# ── Shares ──────────────────────────────────────────
@router.post("/{image_id}/share", response_model=ImageShareResponse)
async def share_image(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image = await get_image_by_id(db, image_id)
    if not image or image.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    share = await create_share(db, str(user.id), image_id, settings.FRONTEND_URL)
    resp = ImageShareResponse.model_validate(share)
    resp.share_url = f"{settings.FRONTEND_URL}/shared/{share.share_token}"
    return resp


@router.delete("/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_share(
    share_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await revoke_share(db, share_id, str(user.id))
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share not found")


@router.get("/{image_id}/shares")
async def image_shares(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shares = await get_image_shares(db, image_id, str(user.id))
    return [
        ImageShareResponse(
            **{k: v for k, v in s.__dict__.items() if not k.startswith("_")},
            share_url=f"{settings.FRONTEND_URL}/shared/{s.share_token}",
        )
        for s in shares
    ]


@router.get("/user/shares")
async def user_shares(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    shares, total = await get_user_shares(db, str(user.id), page, per_page)
    return {
        "shares": [
            ImageShareResponse(
                **{k: v for k, v in s.__dict__.items() if not k.startswith("_")},
                share_url=f"{settings.FRONTEND_URL}/shared/{s.share_token}",
            )
            for s in shares
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
    }


# ── Public shared view (no auth required) ──────────
@router.get("/shared/{share_token}", response_model=SharedImageView)
async def view_shared_image(share_token: str, db: AsyncSession = Depends(get_db)):
    result = await get_shared_image(db, share_token)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Share link expired or not found")
    share, image = result
    from app.models import User as UserModel
    owner = (await db.execute(select(UserModel).where(UserModel.id == image.user_id))).scalar_one_or_none()
    resp = SharedImageView.model_validate(image)
    resp.shared_by = owner.name or owner.email if owner else None
    return resp
