"""Unit tests covering pypinyin-related helpers without external API calls."""
from __future__ import annotations

from app.utils import seo


def test_generate_common_typos_uses_bopomofo_typo(monkeypatch):
    monkeypatch.setattr(seo, "generate_bopomofo_typo", lambda keyword: "abcd")

    typos = seo.generate_common_typos("測試")

    assert typos == ["abcd"]


def test_generate_search_questions_appends_typo_variants():
    typos = ["abcd"]
    questions = seo.generate_search_questions("測試", typos)

    assert any("abcd" in question for question in questions)
    assert any(question.startswith("什麼是測試") for question in questions)

