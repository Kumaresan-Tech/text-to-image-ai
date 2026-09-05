import pytest
from httpx import AsyncClient


class TestAdminStats:
    async def test_get_stats_as_admin(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "images" in data
        assert "jobs" in data

    async def test_stats_requires_admin(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    async def test_stats_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/admin/stats")
        assert response.status_code in [401, 403]


class TestAdminHealth:
    async def test_get_health(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/admin/health", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "database" in data


class TestAdminUsers:
    async def test_list_users(self, client: AsyncClient, admin_headers, test_user):
        response = await client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert data["total"] >= 1

    async def test_list_users_with_search(self, client: AsyncClient, admin_headers, test_user):
        response = await client.get(
            f"/api/admin/users?q={test_user.email[:5]}", headers=admin_headers
        )
        assert response.status_code == 200

    async def test_list_users_requires_admin(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/admin/users", headers=auth_headers)
        assert response.status_code == 403

    async def test_get_user_detail(self, client: AsyncClient, admin_headers, test_user):
        response = await client.get(
            f"/api/admin/users/{test_user.id}", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert "images_count" in data

    async def test_set_user_credits(self, client: AsyncClient, admin_headers, test_user):
        response = await client.put(
            f"/api/admin/users/{test_user.id}/credits",
            json={"credits": 500},
            headers=admin_headers,
        )
        assert response.status_code == 200

    async def test_set_user_role(self, client: AsyncClient, admin_headers, test_user):
        response = await client.put(
            f"/api/admin/users/{test_user.id}/role",
            json={"role": "admin"},
            headers=admin_headers,
        )
        assert response.status_code == 200

    async def test_set_invalid_role(self, client: AsyncClient, admin_headers, test_user):
        response = await client.put(
            f"/api/admin/users/{test_user.id}/role",
            json={"role": "superadmin"},
            headers=admin_headers,
        )
        assert response.status_code in [400, 422]


class TestAdminImages:
    async def test_list_images(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/admin/images", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "images" in data


class TestAdminAuditLogs:
    async def test_list_audit_logs(self, client: AsyncClient, admin_headers):
        response = await client.get("/api/admin/audit-logs", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data


class TestAdminPromptAnalytics:
    async def test_prompt_analytics(self, client: AsyncClient, admin_headers):
        response = await client.get(
            "/api/admin/prompts/analytics?days=30", headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_prompts" in data
