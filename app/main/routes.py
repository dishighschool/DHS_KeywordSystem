"""Public-facing routes for the learning keywords portal."""
from __future__ import annotations

import re
from datetime import datetime
from html import unescape

from flask import Blueprint, abort, jsonify, make_response, redirect, render_template, url_for

from markdown2 import markdown

from ..extensions import db
from ..models import KeywordAlias, KeywordCategory, LearningKeyword, slugify
from ..sitemap import sitemap_manager
from ..keyword_linker import keyword_linker
from ..utils.seo import generate_seo_html


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Render the landing page with search capabilities."""
    categories = KeywordCategory.query.filter_by(is_public=True).order_by(KeywordCategory.position.asc()).all()
    keywords = (
        LearningKeyword.query
        .filter_by(is_public=True)
        .join(LearningKeyword.category)
        .filter(KeywordCategory.is_public == True)
        .order_by(LearningKeyword.position.asc())
        .all()
    )
    
    # Fetch all aliases for search functionality (only public keywords)
    aliases = (
        KeywordAlias.query
        .join(KeywordAlias.keyword)
        .filter(LearningKeyword.is_public == True)
        .join(LearningKeyword.category)
        .filter(KeywordCategory.is_public == True)
        .order_by(KeywordAlias.title.asc())
        .all()
    )
    
    return render_template("main/index.html", categories=categories, keywords=keywords, aliases=aliases)


@main_bp.get("/<string:slug>")
def category_detail(slug: str):
    """Render a category detail page with all keywords and search functionality."""
    # First check if this is a category
    category = KeywordCategory.query.filter_by(slug=slug, is_public=True).first()
    if not category:
        abort(404)
    
    # Get all public keywords in this category
    keywords = (
        LearningKeyword.query
        .filter_by(category_id=category.id, is_public=True)
        .order_by(LearningKeyword.position.asc())
        .all()
    )
    
    # Get all aliases for keywords in this category
    aliases = (
        KeywordAlias.query
        .join(KeywordAlias.keyword)
        .filter(LearningKeyword.category_id == category.id)
        .order_by(KeywordAlias.title.asc())
        .all()
    )
    
    # Get all public categories for navigation with keyword counts
    all_categories = KeywordCategory.query.filter_by(is_public=True).order_by(KeywordCategory.position.asc()).all()
    
    # Build category keyword counts (public keywords only)
    category_counts = {}
    for cat in all_categories:
        count = LearningKeyword.query.filter_by(category_id=cat.id, is_public=True).count()
        category_counts[cat.id] = count
    
    return render_template(
        "main/category_detail.html",
        category=category,
        keywords=keywords,
        aliases=aliases,
        all_categories=all_categories,
        category_counts=category_counts,
    )


@main_bp.get("/<string:category_slug>/<string:slug>")
def keyword_detail(category_slug: str, slug: str):
    """Render a keyword or alias detail page optimized for reading and SEO."""
    # First try to find a public keyword with this slug
    keyword = (
        LearningKeyword.query
        .join(LearningKeyword.category)
        .filter(
            LearningKeyword.slug == slug,
            LearningKeyword.is_public == True,
            KeywordCategory.is_public == True
        )
        .first()
    )
    
    # If not found, try to find an alias with this slug (pointing to public keyword)
    if not keyword:
        alias = (
            KeywordAlias.query
            .join(KeywordAlias.keyword)
            .join(LearningKeyword.category)
            .filter(
                KeywordAlias.slug == slug,
                LearningKeyword.is_public == True,
                KeywordCategory.is_public == True
            )
            .first()
        )
        
        if alias:
            # Found an alias, prepare alias-specific data
            keyword = alias.keyword
            expected_category_slug = slugify(keyword.category.name)
            
            # Validate category slug
            if category_slug.lower() != expected_category_slug:
                return redirect(
                    url_for("main.keyword_detail", category_slug=expected_category_slug, slug=slug),
                    code=301,
                )
            
            # Increment view count
            keyword.view_count += 1
            db.session.commit()
            
            # Convert markdown and link keywords
            # Ensure any HTML entities in stored markdown (e.g. &lt;, &#124;) are unescaped
            # before converting to HTML so markdown features like tables parse
            # correctly.
            html_description = markdown(unescape(keyword.description_markdown or ""), extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")  # noqa: S607
            html_description = keyword_linker.link_keywords_in_html(html_description, current_keyword_id=keyword.id)
            
            # Get related keywords (public only)
            related_keywords = (
                LearningKeyword.query
                .filter(
                    LearningKeyword.category_id == keyword.category_id,
                    LearningKeyword.is_public == True,
                    LearningKeyword.id != keyword.id,
                )
                .order_by(LearningKeyword.position.asc())
                .all()
            )
            
            # Build alternative names list (main keyword + other aliases)
            alternative_names = []
            
            # Add canonical keyword
            alternative_names.append({
                'title': keyword.title,
                'url': url_for('main.keyword_detail', category_slug=expected_category_slug, slug=keyword.slug)
            })
            
            # Add all other aliases (except current one)
            for other_alias in keyword.aliases:
                if other_alias.id != alias.id:
                    alternative_names.append({
                        'title': other_alias.title,
                        'url': url_for('main.keyword_detail', category_slug=expected_category_slug, slug=other_alias.slug)
                    })
            
            canonical_url = url_for(
                "main.keyword_detail", category_slug=expected_category_slug, slug=keyword.slug, _external=True
            )
            
            # Generate or use SEO content (for alias, use display title)
            all_aliases = [keyword.title] + [a['title'] for a in alternative_names if a['title'] != alias.title]
            if keyword.seo_auto_generate or not keyword.seo_content:
                # 自動生成 SEO 內容 (使用別名作為主要關鍵字)
                seo_html = generate_seo_html(alias.title, aliases=all_aliases)
                # 儲存到資料庫 (使用主關鍵字的設定)
                if keyword.seo_auto_generate:
                    keyword.seo_content = seo_html
                    db.session.commit()
            else:
                # 使用資料庫中的 SEO 內容
                seo_html = keyword.seo_content
            
            return render_template(
                "main/keyword_detail.html",
                keyword=keyword,
                display_title=alias.title,
                last_modified=alias.updated_at,
                html_description=html_description,
                related_keywords=related_keywords,
                alternative_names=alternative_names,
                canonical_url=canonical_url,
                is_alias=True,
                seo_content=seo_html,
            )
        
        # Neither keyword nor alias found
        abort(404)

    # Found a keyword, prepare keyword-specific data
    expected_category_slug = slugify(keyword.category.name)
    if category_slug.lower() != expected_category_slug:
        return redirect(
            url_for("main.keyword_detail", category_slug=expected_category_slug, slug=keyword.slug),
            code=301,
        )

    # Increment view count
    keyword.view_count += 1
    db.session.commit()

    # Convert markdown to HTML (unescape stored HTML entities first so
    # markdown tables and other block-level syntax render correctly)
    html_description = markdown(unescape(keyword.description_markdown or ""), extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")  # noqa: S607
    
    # Auto-link other keywords in the content
    html_description = keyword_linker.link_keywords_in_html(html_description, current_keyword_id=keyword.id)

    related_keywords = (
        LearningKeyword.query
        .filter(
            LearningKeyword.category_id == keyword.category_id,
            LearningKeyword.id != keyword.id,
            LearningKeyword.is_public == True,
        )
        .order_by(LearningKeyword.position.asc())
        .all()
    )

    # Build alternative names list (all aliases)
    alternative_names = []
    for alias in keyword.aliases:
        alternative_names.append({
            'title': alias.title,
            'url': url_for('main.keyword_detail', category_slug=expected_category_slug, slug=alias.slug)
        })

    # Generate or use SEO content
    all_aliases = [a['title'] for a in alternative_names]
    if keyword.seo_auto_generate or not keyword.seo_content:
        # 自動生成 SEO 內容
        seo_html = generate_seo_html(keyword.title, aliases=all_aliases)
        # 儲存到資料庫
        if keyword.seo_auto_generate:
            keyword.seo_content = seo_html
            db.session.commit()
    else:
        # 使用資料庫中的自訂 SEO 內容
        seo_html = keyword.seo_content

    return render_template(
        "main/keyword_detail.html",
        keyword=keyword,
        display_title=keyword.title,
        last_modified=keyword.updated_at,
        html_description=html_description,
        related_keywords=related_keywords,
        alternative_names=alternative_names if alternative_names else None,
        canonical_url=None,
        is_alias=False,
        seo_content=seo_html,
    )


@main_bp.get("/sitemap.xml")
def sitemap():
    """Generate and serve the XML sitemap for search engines."""
    xml_content = sitemap_manager.generate_sitemap()
    
    response = make_response(xml_content)
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    return response


@main_bp.get("/robots.txt")
def robots():
    """Serve the robots.txt file with sitemap reference."""
    sitemap_url = url_for('main.sitemap', _external=True)
    
    robots_content = [
        'User-agent: *',
        'Allow: /',
        '',
        '# Sitemap location',
        f'Sitemap: {sitemap_url}',
        '',
        '# Disallow admin pages',
        'Disallow: /admin/',
        'Disallow: /auth/',
        '',
        '# Allow static resources',
        'Allow: /static/',
    ]
    
    response = make_response('\n'.join(robots_content))
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response


@main_bp.get("/api/search")
def api_search():
    """API endpoint for global search functionality."""
    # Get all public keywords with their public categories
    keywords = LearningKeyword.query.join(KeywordCategory).filter(
        LearningKeyword.is_public == True,
        KeywordCategory.is_public == True
    ).order_by(
        KeywordCategory.position.asc(),
        LearningKeyword.title.asc()
    ).all()
    
    # Get all aliases (from public keywords in public categories)
    aliases = KeywordAlias.query.join(LearningKeyword).join(KeywordCategory).filter(
        LearningKeyword.is_public == True,
        KeywordCategory.is_public == True
    ).order_by(
        KeywordCategory.position.asc(),
        KeywordAlias.title.asc()
    ).all()
    
    # Build search data
    search_data = []
    
    # Add keywords
    for keyword in keywords:
        # Convert markdown to plain text for description
        # Unescape stored entities before converting to plain HTML for
        # description extraction used in the search index.
        description_html = markdown(unescape(keyword.description_markdown or ""), extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        description_text = unescape(re.sub(r'<[^>]+>', '', description_html))
        
        search_data.append({
            'title': keyword.title,
            'slug': keyword.slug,
            'category': keyword.category.name,
            'category_slug': keyword.category.slug,
            'category_icon': keyword.category.icon,
            'description': description_text[:150],  # First 150 chars
            'url': url_for('main.keyword_detail', category_slug=keyword.category.slug, slug=keyword.slug),
            'type': 'keyword',
            'updated_at': keyword.updated_at.strftime('%Y-%m-%d')
        })
    
    # Add aliases
    for alias in aliases:
        description_html = markdown(unescape(alias.keyword.description_markdown or ""), extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        description_text = unescape(re.sub(r'<[^>]+>', '', description_html))
        
        search_data.append({
            'title': alias.title,
            'slug': alias.slug,
            'category': alias.keyword.category.name,
            'category_slug': alias.keyword.category.slug,
            'category_icon': alias.keyword.category.icon,
            'description': description_text[:150],
            'url': url_for('main.keyword_detail', category_slug=alias.keyword.category.slug, slug=alias.slug),
            'type': 'alias',
            'main_keyword': alias.keyword.title,
            'updated_at': alias.updated_at.strftime('%Y-%m-%d')
        })
    
    return jsonify(search_data)
