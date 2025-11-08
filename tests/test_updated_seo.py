"""Targeted tests for SEO HTML question selection."""
from __future__ import annotations

import pytest

from app.utils.seo import generate_seo_html, generate_seo_text


@pytest.mark.parametrize(
    "keyword,aliases",
    [
        ("資料庫", ["數據庫", "Database", "DB"]),
        ("演算法", ["算法", "Algorithm"]),
        ("深度學習", []),
    ],
)
def test_generate_seo_html_includes_keyword_and_aliases(keyword: str, aliases: list[str]):
    """Ensure the rendered text contains the main keyword and optional aliases."""

    html = generate_seo_html(keyword, aliases)

    assert keyword in html
    for alias in aliases:
        assert alias in html


def test_generate_seo_html_limits_question_count():
    """The related search list should stay within the curated bounds."""

    seo_payload = generate_seo_text("Python", ["派森", "Python 程式語言"])
    html = generate_seo_html("Python", seo_payload["aliases"])

    assert "相關搜尋" in html
    _, questions_block = html.split("相關搜尋：", 1)
    questions = [item for item in questions_block.strip().split("、") if item]
    assert 1 <= len(questions) <= 8
    # 問句應該包含注音輸入法錯誤或基礎問句
    assert any("什麼" in q or "如何" in q or any(t in q for t in seo_payload["typos"]) for q in questions)

