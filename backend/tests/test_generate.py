import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient


class TestSubmitGeneration:
    async def test_submit_generation_success(self, client: AsyncClient, auth_headers):
        mock_tx = MagicMock()
        mock_tx.balance_after = 99
        with patch("app.routes.generate.deduct_credits", new_callable=AsyncMock, return_value=mock_tx), \
             patch("app.routes.generate.generate_image_task") as mock_task:

            response = await client.post("/api/generate", json={
                "prompt": "a beautiful sunset",
                "model": "sdxl-1.0",
                "width": 1024,
                "height": 1024,
                "steps": 30,
                "cfg_scale": 7.5,
                "sampler": "Euler a",
            }, headers=auth_headers)

            assert response.status_code == 201
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "PENDING"
            mock_task.delay.assert_called_once()

    async def test_submit_generation_empty_prompt(self, client: AsyncClient, auth_headers):
        response = await client.post("/api/generate", json={
            "prompt": "",
            "model": "sdxl-1.0",
        }, headers=auth_headers)
        assert response.status_code in [400, 422]

    async def test_submit_generation_unauthenticated(self, client: AsyncClient):
        response = await client.post("/api/generate", json={
            "prompt": "test",
            "model": "sdxl-1.0",
        })
        assert response.status_code in [401, 403]

    async def test_submit_generation_insufficient_credits(self, client: AsyncClient, auth_headers):
        with patch("app.routes.generate.deduct_credits", new_callable=AsyncMock, side_effect=ValueError("Insufficient credits")):
            response = await client.post("/api/generate", json={
                "prompt": "a beautiful sunset",
                "model": "sdxl-1.0",
            }, headers=auth_headers)
            assert response.status_code == 402


class TestModelsAndSamplers:
    async def test_list_models(self, client: AsyncClient):
        response = await client.get("/api/generate/models")
        assert response.status_code == 200
        models = response.json()
        assert isinstance(models, list)
        assert len(models) > 0
        assert any(m.get("id") or m.get("name") for m in models)

    async def test_list_samplers(self, client: AsyncClient):
        response = await client.get("/api/generate/samplers")
        assert response.status_code == 200
        data = response.json()
        assert "samplers" in data
        assert len(data["samplers"]) > 0


class TestCancelGeneration:
    async def test_cancel_nonexistent_job(self, client: AsyncClient, auth_headers):
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/generate/{fake_id}", headers=auth_headers)
        assert response.status_code in [404, 400]
