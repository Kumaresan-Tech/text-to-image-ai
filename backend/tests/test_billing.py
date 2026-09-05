import pytest
from httpx import AsyncClient


class TestBillingPlans:
    async def test_list_plans(self, client: AsyncClient):
        response = await client.get("/api/billing/plans")
        assert response.status_code == 200
        plans = response.json()
        assert isinstance(plans, list)
        assert len(plans) >= 1

    async def test_get_plan(self, client: AsyncClient):
        response = await client.get("/api/billing/plans")
        if response.status_code == 200 and response.json():
            plan_id = response.json()[0].get("id")
            if plan_id:
                detail = await client.get(f"/api/billing/plans/{plan_id}")
                assert detail.status_code == 200


class TestBillingCredits:
    async def test_get_credits(self, client: AsyncClient, auth_headers, test_user):
        response = await client.get("/api/billing/credits", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "credits" in data
        assert data["credits"] == test_user.credits

    async def test_credits_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/billing/credits")
        assert response.status_code in [401, 403]


class TestBillingSubscription:
    async def test_get_subscription(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/billing/subscription", headers=auth_headers)
        assert response.status_code == 200

    async def test_subscription_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/billing/subscription")
        assert response.status_code in [401, 403]


class TestBillingTransactions:
    async def test_list_transactions(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/billing/transactions", headers=auth_headers)
        assert response.status_code == 200

    async def test_transactions_unauthenticated(self, client: AsyncClient):
        response = await client.get("/api/billing/transactions")
        assert response.status_code in [401, 403]


class TestBillingUsage:
    async def test_get_usage(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/billing/usage", headers=auth_headers)
        assert response.status_code == 200


class TestAddCredits:
    async def test_add_credits(self, client: AsyncClient, auth_headers, test_user):
        initial_credits = test_user.credits
        response = await client.post("/api/billing/credits/add", json={
            "amount": 50,
            "description": "Test credit addition",
        }, headers=auth_headers)
        assert response.status_code == 200


class TestCheckout:
    async def test_checkout_missing_plan(self, client: AsyncClient, auth_headers):
        response = await client.post("/api/billing/checkout", json={
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel",
        }, headers=auth_headers)
        assert response.status_code in [400, 422]
