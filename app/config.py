"""Configuration objects for the Flask application."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():  # pragma: no cover - environment helper
    load_dotenv(ENV_PATH)


def _resolve_sqlite_path(url: str) -> str:
    if not url.startswith("sqlite:///"):
        return url

    path_part = url.replace("sqlite:///", "", 1)
    path_obj = Path(path_part)
    if not path_obj.is_absolute():
        path_obj = BASE_DIR / path_obj
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path_obj.as_posix()}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    _raw_db_url = os.getenv("DATABASE_URL")
    if _raw_db_url:
        SQLALCHEMY_DATABASE_URI = _resolve_sqlite_path(_raw_db_url)
    else:
        SQLALCHEMY_DATABASE_URI = _resolve_sqlite_path(
            f"sqlite:///{(BASE_DIR / 'instance' / 'app.db').as_posix()}"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5000/auth/discord/callback")

    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "learning_keywords_session")
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")
    USE_PROXY_FIX = os.getenv("USE_PROXY_FIX", "1") not in {"0", "false", "False"}
    PROXY_FIX_FOR = int(os.getenv("PROXY_FIX_FOR", "1"))
    PROXY_FIX_PROTO = int(os.getenv("PROXY_FIX_PROTO", "1"))
    PROXY_FIX_HOST = int(os.getenv("PROXY_FIX_HOST", "1"))
    PROXY_FIX_PORT = int(os.getenv("PROXY_FIX_PORT", "1"))
    PROXY_FIX_PREFIX = int(os.getenv("PROXY_FIX_PREFIX", "0"))

    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "replace-this")

    # 檔案上傳設定
    UPLOAD_FOLDER = BASE_DIR / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 5MB max file size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
