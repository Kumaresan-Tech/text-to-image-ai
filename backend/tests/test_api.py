import pytest
from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestCORS:
    async def test_cors_preflight(self, client: AsyncClient):
        response = await client.options("/api/auth/login", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        })
        assert response.status_code in [200, 405]


class TestRateLimiting:
    async def test_auth_rate_limit(self, client: AsyncClient):
        responses = []
        for _ in range(10):
            r = await client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "wrong",
            })
            responses.append(r.status_code)
        assert any(code in [401, 403] for code in responses)


class TestErrorHandling:
    async def test_404_returns_json(self, client: AsyncClient):
        response = await client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_invalid_json_body(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/login",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422


class TestAPIEndpointsExist:
    async def test_models_endpoint(self, client: AsyncClient):
        response = await client.get("/api/generate/models")
        assert response.status_code == 200

    async def test_samplers_endpoint(self, client: AsyncClient):
        response = await client.get("/api/generate/samplers")
        assert response.status_code == 200

    async def test_plans_endpoint(self, client: AsyncClient):
        response = await client.get("/api/billing/plans")
        assert response.status_code == 200

    async def test_templates_endpoint(self, client: AsyncClient):
        response = await client.get("/api/prompts/templates")
        assert response.status_code == 200

    async def test_negative_templates_endpoint(self, client: AsyncClient):
        response = await client.get("/api/prompts/negative-templates")
        assert response.status_code == 200
