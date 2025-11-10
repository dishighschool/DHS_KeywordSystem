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


def _clean_title(value: str | None) -> str:
    """Return a trimmed title with normalized internal whitespace."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _plain_text_from_html(html: str) -> str:
    """Collapse HTML to plain text with normalized whitespace."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _plain_text_from_seo(seo_content: str | None) -> str:
    """Collapse generated SEO content into a searchable snippet."""
    if not seo_content:
        return ""
    parts: list[str] = []
    for raw_line in seo_content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("相關搜尋："):
            _, _, payload = line.partition("：")
            parts.append(payload.strip())
        else:
            parts.append(line)
    combined = " ".join(parts)
    return re.sub(r"\s+", " ", combined).strip()


def _extract_related_queries(seo_content: str | None) -> list[str]:
    """Extract related search queries from SEO content."""
    queries: list[str] = []
    if not seo_content:
        return queries
    for raw_line in seo_content.splitlines():
        line = raw_line.strip()
        if not line.startswith("相關搜尋："):
            continue
        _, _, payload = line.partition("：")
        for item in payload.split("、"):
            cleaned = _clean_title(item)
            if cleaned:
                queries.append(cleaned)
    return queries


def _truncate_text(text: str, limit: int = 160) -> str:
    """Truncate long text safely for meta usage."""
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def _prepare_seo_sections(seo_content: str | None) -> dict[str, object]:
    """Prepare structured SEO sections for template rendering."""
    if not seo_content:
        return {"title": "", "paragraphs": [], "related_queries": []}

    lines = [line.strip() for line in seo_content.splitlines() if line.strip()]
    if not lines:
        return {"title": "", "paragraphs": [], "related_queries": []}

    title_line = _clean_title(lines[0])
    paragraphs: list[str] = []
    related_queries: list[str] = []

    for line in lines[1:]:
        if line.startswith("相關搜尋："):
            _, _, payload = line.partition("：")
            for item in payload.split("、"):
                cleaned = _clean_title(item)
                if cleaned:
                    related_queries.append(cleaned)
        else:
            paragraphs.append(line)

    return {
        "title": title_line,
        "paragraphs": paragraphs,
        "related_queries": related_queries,
    }


def _build_meta_keywords(base_terms: list[str], related_queries: list[str]) -> str:
    """Create a concise, deduplicated keyword list for meta tags."""
    seen: set[str] = set()
    keywords: list[str] = []

    for term in base_terms + related_queries:
        cleaned = _clean_title(term)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        keywords.append(cleaned)
        seen.add(key)
        if len(keywords) >= 16:
            break

    return ",".join(keywords)


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
    keyword = (
        LearningKeyword.query
        .join(LearningKeyword.category)
        .filter(
            LearningKeyword.slug == slug,
            LearningKeyword.is_public == True,
            KeywordCategory.is_public == True,
        )
        .first()
    )

    alias = None
    is_alias = False
    canonical_url: str | None = None
    current_alias_id: int | None = None

    if not keyword:
        alias = (
            KeywordAlias.query
            .join(KeywordAlias.keyword)
            .join(LearningKeyword.category)
            .filter(
                KeywordAlias.slug == slug,
                LearningKeyword.is_public == True,
                KeywordCategory.is_public == True,
            )
            .first()
        )

        if not alias:
            abort(404)

        keyword = alias.keyword
        expected_category_slug = slugify(keyword.category.name)

        if category_slug.lower() != expected_category_slug:
            return redirect(
                url_for("main.keyword_detail", category_slug=expected_category_slug, slug=slug),
                code=301,
            )

        is_alias = True
        canonical_url = url_for(
            "main.keyword_detail", category_slug=expected_category_slug, slug=keyword.slug, _external=True
        )
        current_alias_id = alias.id
        display_title = _clean_title(alias.title)
        last_modified = alias.updated_at
    else:
        expected_category_slug = slugify(keyword.category.name)
        if category_slug.lower() != expected_category_slug:
            return redirect(
                url_for("main.keyword_detail", category_slug=expected_category_slug, slug=keyword.slug),
                code=301,
            )

        display_title = _clean_title(keyword.title)
        last_modified = keyword.updated_at

    keyword_clean_title = _clean_title(keyword.title)
    category_name = _clean_title(keyword.category.name)

    keyword.view_count += 1

    raw_markdown = unescape(keyword.description_markdown or "")
    html_description = markdown(
        raw_markdown,
        extras=["fenced-code-blocks", "tables", "strike", "task_lists", "break-on-newline"],
        safe_mode="escape",
    )  # noqa: S607
    html_description = keyword_linker.link_keywords_in_html(
        html_description, current_keyword_id=keyword.id
    )
    description_plain = _plain_text_from_html(html_description)

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

    alternative_names: list[dict[str, str]] = []
    if is_alias:
        alternative_names.append(
            {
                "title": keyword_clean_title,
                "url": url_for(
                    "main.keyword_detail",
                    category_slug=keyword.category.slug,
                    slug=keyword.slug,
                ),
            }
        )
        for other_alias in keyword.aliases:
            if other_alias.id == current_alias_id:
                continue
            alt_title = _clean_title(other_alias.title)
            if not alt_title:
                continue
            alternative_names.append(
                {
                    "title": alt_title,
                    "url": url_for(
                        "main.keyword_detail",
                        category_slug=keyword.category.slug,
                        slug=other_alias.slug,
                    ),
                }
            )
    else:
        for keyword_alias in keyword.aliases:
            alt_title = _clean_title(keyword_alias.title)
            if not alt_title:
                continue
            alternative_names.append(
                {
                    "title": alt_title,
                    "url": url_for(
                        "main.keyword_detail",
                        category_slug=keyword.category.slug,
                        slug=keyword_alias.slug,
                    ),
                }
            )

    seo_alias_titles: list[str] = []
    if is_alias:
        seo_alias_titles.append(keyword_clean_title)
        for other_alias in keyword.aliases:
            if other_alias.id == current_alias_id:
                continue
            alt_title = _clean_title(other_alias.title)
            if alt_title:
                seo_alias_titles.append(alt_title)
    else:
        for keyword_alias in keyword.aliases:
            alt_title = _clean_title(keyword_alias.title)
            if alt_title:
                seo_alias_titles.append(alt_title)

    seo_keyword_title = display_title if is_alias else keyword_clean_title

    if keyword.seo_auto_generate or not keyword.seo_content:
        seo_html = generate_seo_html(seo_keyword_title, aliases=seo_alias_titles)
        if keyword.seo_auto_generate:
            keyword.seo_content = seo_html
    else:
        seo_html = keyword.seo_content

    seo_html = seo_html or ""
    seo_plain_text = _plain_text_from_seo(seo_html)
    seo_sections = _prepare_seo_sections(seo_html)
    related_queries = seo_sections.get("related_queries", [])

    meta_description_source = seo_plain_text or description_plain or display_title
    seo_meta_description = _truncate_text(meta_description_source, 160)

    base_terms = [display_title, keyword_clean_title, category_name]
    base_terms.extend([entry["title"] for entry in alternative_names])
    base_terms.extend(["學習關鍵字", "教育資源"])
    seo_meta_keywords = _build_meta_keywords(
        base_terms,
        related_queries if isinstance(related_queries, list) else [],
    )

    db.session.commit()

    return render_template(
        "main/keyword_detail.html",
        keyword=keyword,
        display_title=display_title,
        keyword_clean_title=keyword_clean_title,
    category_name=category_name,
        last_modified=last_modified,
        html_description=html_description,
        related_keywords=related_keywords,
        alternative_names=alternative_names if alternative_names else None,
        canonical_url=canonical_url,
        is_alias=is_alias,
        seo_content=seo_html,
        seo_sections=seo_sections,
        seo_plain_text=seo_plain_text,
        seo_meta_description=seo_meta_description,
        seo_meta_keywords=seo_meta_keywords,
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
    seo_cache: dict[int, dict[str, object]] = {}
    
    # Add keywords
    for keyword in keywords:
        description_html = markdown(
            unescape(keyword.description_markdown or ""),
            extras=["fenced-code-blocks", "tables", "strike", "task_lists", "break-on-newline"],
            safe_mode="escape",
        )
        description_text = _plain_text_from_html(description_html)

        alias_titles = [
            _clean_title(alias.title)
            for alias in keyword.aliases
            if _clean_title(alias.title)
        ]

        seo_content = keyword.seo_content or generate_seo_html(
            _clean_title(keyword.title),
            aliases=alias_titles,
        )
        seo_plain_text = _plain_text_from_seo(seo_content)
        seo_sections = _prepare_seo_sections(seo_content)
        related_queries = seo_sections.get("related_queries", [])
        seo_cache[keyword.id] = {
            "plain": seo_plain_text,
            "related_queries": related_queries if isinstance(related_queries, list) else [],
        }

        search_data.append({
            'title': _clean_title(keyword.title),
            'slug': keyword.slug,
            'category': _clean_title(keyword.category.name),
            'category_slug': keyword.category.slug,
            'category_icon': keyword.category.icon,
            'description': _truncate_text(description_text, 150),
            'description_full': description_text,
            'url': url_for('main.keyword_detail', category_slug=keyword.category.slug, slug=keyword.slug),
            'type': 'keyword',
            'updated_at': keyword.updated_at.strftime('%Y-%m-%d'),
            'seo_text': seo_plain_text,
            'seo_related_queries': seo_cache[keyword.id]['related_queries'],
        })
    
    # Add aliases
    for alias in aliases:
        description_html = markdown(
            unescape(alias.keyword.description_markdown or ""),
            extras=["fenced-code-blocks", "tables", "strike", "task_lists", "break-on-newline"],
            safe_mode="escape",
        )
        description_text = _plain_text_from_html(description_html)

        keyword_seo = seo_cache.get(alias.keyword_id, {"plain": "", "related_queries": []})
        seo_plain_text = keyword_seo.get("plain", "")

        search_data.append({
            'title': _clean_title(alias.title),
            'slug': alias.slug,
            'category': _clean_title(alias.keyword.category.name),
            'category_slug': alias.keyword.category.slug,
            'category_icon': alias.keyword.category.icon,
            'description': _truncate_text(description_text, 150),
            'description_full': description_text,
            'url': url_for('main.keyword_detail', category_slug=alias.keyword.category.slug, slug=alias.slug),
            'type': 'alias',
            'main_keyword': _clean_title(alias.keyword.title),
            'updated_at': alias.updated_at.strftime('%Y-%m-%d'),
            'seo_text': str(seo_plain_text),
            'seo_related_queries': keyword_seo.get('related_queries', []),
        })
    
    return jsonify(search_data)
