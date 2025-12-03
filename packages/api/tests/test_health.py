"""Tests for health endpoints."""

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_health_is_lightweight(self, client):
        """Health endpoint should be fast."""
        import time

        start = time.perf_counter()
        response = client.get("/health")
        duration = time.perf_counter() - start

        assert response.status_code == 200
        assert duration < 0.1  # Should complete in < 100ms


class TestReadinessEndpoint:
    """Tests for readiness probe."""

    @pytest.mark.skip(reason="Requires Redis and DB connection")
    def test_ready_checks_dependencies(self, client):
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert "checks" in data
        assert "redis" in data["checks"]
        assert "database" in data["checks"]


class TestStartupEndpoint:
    """Tests for startup probe."""

    @pytest.mark.skip(reason="Requires DB connection")
    def test_startup_checks_migrations(self, client):
        response = client.get("/startup")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "initializing"]

