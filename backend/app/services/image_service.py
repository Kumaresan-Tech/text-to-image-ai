import secrets
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, desc, asc, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Image, ImageTag, ImageFavorite, ImageShare, User

DEFAULT_FRONTEND_URL = "http://localhost:3000"


# ── Create ───────────────────────────────────────────
async def create_image(
    db: AsyncSession,
    user_id: str,
    prompt: str,
    image_url: str,
    negative_prompt: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg_scale: float = 7.5,
    sampler: str = "DPM++ 2M Karras",
    seed: Optional[int] = None,
    model: str = "sdxl-1.0",
    is_public: bool = False,
    tags: Optional[List[str]] = None,
) -> Image:
    image = Image(
        user_id=user_id,
        prompt=prompt,
        negative_prompt=negative_prompt,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        width=width,
        height=height,
        steps=steps,
        cfg_scale=cfg_scale,
        sampler=sampler,
        seed=seed,
        model=model,
        is_public=is_public,
    )
    db.add(image)
    await db.flush()

    if tags:
        for tag in tags:
            db.add(ImageTag(image_id=image.id, tag=tag.lower().strip()))
        await db.flush()

    return image


# ── Read: single ─────────────────────────────────────
async def get_image_by_id(db: AsyncSession, image_id: str) -> Optional[Image]:
    result = await db.execute(select(Image).where(Image.id == image_id))
    return result.scalar_one_or_none()


async def get_image_tags(db: AsyncSession, image_id: str) -> List[str]:
    result = await db.execute(
        select(ImageTag.tag).where(ImageTag.image_id == image_id)
    )
    return [row[0] for row in result.all()]


# ── Read: user images ───────────────────────────────
async def get_user_images(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Image], int]:
    count_q = select(func.count()).select_from(Image).where(Image.user_id == user_id)
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(Image)
        .where(Image.user_id == user_id)
        .order_by(desc(Image.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


# ── Read: public gallery ────────────────────────────
async def get_public_gallery(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    q: Optional[str] = None,
    model_filter: Optional[str] = None,
) -> Tuple[List[Image], int]:
    conditions = [Image.is_public == True]

    if q:
        conditions.append(Image.prompt.ilike(f"%{q}%"))
    if model_filter:
        conditions.append(Image.model == model_filter)

    where = and_(*conditions)

    count_q = select(func.count()).select_from(Image).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Image)
        .where(where)
        .order_by(desc(Image.likes_count), desc(Image.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


# ── Read: shared view ───────────────────────────────
async def get_shared_image(db: AsyncSession, share_token: str) -> Optional[Tuple[ImageShare, Image]]:
    result = await db.execute(
        select(ImageShare, Image)
        .join(Image, ImageShare.image_id == Image.id)
        .where(
            ImageShare.share_token == share_token,
            ImageShare.is_active == True,
        )
    )
    row = result.first()
    if row:
        share, image = row
        share.view_count += 1
        await db.flush()
        return share, image
    return None


# ── Search / filter ─────────────────────────────────
async def search_user_images(
    db: AsyncSession,
    user_id: str,
    q: Optional[str] = None,
    model_filter: Optional[str] = None,
    sampler_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    is_favorited: Optional[bool] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Image], int]:
    conditions = [Image.user_id == user_id]

    if q:
        conditions.append(
            or_(
                Image.prompt.ilike(f"%{q}%"),
                Image.model.ilike(f"%{q}%"),
                Image.sampler.ilike(f"%{q}%"),
            )
        )
    if model_filter:
        conditions.append(Image.model == model_filter)
    if sampler_filter:
        Image.sampler == sampler_filter
        conditions.append(Image.sampler == sampler_filter)
    if date_from:
        conditions.append(Image.created_at >= date_from)
    if date_to:
        conditions.append(Image.created_at <= date_to)
    if is_favorited:
        favorited_subq = (
            select(ImageFavorite.image_id)
            .where(ImageFavorite.user_id == user_id)
            .correlate(Image)
            .exists()
        )
        conditions.append(favorited_subq)

    where = and_(*conditions)

    count_q = select(func.count()).select_from(Image).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    order_col = {
        "created_at": Image.created_at,
        "likes_count": Image.likes_count,
        "model": Image.model,
        "prompt": Image.prompt,
    }.get(sort_by, Image.created_at)

    order_fn = desc if sort_order == "desc" else asc

    query = (
        select(Image)
        .where(where)
        .order_by(order_fn(order_col))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def get_favorited_image_ids(db: AsyncSession, user_id: str) -> set:
    result = await db.execute(
        select(ImageFavorite.image_id).where(ImageFavorite.user_id == user_id)
    )
    return {row[0] for row in result.all()}


# ── Update ──────────────────────────────────────────
async def update_image(db: AsyncSession, image: Image, **kwargs) -> Image:
    for key, value in kwargs.items():
        if hasattr(image, key) and value is not None:
            setattr(image, key, value)
    await db.flush()
    return image


# ── Delete ──────────────────────────────────────────
async def delete_image(db: AsyncSession, image: Image) -> None:
    await db.delete(image)
    await db.flush()


# ── Tags ────────────────────────────────────────────
async def add_tags(db: AsyncSession, image_id: str, tags: List[str]) -> None:
    for tag in tags:
        db.add(ImageTag(image_id=image_id, tag=tag.lower().strip()))
    await db.flush()


async def remove_tag(db: AsyncSession, image_id: str, tag: str) -> None:
    result = await db.execute(
        select(ImageTag).where(
            ImageTag.image_id == image_id,
            ImageTag.tag == tag.lower().strip(),
        )
    )
    tag_obj = result.scalar_one_or_none()
    if tag_obj:
        await db.delete(tag_obj)
        await db.flush()


async def get_tags(db: AsyncSession, image_id: str) -> List[str]:
    result = await db.execute(
        select(ImageTag.tag).where(ImageTag.image_id == image_id)
    )
    return [row[0] for row in result.all()]


# ── Favorites ───────────────────────────────────────
async def toggle_favorite(db: AsyncSession, user_id: str, image_id: str) -> Tuple[bool, int]:
    result = await db.execute(
        select(ImageFavorite).where(
            ImageFavorite.user_id == user_id,
            ImageFavorite.image_id == image_id,
        )
    )
    fav = result.scalar_one_or_none()

    if fav:
        await db.delete(fav)
        await db.flush()
        is_fav = False
    else:
        db.add(ImageFavorite(user_id=user_id, image_id=image_id))
        await db.flush()
        is_fav = True

    count_result = await db.execute(
        select(func.count()).select_from(ImageFavorite).where(ImageFavorite.image_id == image_id)
    )
    count = (count_result.scalar() or 0)

    return is_fav, count


async def get_user_favorites(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[Image], int]:
    fav_subq = select(ImageFavorite.image_id).where(ImageFavorite.user_id == user_id).subquery()

    count_q = (
        select(func.count())
        .select_from(Image)
        .join(fav_subq, Image.id == fav_subq.c.image_id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(Image)
        .join(fav_subq, Image.id == fav_subq.c.image_id)
        .order_by(desc(Image.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


# ── Shares ──────────────────────────────────────────
async def create_share(db: AsyncSession, user_id: str, image_id: str, frontend_url: str = DEFAULT_FRONTEND_URL) -> ImageShare:
    existing = await db.execute(
        select(ImageShare).where(
            ImageShare.image_id == image_id,
            ImageShare.shared_by == user_id,
            ImageShare.is_active == True,
        )
    )
    existing_share = existing.scalar_one_or_none()
    if existing_share:
        existing_share.share_token = secrets.token_urlsafe(32)
        await db.flush()
        return existing_share

    token = secrets.token_urlsafe(32)
    share = ImageShare(
        image_id=image_id,
        shared_by=user_id,
        share_token=token,
    )
    db.add(share)
    await db.flush()
    return share


async def revoke_share(db: AsyncSession, share_id: str, user_id: str) -> bool:
    result = await db.execute(
        select(ImageShare).where(
            ImageShare.id == share_id,
            ImageShare.shared_by == user_id,
        )
    )
    share = result.scalar_one_or_none()
    if not share:
        return False
    share.is_active = False
    await db.flush()
    return True


async def get_image_shares(db: AsyncSession, image_id: str, user_id: str) -> List[ImageShare]:
    result = await db.execute(
        select(ImageShare).where(
            ImageShare.image_id == image_id,
            ImageShare.shared_by == user_id,
        ).order_by(desc(ImageShare.created_at))
    )
    return list(result.scalars().all())


async def get_user_shares(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[ImageShare], int]:
    count_q = (
        select(func.count())
        .select_from(ImageShare)
        .where(ImageShare.shared_by == user_id, ImageShare.is_active == True)
    )
    total = (await db.execute(count_q)).scalar() or 0

    q = (
        select(ImageShare)
        .where(ImageShare.shared_by == user_id, ImageShare.is_active == True)
        .order_by(desc(ImageShare.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(q)
    return list(result.scalars().all()), total


# ── Stats ───────────────────────────────────────────
async def get_user_image_stats(db: AsyncSession, user_id: str) -> dict:
    total_q = select(func.count()).select_from(Image).where(Image.user_id == user_id)
    total = (await db.execute(total_q)).scalar() or 0

    fav_q = (
        select(func.count())
        .select_from(ImageFavorite)
        .where(ImageFavorite.user_id == user_id)
    )
    favorites = (await db.execute(fav_q)).scalar() or 0

    public_q = (
        select(func.count())
        .select_from(Image)
        .where(Image.user_id == user_id, Image.is_public == True)
    )
    public = (await db.execute(public_q)).scalar() or 0

    share_q = (
        select(func.count())
        .select_from(ImageShare)
        .where(ImageShare.shared_by == user_id, ImageShare.is_active == True)
    )
    shares = (await db.execute(share_q)).scalar() or 0

    return {
        "total_images": total,
        "total_favorites": favorites,
        "total_public": public,
        "total_shares": shares,
    }
