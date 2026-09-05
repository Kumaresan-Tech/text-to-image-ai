import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


class TestPromptEnhance:
    async def test_enhance_prompt(self, client: AsyncClient, auth_headers):
        with patch("app.routes.prompt.enhance_prompt") as mock_enhance:
            mock_enhance.return_value = {
                "original": "a cat",
                "enhanced": "a fluffy orange cat sitting on a windowsill",
                "negative": "blurry, low quality",
                "tips": ["Add more detail", "Specify lighting"],
                "is_safe": True,
                "safety_flags": [],
            }

            response = await client.post("/api/prompts/enhance", json={
                "prompt": "a cat",
                "action": "enhance",
            }, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "enhanced" in data
            assert "negative" in data

    async def test_enhance_empty_prompt(self, client: AsyncClient, auth_headers):
        response = await client.post("/api/prompts/enhance", json={
            "prompt": "",
            "action": "enhance",
        }, headers=auth_headers)
        assert response.status_code in [400, 422]

    async def test_enhance_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/prompts/enhance", json={
            "prompt": "test",
            "action": "enhance",
        })
        assert response.status_code in [401, 403]

    async def test_optimize_prompt(self, client: AsyncClient, auth_headers):
        with patch("app.routes.prompt.enhance_prompt") as mock_enhance:
            mock_enhance.return_value = {
                "original": "a sunset",
                "enhanced": "a cinematic sunset with dramatic cloud formations",
                "negative": "",
                "tips": [],
                "is_safe": True,
                "safety_flags": [],
            }

            response = await client.post("/api/prompts/enhance", json={
                "prompt": "a sunset",
                "action": "optimize",
            }, headers=auth_headers)
            assert response.status_code == 200


class TestPromptHistory:
    async def test_get_history(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/prompts/history", headers=auth_headers)
        assert response.status_code == 200

    async def test_get_history_with_action_filter(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/prompts/history?action=enhance", headers=auth_headers)
        assert response.status_code == 200


class TestPromptTemplates:
    async def test_get_templates(self, client: AsyncClient):
        response = await client.get("/api/prompts/templates")
        assert response.status_code == 200

    async def test_get_negative_templates(self, client: AsyncClient):
        response = await client.get("/api/prompts/negative-templates")
        assert response.status_code == 200
