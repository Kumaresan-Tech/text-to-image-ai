import pytest
from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "StrongPass123!",
            "name": "New User",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@example.com"
        assert data["user"]["name"] == "New User"
        assert data["user"]["credits"] >= 0
        assert data["user"]["role"] == "user"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post("/api/auth/register", json={
            "email": test_user.email,
            "password": "StrongPass123!",
            "name": "Duplicate",
        })
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "StrongPass123!",
        })
        assert response.status_code in [400, 422]

    async def test_register_weak_password(self, client: AsyncClient):
        response = await client.post("/api/auth/register", json={
            "email": "weak@example.com",
            "password": "123",
        })
        assert response.status_code in [400, 422]


class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user):
        response = await client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "TestPass123!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["id"] == str(test_user.id)

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "WrongPassword!",
        })
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        response = await client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "Whatever123!",
        })
        assert response.status_code == 401

    async def test_login_banned_user(self, client: AsyncClient, db_session):
        from app.models import User
        from app.services.auth_service import hash_password

        user = User(
            email="banned@example.com",
            hashed_password=hash_password("BannedPass123!"),
            name="Banned User",
            credits=50,
            plan="FREE",
            role="user",
            is_active=False,
            is_banned=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post("/api/auth/login", json={
            "email": "banned@example.com",
            "password": "BannedPass123!",
        })
        assert response.status_code == 403


class TestMe:
    async def test_get_me_authenticated(self, client: AsyncClient, auth_headers, test_user):
        response = await client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/auth/me")
        assert response.status_code in [401, 403]

    async def test_get_me_invalid_token(self, client: AsyncClient):
        response = await client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid_token_12345"
        })
        assert response.status_code == 401


class TestUpdateProfile:
    async def test_update_name(self, client: AsyncClient, auth_headers):
        response = await client.patch("/api/auth/me", json={
            "name": "Updated Name"
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_update_unauthenticated(self, client: AsyncClient):
        response = await client.patch("/api/auth/me", json={"name": "X"})
        assert response.status_code in [401, 403]
