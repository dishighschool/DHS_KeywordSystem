"""Application factory for the learning keywords portal."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
import markdown2
from alembic.util import CommandError
from flask import Flask, current_app, jsonify, request
from flask_migrate import upgrade
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from .config import Config
from .extensions import csrf, db, login_manager, migrate, oauth
from .models import FooterSocialLink, NavigationLink, SiteSetting, User, slugify
from .sitemap import sitemap_manager

if TYPE_CHECKING:  # pragma: no cover
    from flask.typing import ResponseReturnValue


def create_app(config_object: type[Config] | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__, instance_relative_config=True, static_folder="static")
    config_object = config_object or Config
    app.config.from_object(config_object)

    _ensure_instance_folder(app)
    _register_extensions(app)
    _register_sitemap_manager(app)
    _register_blueprints(app)
    _register_template_context(app)
    _register_error_handlers(app)
    _register_cli(app)
    _ensure_database_schema(app)

    return app


def _ensure_instance_folder(app: Flask) -> None:
    """Make sure the instance folder exists for the SQLite database."""
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)


def _register_extensions(app: Flask) -> None:
    """Initialize third-party extensions with the Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore[assignment]
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:  # pragma: no cover - simple lookup
        if user_id and user_id.isdigit():
            return User.query.get(int(user_id))
        return User.query.filter_by(discord_id=user_id).first()

    oauth.init_app(app)
    from .auth.discord import register_discord_oauth

    register_discord_oauth(app, oauth)


def _register_sitemap_manager(app: Flask) -> None:
    """Initialize the sitemap manager for automatic updates."""
    sitemap_manager.init_app(app)


def _register_blueprints(app: Flask) -> None:
    """Attach Flask blueprints for routing."""
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")


def _register_template_context(app: Flask) -> None:
    """Expose navigation links and site branding to all templates."""

    @app.context_processor
    def inject_globals() -> dict[str, object]:  # pragma: no cover - simple mapping
        from .models import AnnouncementBanner
        
        nav_links = NavigationLink.query.order_by(NavigationLink.position.asc()).all()
        footer_links = FooterSocialLink.query.order_by(FooterSocialLink.position.asc()).all()
        announcements = AnnouncementBanner.query.filter_by(is_active=True).order_by(AnnouncementBanner.position.asc()).all()
        settings_raw = SiteSetting.as_dict()
        
        # 整合 logo 設定：優先使用上傳的檔案
        settings = settings_raw.copy()
        settings['header_logo_url'] = (
            settings_raw.get('header_logo_file') or 
            settings_raw.get('header_logo_url', '')
        )
        settings['footer_logo_url'] = (
            settings_raw.get('footer_logo_file') or 
            settings_raw.get('footer_logo_url', '')
        )
        
        return {
            "nav_links": nav_links,
            "footer_links": footer_links,
            "announcements": announcements,
            "site_settings": settings,
        }

    app.jinja_env.filters["slugify"] = slugify
    
    def markdown_filter(text: str) -> str:
        """Convert markdown text to HTML."""
        if not text:
            return ""
        return markdown2.markdown(text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
    
    app.jinja_env.filters["markdown"] = markdown_filter
    
    # Register YouTube URL filters
    from .utils.youtube import get_youtube_embed_url, extract_youtube_video_id, is_youtube_url
    
    app.jinja_env.filters["youtube_embed"] = get_youtube_embed_url
    app.jinja_env.filters["youtube_id"] = extract_youtube_video_id
    app.jinja_env.filters["is_youtube"] = is_youtube_url


def _register_error_handlers(app: Flask) -> None:
    """Register custom error pages for common HTTP errors."""
    from flask import render_template
    from .models import KeywordCategory

    @app.errorhandler(400)
    def bad_request_error(error: Exception) -> ResponseReturnValue:
        """Handle 400 Bad Request errors."""
        # 如果是 JSON 請求,返回 JSON 錯誤
        if request.is_json or 'application/json' in request.headers.get('Content-Type', ''):
            return jsonify({
                "success": False,
                "message": "無效的請求資料"
            }), 400
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden_error(error: Exception) -> ResponseReturnValue:
        """Handle 403 Forbidden errors."""
        # 如果是 JSON 請求,返回 JSON 錯誤
        if request.is_json or 'application/json' in request.headers.get('Content-Type', ''):
            return jsonify({
                "success": False,
                "message": "需要管理員權限"
            }), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error: Exception) -> ResponseReturnValue:
        """Handle 404 Not Found errors with hot categories."""
        # 如果是 JSON 請求,返回 JSON 錯誤
        if request.is_json or 'application/json' in request.headers.get('Content-Type', ''):
            return jsonify({
                "success": False,
                "message": "找不到請求的資源"
            }), 404
        # Get up to 6 public categories with most keywords for hot categories
        hot_categories = (
            KeywordCategory.query
            .filter_by(is_public=True)
            .order_by(KeywordCategory.created_at.desc())
            .limit(6)
            .all()
        )
        return render_template("errors/404.html", categories=hot_categories), 404

    @app.errorhandler(500)
    def internal_error(error: Exception) -> ResponseReturnValue:
        """Handle 500 Internal Server errors."""
        # Rollback any pending database transactions
        from .extensions import db
        db.session.rollback()
        
        # 如果是 JSON 請求,返回 JSON 錯誤
        if request.is_json or 'application/json' in request.headers.get('Content-Type', ''):
            return jsonify({
                "success": False,
                "message": "伺服器內部錯誤"
            }), 500
        
        # Generate error ID for tracking (optional)
        import uuid
        error_id = str(uuid.uuid4())[:8]
        
        return render_template("errors/500.html", error_id=error_id), 500


def _register_cli(app: Flask) -> None:
    """Add helpful Flask CLI commands."""

    @app.cli.command("seed")
    def seed_command() -> None:
        """Seed the database with example categories, keywords, and navigation."""
        from .seed import SeedService
        SeedService(db.session).run()
        click.secho("Database seeded with example content.", fg="green")


def _ensure_database_schema(app: Flask) -> None:
    """Ensure core database tables exist before handling requests."""

    bootstrap_state = {"done": False}

    def verify_schema() -> None:  # pragma: no cover - startup guard
        if bootstrap_state["done"]:
            return
        if app.config.get("TESTING", False):
            bootstrap_state["done"] = True
            return

        bootstrap_state["done"] = True

        with app.app_context():
            try:
                upgrade()
                inspector = inspect(db.engine)
                existing_tables = set(inspector.get_table_names())
                expected_tables = {table.name for table in db.Model.metadata.sorted_tables}
                missing = expected_tables - existing_tables
                if missing:
                    current_app.logger.warning(
                        "Detected missing tables %s; creating via metadata.",
                        ", ".join(sorted(missing)),
                    )
                    db.create_all()
            except (OperationalError, CommandError):
                current_app.logger.warning(
                    "Database schema verification failed; applying metadata create_all fallback.",
                    exc_info=True,
                )
                db.create_all()
            except Exception:  # pragma: no cover - defensive logging
                current_app.logger.exception("Unexpected error while ensuring database schema.")
                raise

    app.before_request(verify_schema)
