"""Automatic keyword linking utility."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from flask import url_for

if TYPE_CHECKING:
    from .models import LearningKeyword


class KeywordLinker:
    """Automatically link keywords in text content."""
    
    def __init__(self):
        """Initialize the keyword linker."""
        self._keyword_cache = {}
        self._cache_timestamp = None
    
    def link_keywords_in_html(self, html_content: str, current_keyword_id: int | None = None) -> str:
        """
        Find and link keywords in HTML content.
        
        Args:
            html_content: HTML content to process
            current_keyword_id: ID of current keyword to exclude from linking
            
        Returns:
            HTML content with linked keywords
        """
        from .models import KeywordAlias, LearningKeyword, slugify

        query = LearningKeyword.query.filter_by(is_public=True)
        if current_keyword_id:
            query = query.filter(LearningKeyword.id != current_keyword_id)

        keywords = query.order_by(LearningKeyword.title.desc()).all()

        alias_query = KeywordAlias.query.join(LearningKeyword).filter(LearningKeyword.is_public == True)
        if current_keyword_id:
            alias_query = alias_query.filter(KeywordAlias.keyword_id != current_keyword_id)
        aliases = alias_query.order_by(KeywordAlias.title.desc()).all()

        link_targets: list[tuple[str, str]] = []
        seen_titles: set[str] = set()

        for kw in keywords:
            title = kw.title.strip()
            if not title:
                continue
            title_key = title.lower()
            if title_key in seen_titles:
                continue
            category_slug = slugify(kw.category.name)
            link_targets.append(
                (title, url_for("main.keyword_detail", category_slug=category_slug, slug=kw.slug))
            )
            seen_titles.add(title_key)

        for alias in aliases:
            title = alias.title.strip()
            if not title:
                continue
            title_key = title.lower()
            if title_key in seen_titles:
                continue
            category_slug = slugify(alias.keyword.category.name)
            link_targets.append(
                (title, url_for("main.keyword_detail", category_slug=category_slug, slug=alias.slug))
            )
            seen_titles.add(title_key)

        sorted_titles = sorted(link_targets, key=lambda item: len(item[0]), reverse=True)

        result = html_content

        for title, target_url in sorted_titles:
            # 使用更寬鬆的模式,不要求單詞邊界(因為中文沒有單詞邊界)
            # 只要求不在 HTML 標籤內或已有的連結內
            pattern = re.escape(title)

            def replace_if_valid(match: re.Match[str]) -> str:
                before_text = match.string[: match.start()]
                after_text = match.string[match.end():]
                
                # 檢查是否在 HTML 標籤內
                open_tags = before_text.count("<")
                close_tags = before_text.count(">")
                if open_tags > close_tags:
                    return match.group(0)
                
                # 檢查後面是否有未閉合的標籤
                if after_text:
                    next_open = after_text.find("<")
                    next_close = after_text.find(">")
                    if next_close != -1 and (next_open == -1 or next_close < next_open):
                        return match.group(0)

                # 檢查是否在 <a> 標籤內
                last_a_open = before_text.rfind("<a ")
                last_a_close = before_text.rfind("</a>")
                if last_a_open > last_a_close:
                    return match.group(0)

                return (
                    f'<a href="{target_url}" class="keyword-link" '
                    f'title="查看關鍵字: {title}">{match.group(0)}</a>'
                )

            result = re.sub(pattern, replace_if_valid, result, flags=re.IGNORECASE)

        return result
    
    def _create_keyword_pattern(self, keyword: str) -> str:
        """
        Create a regex pattern for matching keyword.
        
        Pattern should:
        - Match the keyword as a whole word
        - Not match inside HTML tags
        - Not match inside existing links
        """
        # Escape special regex characters
        escaped = re.escape(keyword)
        
        # Pattern: keyword not inside tags or links
        # Negative lookbehind: not preceded by < or inside <a> tag
        # Negative lookahead: not followed by > or inside </a> tag
        pattern = (
            r'(?<!<[^>]*)'  # Not inside a tag
            r'(?<!<a[^>]*>)'  # Not inside a link opening tag
            r'\b'  # Word boundary
            f'({escaped})'
            r'\b'  # Word boundary
            r'(?![^<]*>)'  # Not followed by tag closing
            r'(?![^<]*</a>)'  # Not inside a closing link tag
        )
        
        return pattern
    
    def link_keywords_in_markdown(
        self, markdown_content: str, current_keyword_id: int | None = None
    ) -> str:
        """
        Find and link keywords in Markdown content before HTML conversion.
        
        Args:
            markdown_content: Markdown content to process
            current_keyword_id: ID of current keyword to exclude from linking
            
        Returns:
            Markdown content with linked keywords
        """
        from .models import KeywordAlias, LearningKeyword, slugify

        query = LearningKeyword.query.filter_by(is_public=True)
        if current_keyword_id:
            query = query.filter(LearningKeyword.id != current_keyword_id)

        keywords = query.order_by(LearningKeyword.title.desc()).all()

        alias_query = KeywordAlias.query.join(LearningKeyword).filter(LearningKeyword.is_public == True)
        if current_keyword_id:
            alias_query = alias_query.filter(KeywordAlias.keyword_id != current_keyword_id)
        aliases = alias_query.order_by(KeywordAlias.title.desc()).all()

        link_targets: list[tuple[str, str]] = []
        seen_titles: set[str] = set()

        for kw in keywords:
            title = kw.title.strip()
            if not title:
                continue
            title_key = title.lower()
            if title_key in seen_titles:
                continue
            category_slug = slugify(kw.category.name)
            link_targets.append(
                (title, url_for("main.keyword_detail", category_slug=category_slug, slug=kw.slug))
            )
            seen_titles.add(title_key)

        for alias in aliases:
            title = alias.title.strip()
            if not title:
                continue
            title_key = title.lower()
            if title_key in seen_titles:
                continue
            category_slug = slugify(alias.keyword.category.name)
            link_targets.append(
                (title, url_for("main.keyword_detail", category_slug=category_slug, slug=alias.slug))
            )
            seen_titles.add(title_key)

        sorted_titles = sorted(link_targets, key=lambda item: len(item[0]), reverse=True)

        result = markdown_content

        for title, target_url in sorted_titles:
            # 使用更寬鬆的模式,不使用 \b 單詞邊界(中文不適用)
            # 只檢查不在 Markdown 連結語法內
            pattern_parts = [
                r"(?<!\[)",  # Not preceded by [
                r"(?<!!)",  # Not preceded by ! (for images)
                f"({re.escape(title)})",
                r"(?!\])",  # Not followed by ]
                r"(?!\()",  # Not followed by (
            ]
            pattern = "".join(pattern_parts)

            replacement = f'[{title}]({target_url} "查看關鍵字: {title}")'
            result = re.sub(pattern, replacement, result, count=0, flags=re.IGNORECASE)

        return result


# Global keyword linker instance
keyword_linker = KeywordLinker()
