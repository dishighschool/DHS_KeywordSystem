"""Tests for AI service functionality."""

from __future__ import annotations

import pytest


class TestAIService:
    """Test AI service functions."""

    def test_ai_service_imports(self):
        """Test that AI service module can be imported."""
        from app.utils.ai_service import (
            DEFAULT_SYSTEM_PROMPT,
            generate_keyword_description,
            get_ai_settings,
            get_usage_statistics,
            get_user_usage_history,
            is_ai_enabled,
        )

        # Verify functions are callable
        assert callable(get_ai_settings)
        assert callable(is_ai_enabled)
        assert callable(generate_keyword_description)
        assert callable(get_usage_statistics)
        assert callable(get_user_usage_history)

        # Verify default prompt exists
        assert len(DEFAULT_SYSTEM_PROMPT) > 0

    def test_ai_settings_keys_exist(self):
        """Test that AI settings keys are defined."""
        from app.models import SiteSettingKey

        ai_keys = [
            SiteSettingKey.AI_API_KEY,
            SiteSettingKey.AI_MODEL,
            SiteSettingKey.AI_SYSTEM_PROMPT,
            SiteSettingKey.AI_MAX_TOKENS,
            SiteSettingKey.AI_TEMPERATURE,
            SiteSettingKey.AI_ENABLED,
        ]

        for key in ai_keys:
            assert key is not None

    def test_ai_usage_log_model(self, db_session):
        """Test AIUsageLog model creation."""
        from app.models import AIUsageLog, User

        # Create a test user
        user = User(
            discord_id="test_discord_id",
            username="test_user",
        )
        db_session.add(user)
        db_session.flush()

        # Create an AI usage log
        log = AIUsageLog(
            user_id=user.id,
            model="gemini-1.5-flash",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            keyword_title="測試關鍵字",
            generated_content="這是一段測試內容",
            success=True,
        )
        db_session.add(log)
        db_session.commit()

        # Verify the log was created
        saved_log = AIUsageLog.query.filter_by(keyword_title="測試關鍵字").first()
        assert saved_log is not None
        assert saved_log.model == "gemini-1.5-flash"
        assert saved_log.total_tokens == 150
        assert saved_log.success is True
        assert saved_log.user.username == "test_user"

    def test_ai_usage_log_nullable_user(self, db_session):
        """Test AIUsageLog model creation with nullable user_id."""
        from app.models import AIUsageLog

        # Create an AI usage log without user
        log = AIUsageLog(
            user_id=None,
            model="gemini-1.5-flash",
            prompt_tokens=50,
            completion_tokens=25,
            total_tokens=75,
            keyword_title="匿名測試",
            generated_content="這是匿名測試內容",
            success=True,
        )
        db_session.add(log)
        db_session.commit()

        # Verify the log was created with null user_id
        saved_log = AIUsageLog.query.filter_by(keyword_title="匿名測試").first()
        assert saved_log is not None
        assert saved_log.user_id is None
        assert saved_log.user is None
        assert saved_log.model == "gemini-1.5-flash"
        assert saved_log.total_tokens == 75
        assert saved_log.success is True

    def test_get_ai_settings_defaults(self, app, db_session):
        """Test get_ai_settings returns defaults when no settings are configured."""
        with app.app_context():
            from app.utils.ai_service import get_ai_settings

            settings = get_ai_settings()

            assert settings["api_key"] == ""
            # Model default is empty by default; admin should explicitly choose a model.
            assert settings["model"] == ""
            assert settings["max_tokens"] == 500
            assert settings["temperature"] == 0.7
            assert settings["enabled"] is False

    def test_is_ai_enabled_false_by_default(self, app, db_session):
        """Test is_ai_enabled returns False when not configured."""
        with app.app_context():
            from app.utils.ai_service import is_ai_enabled

            assert is_ai_enabled() is False

    def test_generate_description_fails_when_disabled(self, app, db_session):
        """Test generate_keyword_description returns error when AI is disabled."""
        with app.app_context():
            from app.utils.ai_service import generate_keyword_description

            result = generate_keyword_description("測試關鍵字")

            assert result["success"] is False
            assert "未啟用" in result["error"]

    def test_ai_forms_import(self):
        """Test that AI settings form can be imported."""
        from app.forms import AISettingsForm

        assert AISettingsForm is not None


class TestAIRoutes:
    """Test AI admin routes."""

    def test_ai_status_route_exists(self, app):
        """Test that AI status route is registered."""
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert "/admin/api/ai/status" in rules

    def test_ai_settings_route_exists(self, app):
        """Test that AI settings route is registered."""
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert "/admin/ai-settings" in rules

    def test_ai_generate_route_exists(self, app):
        """Test that AI generate description route is registered."""
        rules = [r.rule for r in app.url_map.iter_rules()]
        assert "/admin/api/ai/generate-description" in rules
