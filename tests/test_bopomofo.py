from __future__ import annotations

import pytest

from app.utils import seo


def test_convert_bopomofo_to_keyboard_maps_known_symbols():
    mapping = seo.convert_bopomofo_to_keyboard("ㄅㄆ ㄉˊ")

    assert mapping == "1q 26"


@pytest.mark.skipif(not seo.PYPINYIN_AVAILABLE, reason="pypinyin 未安裝")
def test_generate_bopomofo_typo_returns_ascii_when_dependency_available():
    sample = "牛頓第一運動定律"
    result = seo.generate_bopomofo_typo(sample)

    assert result
    assert all(ord(char) < 128 for char in result)


def test_generate_bopomofo_typo_returns_empty_without_dependency(monkeypatch):
    monkeypatch.setattr(seo, "PYPINYIN_AVAILABLE", False)
    monkeypatch.setattr(seo, "pinyin", None)
    monkeypatch.setattr(seo, "Style", None)

    assert seo.generate_bopomofo_typo("測試") == ""

