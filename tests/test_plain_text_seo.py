from app.utils.seo import generate_seo_html


def test_generate_seo_html_is_plain_text():
    content = generate_seo_html("測試關鍵字", ["別名一", "別名二"])
    normalized = content.strip()

    assert normalized  # 內容不可為空
    assert "<" not in normalized and ">" not in normalized
    assert "測試關鍵字" in normalized
    assert "相關搜尋" in normalized
