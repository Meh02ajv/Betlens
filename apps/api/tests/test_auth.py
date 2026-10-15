"""
Integration tests for the auth module.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
class TestAuthEndpoints:
    async def test_signup_success(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/signup", json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "New User",
            "is_adult_confirmed": True,
        })
        assert response.status_code == 201
        assert "message" in response.json()

    async def test_signup_duplicate_email(self, client: AsyncClient) -> None:
        data = {
            "email": "duplicate@example.com",
            "password": "securepassword123",
            "name": "User",
            "is_adult_confirmed": True,
        }
        await client.post("/api/v1/auth/signup", json=data)
        response = await client.post("/api/v1/auth/signup", json=data)
        assert response.status_code == 409

    async def test_signup_underage_rejected(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/signup", json={
            "email": "young@example.com",
            "password": "securepassword123",
            "name": "Young User",
            "is_adult_confirmed": False,
        })
        assert response.status_code == 400

    async def test_signup_short_password_rejected(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/signup", json={
            "email": "user@example.com",
            "password": "short",
            "name": "User",
            "is_adult_confirmed": True,
        })
        assert response.status_code == 422

    async def test_login_invalid_credentials(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    async def test_forgot_password_always_200(self, client: AsyncClient) -> None:
        """Should not reveal whether email exists."""
        response = await client.post("/api/v1/auth/forgot-password", json={
            "email": "nonexistent@example.com",
        })
        assert response.status_code == 200

    async def test_logout_always_succeeds(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200

    async def test_health_endpoint(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"