"""
測試 Markdown 渲染器的 XSS 防護功能
"""
import pytest
from app.utils.markdown_renderer import render_markdown_safe, strip_markdown_to_text


class TestMarkdownXSSProtection:
    """測試 Markdown 渲染器能否正確防範 XSS 攻擊"""

    def test_script_tag_blocked(self):
        """測試 script 標籤被阻擋"""
        malicious = "<script>alert('XSS')</script>"
        result = render_markdown_safe(malicious)
        
        # script 標籤應該被移除（bleach 的 strip=True 會保留文本內容）
        assert "<script>" not in result.lower()
        assert "</script>" not in result.lower()
        # 文本內容可能被保留，但無法執行
        # 重要的是沒有可執行的 script 標籤

    def test_onclick_attribute_stripped(self):
        """測試 onclick 等事件屬性被移除"""
        malicious = '<a href="#" onclick="alert(\'XSS\')">Click</a>'
        result = render_markdown_safe(malicious)
        
        # onclick 屬性應該被移除
        assert "onclick" not in result.lower()
        assert "alert" not in result

    def test_javascript_protocol_blocked(self):
        """測試 javascript: 協議被阻擋"""
        malicious = '[Click me](javascript:alert("XSS"))'
        result = render_markdown_safe(malicious)
        
        # javascript: 協議應該被移除
        assert "javascript:" not in result.lower()

    def test_iframe_tag_blocked(self):
        """測試 iframe 標籤被阻擋"""
        malicious = '<iframe src="https://evil.com"></iframe>'
        result = render_markdown_safe(malicious)
        
        # iframe 應該被移除
        assert "<iframe" not in result.lower()

    def test_img_onerror_stripped(self):
        """測試 img 標籤的 onerror 屬性被移除"""
        malicious = '<img src="x" onerror="alert(\'XSS\')">'
        result = render_markdown_safe(malicious)
        
        # onerror 屬性應該被移除
        assert "onerror" not in result.lower()
        # img 標籤本身可能保留（如果 src 有效）或被移除

    def test_style_with_expression_blocked(self):
        """測試帶有 expression 的 style 屬性被阻擋"""
        malicious = '<div style="width:expression(alert(\'XSS\'))">test</div>'
        result = render_markdown_safe(malicious)
        
        # expression 應該被移除
        assert "expression" not in result.lower()

    def test_object_embed_tags_blocked(self):
        """測試 object 和 embed 標籤被阻擋"""
        malicious = '<object data="evil.swf"></object><embed src="evil.swf">'
        result = render_markdown_safe(malicious)
        
        # object 和 embed 應該被移除
        assert "<object" not in result.lower()
        assert "<embed" not in result.lower()

    def test_base_tag_blocked(self):
        """測試 base 標籤被阻擋"""
        malicious = '<base href="https://evil.com">'
        result = render_markdown_safe(malicious)
        
        # base 標籤應該被移除
        assert "<base" not in result.lower()

    def test_safe_markdown_renders_correctly(self):
        """測試正常的 Markdown 仍然能正確渲染"""
        markdown_text = """
# 標題

這是**粗體**和*斜體*文字。

- 列表項目 1
- 列表項目 2

[安全連結](https://example.com)
"""
        result = render_markdown_safe(markdown_text)
        
        # 正常的 Markdown 應該被正確渲染
        assert "<h1" in result
        assert "<strong>" in result or "<b>" in result
        assert "<em>" in result or "<i>" in result
        assert "<ul>" in result
        assert "<li>" in result
        assert 'href="https://example.com"' in result

    def test_strikethrough_renders_safely(self):
        """測試刪除線正確渲染"""
        markdown_text = "這是~~刪除的文字~~正常文字"
        result = render_markdown_safe(markdown_text)
        
        # 刪除線應該被正確渲染
        assert "<s>" in result or "<del>" in result or "<strike>" in result
        assert "刪除的文字" in result

    def test_code_block_renders_safely(self):
        """測試代碼塊正確渲染"""
        markdown_text = """
```python
def hello():
    print("<script>alert('XSS')</script>")
```
"""
        result = render_markdown_safe(markdown_text)
        
        # 代碼塊應該被正確渲染
        assert "<pre>" in result or "<code>" in result
        # 代碼塊中的 HTML 應該被轉義
        assert "&lt;script&gt;" in result or "<script>" not in result

    def test_table_renders_safely(self):
        """測試表格正確渲染"""
        markdown_text = """
| 標題 1 | 標題 2 |
| ------ | ------ |
| 內容 1 | 內容 2 |
"""
        result = render_markdown_safe(markdown_text)
        
        # 表格應該被正確渲染
        assert "<table>" in result
        assert "<thead>" in result
        assert "<tbody>" in result
        assert "<tr>" in result
        assert "<th>" in result or "<td>" in result

    def test_mixed_xss_attempts(self):
        """測試混合的 XSS 攻擊嘗試"""
        markdown_text = """
# 正常標題

這是正常文字。

<script>alert('XSS1')</script>

[正常連結](https://example.com)

<img src=x onerror="alert('XSS2')">

**正常粗體** <a href="javascript:alert('XSS3')">連結</a>

<iframe src="https://evil.com"></iframe>
"""
        result = render_markdown_safe(markdown_text)
        
        # 正常內容應該保留
        assert "<h1" in result
        assert "正常標題" in result
        assert "正常文字" in result
        assert "https://example.com" in result
        
        # XSS 攻擊應該被阻擋
        assert "<script>" not in result.lower() or "&lt;script&gt;" in result
        assert "onerror" not in result.lower()
        assert "javascript:" not in result.lower()
        assert "<iframe" not in result.lower()

    def test_external_links_get_noopener(self):
        """測試外部連結自動添加 rel=noopener noreferrer"""
        markdown_text = "[External Link](https://example.com)"
        result = render_markdown_safe(markdown_text)
        
        # 外部連結應該有 target="_blank" 和 rel="noopener noreferrer"
        assert 'target="_blank"' in result
        assert 'rel=' in result
        assert 'noopener' in result.lower()

    def test_strip_markdown_to_text_removes_html(self):
        """測試 strip_markdown_to_text 正確移除所有 HTML"""
        markdown_text = """
# 標題

這是**粗體**和~~刪除線~~文字。

<script>alert('XSS')</script>
"""
        result = strip_markdown_to_text(markdown_text)
        
        # 應該只保留純文本
        assert "<" not in result
        assert ">" not in result
        assert "標題" in result
        assert "粗體" in result
        assert "刪除線" in result
        # XSS 應該被移除或轉義
        assert "alert" not in result or "script" not in result.lower()

    def test_nested_xss_attempts(self):
        """測試嵌套的 XSS 攻擊嘗試"""
        malicious = "<a href='#' onclick='alert(1)'><img src='x' onerror='alert(2)'></a>"
        result = render_markdown_safe(malicious)
        
        # 所有事件處理器都應該被移除
        assert "onclick" not in result.lower()
        assert "onerror" not in result.lower()

    def test_data_uri_with_javascript(self):
        """測試 data URI 中的 JavaScript"""
        malicious = '<a href="data:text/html,<script>alert(\'XSS\')</script>">Click</a>'
        result = render_markdown_safe(malicious)
        
        # data URI 應該被阻擋（不在允許的協議列表中）
        assert "data:text/html" not in result.lower()

    def test_svg_with_script(self):
        """測試 SVG 中的 script"""
        malicious = '<svg><script>alert("XSS")</script></svg>'
        result = render_markdown_safe(malicious)
        
        # SVG 標籤應該被移除（不在允許列表中）
        assert "<svg" not in result.lower()
        assert "<script" not in result.lower()

    def test_form_tags_blocked(self):
        """測試 form 標籤被阻擋"""
        malicious = '<form action="https://evil.com"><input type="submit"></form>'
        result = render_markdown_safe(malicious)
        
        # form 標籤應該被移除
        assert "<form" not in result.lower()

    def test_meta_refresh_blocked(self):
        """測試 meta refresh 被阻擋"""
        malicious = '<meta http-equiv="refresh" content="0;url=https://evil.com">'
        result = render_markdown_safe(malicious)
        
        # meta 標籤應該被移除
        assert "<meta" not in result.lower()

    def test_chinese_content_with_xss(self):
        """測試包含中文的 XSS 攻擊"""
        markdown_text = """
# 測試標題

這是一段中文內容。

<script>alert('中文XSS')</script>

**重要**：這是正常的文字。
"""
        result = render_markdown_safe(markdown_text)
        
        # 中文內容應該保留
        assert "測試標題" in result
        assert "中文內容" in result
        assert "重要" in result
        
        # XSS 應該被阻擋
        assert "<script>" not in result.lower() or "&lt;script&gt;" in result
