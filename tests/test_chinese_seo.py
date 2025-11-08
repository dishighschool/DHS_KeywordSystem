"""Behavioral tests for Chinese keyword SEO helpers."""
from __future__ import annotations

import pytest

from app.utils.seo import generate_seo_html, generate_seo_text


@pytest.mark.parametrize(
    "keyword,aliases",
    [
        ("資料庫", ["數據庫", "Database"]),
        ("演算法", ["算法", "Algorithm"]),
        ("人工智慧", ["AI", "Artificial Intelligence"]),
    ],
)
def test_generate_seo_text_returns_consistent_structure(keyword: str, aliases: list[str]):
    """Ensure Chinese keywords produce populated SEO payloads."""

    seo_data = generate_seo_text(keyword, aliases)

    assert seo_data["keyword"] == keyword
    assert set(aliases).intersection(seo_data["aliases"])  # 至少包含一個別名
    assert seo_data["typos"] is not None
    assert isinstance(seo_data["paragraphs"], list) and seo_data["paragraphs"]
    assert all(isinstance(p, str) and p.strip() for p in seo_data["paragraphs"])
    assert seo_data["full_text"].strip()
    assert any("注音" in p or "誤輸入" in p for p in seo_data["paragraphs"])


def test_generate_seo_text_without_aliases_still_mentions_keyword():
    seo_data = generate_seo_text("深度學習")

    assert seo_data["aliases"] == []
    assert seo_data["paragraphs"]
    assert any("深度學習" in section for section in seo_data["paragraphs"])


def test_generate_seo_html_contains_related_search_block():
    html = generate_seo_html("資料結構", ["Data Structure", "數據結構"])

    assert "資料結構" in html
    assert "相關搜尋" in html
    assert "\n\n" in html  # 段落以雙換行分隔
    assert "<script" not in html.lower()

