"""Sitemap generation and caching utilities."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from flask import url_for

if TYPE_CHECKING:
    from flask import Flask


class SitemapManager:
    """Manages sitemap generation and caching."""
    
    def __init__(self, app: Flask | None = None):
        """Initialize the sitemap manager."""
        self.app = app
        self.cache_dir = None
        self.cache_file = None
        self._last_generated = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """Initialize the sitemap manager with a Flask app."""
        self.app = app
        
        # Setup cache directory
        instance_path = Path(app.instance_path)
        self.cache_dir = instance_path / 'cache'
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / 'sitemap.xml'
        
        # Register event listeners
        self._register_listeners()
    
    def _register_listeners(self) -> None:
        """Register SQLAlchemy event listeners for auto-update."""
        from sqlalchemy import event
        from .models import KeywordAlias, KeywordCategory, LearningKeyword

        # Listen for changes to keywords
        event.listen(LearningKeyword, 'after_insert', self._on_model_change)
        event.listen(LearningKeyword, 'after_update', self._on_model_change)
        event.listen(LearningKeyword, 'after_delete', self._on_model_change)

        # Listen for changes to categories
        event.listen(KeywordCategory, 'after_insert', self._on_model_change)
        event.listen(KeywordCategory, 'after_update', self._on_model_change)
        event.listen(KeywordCategory, 'after_delete', self._on_model_change)

        # Listen for changes to keyword aliases
        event.listen(KeywordAlias, 'after_insert', self._on_model_change)
        event.listen(KeywordAlias, 'after_update', self._on_model_change)
        event.listen(KeywordAlias, 'after_delete', self._on_model_change)
    
    def _on_model_change(self, mapper, connection, target) -> None:
        """Callback when a model changes - invalidate cache."""
        self.invalidate_cache()
    
    def invalidate_cache(self) -> None:
        """Invalidate the sitemap cache."""
        if self.cache_file and self.cache_file.exists():
            try:
                self.cache_file.unlink()
                self._last_generated = None
            except Exception as e:
                if self.app:
                    self.app.logger.warning(f"Failed to invalidate sitemap cache: {e}")
    
    def generate_sitemap(self, force: bool = False) -> str:
        """
        Generate sitemap XML content.
        
        Args:
            force: Force regeneration even if cache exists
            
        Returns:
            XML content as string
        """
        # Check cache first
        if not force and self.cache_file and self.cache_file.exists():
            cache_age = datetime.utcnow().timestamp() - self.cache_file.stat().st_mtime
            # Cache valid for 1 hour
            if cache_age < 3600:
                try:
                    return self.cache_file.read_text(encoding='utf-8')
                except Exception as e:
                    if self.app:
                        self.app.logger.warning(f"Failed to read sitemap cache: {e}")
        
        # Generate fresh sitemap
        xml_content = self._build_sitemap_xml()
        
        # Save to cache
        if self.cache_file:
            try:
                self.cache_file.write_text(xml_content, encoding='utf-8')
                self._last_generated = datetime.utcnow()
            except Exception as e:
                if self.app:
                    self.app.logger.warning(f"Failed to cache sitemap: {e}")
        
        return xml_content
    
    def _build_sitemap_xml(self) -> str:
        """Build the sitemap XML content."""
        from .models import KeywordAlias, KeywordCategory, LearningKeyword, slugify

        if not self.app:
            raise RuntimeError("SitemapManager requires an application context")
        
        # Use application context for URL generation
        with self.app.app_context():
            keywords = LearningKeyword.query.order_by(
                LearningKeyword.updated_at.desc()
            ).all()
            aliases = KeywordAlias.query.order_by(KeywordAlias.updated_at.desc()).all()
            categories = KeywordCategory.query.order_by(KeywordCategory.position.asc()).all()
            
            xml_lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            ]
            
            # Homepage
            xml_lines.extend([
                '  <url>',
                f'    <loc>{url_for("main.index", _external=True)}</loc>',
                f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>',
                '    <changefreq>daily</changefreq>',
                '    <priority>1.0</priority>',
                '  </url>'
            ])
            
            # Category pages
            for category in categories:
                xml_lines.extend([
                    '  <url>',
                    f'    <loc>{url_for("main.category_detail", slug=category.slug, _external=True)}</loc>',
                    f'    <lastmod>{datetime.utcnow().strftime("%Y-%m-%d")}</lastmod>',
                    '    <changefreq>weekly</changefreq>',
                    '    <priority>0.9</priority>',
                    '  </url>'
                ])
            
            # Keywords
            for keyword in keywords:
                category_slug = slugify(keyword.category.name)
                xml_lines.extend([
                    '  <url>',
                    f'    <loc>{url_for("main.keyword_detail", category_slug=category_slug, slug=keyword.slug, _external=True)}</loc>',
                    f'    <lastmod>{keyword.updated_at.strftime("%Y-%m-%d")}</lastmod>',
                    '    <changefreq>weekly</changefreq>',
                    '    <priority>0.8</priority>',
                    '  </url>'
                ])

            # Keyword Aliases
            for alias in aliases:
                category_slug = slugify(alias.keyword.category.name)
                xml_lines.extend([
                    '  <url>',
                    f'    <loc>{url_for("main.keyword_detail", category_slug=category_slug, slug=alias.slug, _external=True)}</loc>',
                    f'    <lastmod>{alias.updated_at.strftime("%Y-%m-%d")}</lastmod>',
                    '    <changefreq>weekly</changefreq>',
                    '    <priority>0.6</priority>',
                    '  </url>'
                ])
            
            xml_lines.append('</urlset>')
            
            return '\n'.join(xml_lines)
    
    def get_stats(self) -> dict:
        """Get sitemap statistics."""
        from .models import KeywordAlias, KeywordCategory, LearningKeyword

        if not self.app:
            raise RuntimeError("SitemapManager requires an application context")
        
        stats = {
            'keywords_count': LearningKeyword.query.count(),
            'aliases_count': KeywordAlias.query.count(),
            'categories_count': KeywordCategory.query.count(),
            'total_urls': 1,  # Homepage
            'last_generated': None,
            'cache_exists': False,
            'cache_age': None,
        }
        
        stats['total_urls'] += stats['keywords_count'] + stats['aliases_count'] + stats['categories_count']
        
        if self.cache_file and self.cache_file.exists():
            stats['cache_exists'] = True
            stats['last_generated'] = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            cache_age = datetime.utcnow().timestamp() - self.cache_file.stat().st_mtime
            stats['cache_age'] = int(cache_age)
        
        # Get last modified keyword or alias
        last_keyword = LearningKeyword.query.order_by(
            LearningKeyword.updated_at.desc()
        ).first()
        last_alias = KeywordAlias.query.order_by(KeywordAlias.updated_at.desc()).first()

        timestamps = [
            dt for dt in (
                last_keyword.updated_at if last_keyword else None,
                last_alias.updated_at if last_alias else None,
            )
            if dt is not None
        ]

        if timestamps:
            stats['last_modified'] = max(timestamps)
        
        return stats


# Global sitemap manager instance
sitemap_manager = SitemapManager()
