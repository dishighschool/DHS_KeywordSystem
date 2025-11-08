"""Unit tests for SEO helper functions."""

import pytest

from app.utils.seo import generate_bopomofo_typo, generate_seo_html, generate_seo_text


@pytest.mark.parametrize("word", ["什麼", "如何", "使用", "學習", "程式", "資料庫"])
def test_generate_bopomofo_typo_returns_ascii(word):
    typo = generate_bopomofo_typo(word)
    assert isinstance(typo, str)
    assert typo == typo.lower()
    assert all(ord(char) < 128 for char in typo)


def test_generate_seo_text_includes_aliases_and_questions():
    keyword = "Python"
    aliases = ["派森", "python", "Python語言", "Python程式語言"]

    seo_data = generate_seo_text(keyword, aliases)

    assert seo_data["keyword"] == keyword
    assert set(aliases[:3]).issubset(set(seo_data["aliases"]))
    assert len(seo_data["questions"]) >= 6
    assert isinstance(seo_data["typos"], list)
    if seo_data["typos"]:
        assert all(isinstance(item, str) and item for item in seo_data["typos"])
    assert seo_data["paragraphs"]
    assert seo_data["full_text"].strip()


def test_generate_seo_text_without_aliases_still_produces_content():
    seo_data = generate_seo_text("演算法")

    assert seo_data["aliases"] == []
    assert seo_data["paragraphs"]
    assert "演算法" in seo_data["full_text"]


def test_generate_seo_html_contains_alias_information():
    keyword = "JavaScript"
    aliases = ["JS", "javascript", "ECMAScript", "JS語言"]

    content = generate_seo_html(keyword, aliases)

    assert keyword in content
    for alias in aliases[:4]:
        assert alias in content
    assert "相關搜尋" in content
    assert "\n\n" in content
