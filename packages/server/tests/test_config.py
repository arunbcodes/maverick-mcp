"""Tests for server configuration module."""

import os
import pytest


class TestSettings:
    """Test Settings class."""

    def test_settings_import(self):
        """Test Settings can be imported."""
        from maverick_server.config import Settings
        assert Settings is not None

    def test_get_settings_import(self):
        """Test get_settings can be imported."""
        from maverick_server.config import get_settings
        assert get_settings is not None

    def test_settings_defaults(self):
        """Test Settings has sensible defaults."""
        from maverick_server.config import Settings

        settings = Settings()
        assert settings.server_name == "maverick-mcp"
        assert settings.server_port == 8003
        assert settings.transport == "sse"

    def test_settings_database_url_default(self):
        """Test database URL defaults to SQLite."""
        from maverick_server.config import Settings

        settings = Settings()
        assert "sqlite" in settings.database_url

    def test_settings_redis_url(self):
        """Test Redis URL property."""
        from maverick_server.config import Settings

        settings = Settings()
        # No Redis by default
        assert settings.redis_url is None

    def test_settings_api_key_properties(self):
        """Test API key check properties."""
        from maverick_server.config import Settings

        settings = Settings()
        # Should return False if not set
        assert isinstance(settings.has_tiingo, bool)
        assert isinstance(settings.has_openrouter, bool)
        assert isinstance(settings.has_exa, bool)

    def test_settings_validate(self):
        """Test settings validation."""
        from maverick_server.config import Settings

        settings = Settings()
        warnings = settings.validate()
        # Should return a list
        assert isinstance(warnings, list)

    def test_get_settings_caching(self):
        """Test get_settings returns cached instance."""
        from maverick_server.config import get_settings, reset_settings_cache

        reset_settings_cache()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestRouterImports:
    """Test router module imports."""

    def test_routers_package_import(self):
        """Test routers package can be imported."""
        from maverick_server import routers
        assert routers is not None

    def test_register_all_tools_import(self):
        """Test register_all_tools can be imported."""
        from maverick_server.routers import register_all_tools
        assert register_all_tools is not None

    def test_technical_router_import(self):
        """Test technical router can be imported."""
        from maverick_server.routers.technical import register_technical_tools
        assert register_technical_tools is not None

    def test_screening_router_import(self):
        """Test screening router can be imported."""
        from maverick_server.routers.screening import register_screening_tools
        assert register_screening_tools is not None

    def test_portfolio_router_import(self):
        """Test portfolio router can be imported."""
        from maverick_server.routers.portfolio import register_portfolio_tools
        assert register_portfolio_tools is not None

    def test_data_router_import(self):
        """Test data router can be imported."""
        from maverick_server.routers.data import register_data_tools
        assert register_data_tools is not None

    def test_health_router_import(self):
        """Test health router can be imported."""
        from maverick_server.routers.health import register_health_tools
        assert register_health_tools is not None


class TestMainModule:
    """Test __main__ module."""

    def test_main_module_import(self):
        """Test __main__ module can be imported."""
        from maverick_server import __main__
        assert __main__ is not None

    def test_main_function_exists(self):
        """Test main function exists."""
        from maverick_server.__main__ import main
        assert main is not None
        assert callable(main)
