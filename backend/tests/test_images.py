import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Image, User


async def create_test_image(db: AsyncSession, user_id: str, **kwargs) -> Image:
    defaults = {
        "prompt": "a beautiful sunset over mountains",
        "negative_prompt": "blurry, low quality",
        "model": "stable-diffusion-xl",
        "width": 1024,
        "height": 1024,
        "image_url": "https://storage.example.com/test.png",
        "thumbnail_url": "https://storage.example.com/thumb.png",
        "seed": 42,
        "steps": 30,
        "cfg_scale": 7.5,
        "sampler": "euler_a",
        "is_public": True,
        "likes_count": 0,
    }
    defaults.update(kwargs)
    img = Image(id=str(uuid.uuid4()), user_id=user_id, **defaults)
    db.add(img)
    await db.commit()
    return img


class TestListImages:
    async def test_list_images_authenticated(self, client: AsyncClient, auth_headers, db_session, test_user):
        await create_test_image(db_session, str(test_user.id))
        await db_session.commit()

        response = await client.get("/api/images", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert "total" in data
        assert data["total"] >= 1

    async def test_list_images_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/images")
        assert response.status_code in [401, 403]

    async def test_list_images_with_search(self, client: AsyncClient, auth_headers, db_session, test_user):
        await create_test_image(db_session, str(test_user.id), prompt="cat sitting on a couch")
        await create_test_image(db_session, str(test_user.id), prompt="dog running in park")
        await db_session.commit()

        response = await client.get("/api/images?search=cat", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    async def test_list_images_pagination(self, client: AsyncClient, auth_headers, db_session, test_user):
        for i in range(5):
            await create_test_image(db_session, str(test_user.id), prompt=f"image {i}")
        await db_session.commit()

        response = await client.get("/api/images?page=1&per_page=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["images"]) <= 2
        assert data["total"] >= 5


class TestGetImage:
    async def test_get_image_success(self, client: AsyncClient, auth_headers, db_session, test_user):
        img = await create_test_image(db_session, str(test_user.id))
        await db_session.commit()

        response = await client.get(f"/api/images/{img.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["prompt"] == img.prompt

    async def test_get_image_not_found(self, client: AsyncClient, auth_headers):
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/images/{fake_id}", headers=auth_headers)
        assert response.status_code == 404


class TestDeleteImage:
    async def test_delete_own_image(self, client: AsyncClient, auth_headers, db_session, test_user):
        img = await create_test_image(db_session, str(test_user.id))
        await db_session.commit()

        response = await client.delete(f"/api/images/{img.id}", headers=auth_headers)
        assert response.status_code in [200, 204]

    async def test_delete_other_user_image(self, client: AsyncClient, auth_headers, db_session):
        other_user = User(
            id=str(uuid.uuid4()),
            email="other@example.com",
            hashed_password="x" * 60,
            credits=50,
            plan="FREE",
            role="user",
            is_active=True,
            is_banned=False,
        )
        db_session.add(other_user)
        await db_session.flush()

        img = await create_test_image(db_session, str(other_user.id))
        await db_session.commit()

        response = await client.delete(f"/api/images/{img.id}", headers=auth_headers)
        assert response.status_code in [403, 404]


class TestImageFavorite:
    async def test_favorite_image(self, client: AsyncClient, auth_headers, db_session, test_user):
        img = await create_test_image(db_session, str(test_user.id))
        await db_session.commit()

        response = await client.post(f"/api/images/{img.id}/favorite", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "is_favorited" in data
        assert data["is_favorited"] is True
        assert data["favorites_count"] >= 1

    async def test_unfavorite_image(self, client: AsyncClient, auth_headers, db_session, test_user):
        img = await create_test_image(db_session, str(test_user.id))
        await db_session.commit()

        await client.post(f"/api/images/{img.id}/favorite", headers=auth_headers)
        response = await client.post(f"/api/images/{img.id}/favorite", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["is_favorited"] is False


class TestImageShare:
    async def test_create_share_link(self, client: AsyncClient, auth_headers, db_session, test_user):
        img = await create_test_image(db_session, str(test_user.id))
        await db_session.commit()

        response = await client.post(f"/api/images/{img.id}/share", headers=auth_headers)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "share_token" in data or "token" in data


class TestImageStats:
    async def test_get_stats(self, client: AsyncClient, auth_headers, db_session, test_user):
        await create_test_image(db_session, str(test_user.id))
        await create_test_image(db_session, str(test_user.id), is_public=False)
        await db_session.commit()

        response = await client.get("/api/images/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_images" in data or "total" in data
