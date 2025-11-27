"""AI Service for Google Gemini API integration."""

from __future__ import annotations

import logging
from typing import Any

from flask_login import current_user

logger = logging.getLogger(__name__)

# Default system prompt for keyword description generation
DEFAULT_SYSTEM_PROMPT = """你是一個專業的教育內容編輯助手。你的任務是為學習關鍵字生成簡短、清晰、有教育意義的描述。

生成規則:
1. 描述應該簡潔明瞭,約 50-150 字
2. 使用繁體中文
3. 內容應該適合學習者理解
4. 可以使用 Markdown 格式
5. 不要包含標題(因為標題已經是關鍵字本身)
6. 直接開始描述內容,不要有前綴

範例輸出格式:
此概念是指...具體來說,...主要應用於...

請根據給定的關鍵字標題生成描述。"""


def get_ai_settings() -> dict[str, Any]:
    """Get AI settings from database."""
    from ..models import SiteSetting, SiteSettingKey

    # Safe integer conversion with fallback
    try:
        max_tokens = int(SiteSetting.get(SiteSettingKey.AI_MAX_TOKENS, "500") or "500")
    except (ValueError, TypeError):
        max_tokens = 500

    # Safe float conversion with fallback
    try:
        temperature = float(SiteSetting.get(SiteSettingKey.AI_TEMPERATURE, "0.7") or "0.7")
    except (ValueError, TypeError):
        temperature = 0.7

    return {
        "api_key": SiteSetting.get(SiteSettingKey.AI_API_KEY, ""),
        # Model is stored as the full model resource name (e.g. "models/gemini-1.5-pro");
        # keep empty default so admin explicitly picks a model
        "model": SiteSetting.get(SiteSettingKey.AI_MODEL, ""),
        "system_prompt": SiteSetting.get(SiteSettingKey.AI_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT),
        "max_tokens": max_tokens,
        "temperature": temperature,
        "enabled": SiteSetting.get(SiteSettingKey.AI_ENABLED, "false") == "true",
    }


def is_ai_enabled() -> bool:
    """Check if AI functionality is enabled."""
    settings = get_ai_settings()
    return settings["enabled"] and bool(settings["api_key"])


def fetch_available_models(api_key: str) -> list[dict[str, str]]:
    """Fetch available models from Google Gemini API.

    Args:
        api_key: Google AI Studio API key

    Returns:
        List of available models with name and display name
    """
    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        models = genai.list_models()

        available_models = []
        for model in models:
            # Only include models that support generateContent
                if "generateContent" in model.supported_generation_methods:
                    available_models.append(
                        {
                            # Use the full model resource name (models/...) as the value so it can be passed
                            # directly to the library when constructing the GenerativeModel.
                            "name": model.name,
                            "display_name": model.display_name,
                            "description": getattr(model, "description", "") or "",
                            "input_token_limit": getattr(model, "input_token_limit", 0),
                            "output_token_limit": getattr(model, "output_token_limit", 0),
                            "supported_generation_methods": getattr(model, "supported_generation_methods", []),
                        }
                    )

        return available_models

    except Exception as e:
        logger.error(f"Failed to fetch Gemini models: {e}")
        return []


def generate_keyword_description(keyword_title: str) -> dict[str, Any]:
    """Generate a keyword description using Google Gemini API.

    Args:
        keyword_title: The keyword title to generate description for

    Returns:
        Dictionary with success status, generated content, and usage stats
    """
    from ..extensions import db
    from ..models import AIUsageLog

    settings = get_ai_settings()

    if not settings["enabled"]:
        return {
            "success": False,
            "error": "AI 功能未啟用",
            "content": None,
        }

    if not settings["api_key"]:
        return {
            "success": False,
            "error": "未設定 API 金鑰",
            "content": None,
        }

    if not keyword_title or not keyword_title.strip():
        return {
            "success": False,
            "error": "關鍵字標題不能為空",
            "content": None,
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings["api_key"])

        model_name = settings.get("model") or ""
        # If the stored model doesn't include the 'models/' prefix, gracefully prefix it.
        if model_name and not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        # If there's still no model selected, try to auto-select the first available model
        if not model_name:
            models = fetch_available_models(settings["api_key"]) if settings.get("api_key") else []
            if models:
                model_name = models[0]["name"]

        if not model_name:
            return {"success": False, "error": "未選擇模型", "content": None}

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=settings["system_prompt"],
        )

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=settings["max_tokens"],
            temperature=settings["temperature"],
        )

        # Generate content
        prompt = f"請為以下學習關鍵字生成描述:\n\n關鍵字: {keyword_title}"

        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )

        # Extract usage metadata
        prompt_tokens = 0
        completion_tokens = 0
        if hasattr(response, "usage_metadata"):
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)

        total_tokens = prompt_tokens + completion_tokens

        # Get the generated text
        generated_text = ""
        if response.text:
            generated_text = response.text.strip()

        # Log usage (user_id is None if not authenticated)
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        usage_log = AIUsageLog(
            user_id=user_id,
            model=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            keyword_title=keyword_title,
            generated_content=generated_text,
            success=True,
        )
        db.session.add(usage_log)
        db.session.commit()

        return {
            "success": True,
            "content": generated_text,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "model": settings["model"],
            },
        }

    except Exception as e:
        error_message = str(e)
        logger.error(f"AI generation failed: {error_message}")

        # Provide user-friendly error messages
        if "location" in error_message.lower():
            user_error = "您的位置不被支援，請嘗試使用 VPN"
        elif "not found" in error_message.lower() or "404" in error_message:
            user_error = "選擇的模型無效或不支援，請重新選擇模型"
        else:
            user_error = f"生成失敗: {error_message}"

        # Log failed attempt
        try:
            user_id = current_user.id if current_user and current_user.is_authenticated else None
            usage_log = AIUsageLog(
                user_id=user_id,
                model=settings["model"],
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                keyword_title=keyword_title,
                success=False,
                error_message=error_message,
            )
            db.session.add(usage_log)
            db.session.commit()
        except Exception as log_error:
            logger.error(f"Failed to log AI usage error: {log_error}")

        return {
            "success": False,
            "error": user_error,
            "content": None,
        }


def get_usage_statistics() -> dict[str, Any]:
    """Get AI usage statistics.

    Returns:
        Dictionary with usage statistics
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func

    from ..extensions import db
    from ..models import AIUsageLog

    # Calculate date ranges
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Total statistics
    total_stats = (
        db.session.query(
            func.count(AIUsageLog.id).label("total_requests"),
            func.sum(AIUsageLog.prompt_tokens).label("total_prompt_tokens"),
            func.sum(AIUsageLog.completion_tokens).label("total_completion_tokens"),
            func.sum(AIUsageLog.total_tokens).label("total_tokens"),
        )
        .filter(AIUsageLog.success.is_(True))
        .first()
    )

    # Today's statistics
    today_stats = (
        db.session.query(
            func.count(AIUsageLog.id).label("requests"),
            func.sum(AIUsageLog.total_tokens).label("tokens"),
        )
        .filter(
            AIUsageLog.success.is_(True),
            AIUsageLog.created_at >= today_start,
        )
        .first()
    )

    # This week's statistics
    week_stats = (
        db.session.query(
            func.count(AIUsageLog.id).label("requests"),
            func.sum(AIUsageLog.total_tokens).label("tokens"),
        )
        .filter(
            AIUsageLog.success.is_(True),
            AIUsageLog.created_at >= week_start,
        )
        .first()
    )

    # This month's statistics
    month_stats = (
        db.session.query(
            func.count(AIUsageLog.id).label("requests"),
            func.sum(AIUsageLog.total_tokens).label("tokens"),
        )
        .filter(
            AIUsageLog.success.is_(True),
            AIUsageLog.created_at >= month_start,
        )
        .first()
    )

    # Error count
    error_count = db.session.query(func.count(AIUsageLog.id)).filter(AIUsageLog.success.is_(False)).scalar() or 0

    return {
        "total": {
            "requests": total_stats.total_requests or 0,
            "prompt_tokens": total_stats.total_prompt_tokens or 0,
            "completion_tokens": total_stats.total_completion_tokens or 0,
            "total_tokens": total_stats.total_tokens or 0,
        },
        "today": {
            "requests": today_stats.requests or 0,
            "tokens": today_stats.tokens or 0,
        },
        "week": {
            "requests": week_stats.requests or 0,
            "tokens": week_stats.tokens or 0,
        },
        "month": {
            "requests": month_stats.requests or 0,
            "tokens": month_stats.tokens or 0,
        },
        "errors": error_count,
    }


def get_user_usage_history(user_id: int | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Get AI usage history for a specific user or all users.

    Args:
        user_id: User ID to filter by, or None for all users
        limit: Maximum number of records to return

    Returns:
        List of usage records
    """
    from sqlalchemy.orm import selectinload

    from ..models import AIUsageLog, User

    query = AIUsageLog.query.options(selectinload(AIUsageLog.user).load_only(User.id, User.username))

    if user_id:
        query = query.filter(AIUsageLog.user_id == user_id)

    records = query.order_by(AIUsageLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": record.id,
            "user_id": record.user_id,
            "username": record.user.username if record.user else "未知用戶",
            "model": record.model,
            "keyword_title": record.keyword_title,
            "total_tokens": record.total_tokens,
            "success": record.success,
            "error_message": record.error_message,
            "created_at": record.created_at.isoformat(),
        }
        for record in records
    ]
