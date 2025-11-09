"""
Test markdown rendering with XSS protection and all features.
"""
import pytest
from markdown2 import markdown


class TestMarkdownRendering:
    """Test markdown rendering capabilities."""

    def test_table_rendering(self):
        """Test that tables are correctly rendered."""
        markdown_text = """
| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
"""
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<table>" in html
        assert "</table>" in html
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "<tr>" in html
        assert "<th>" in html
        assert "<td>" in html

    def test_xss_script_protection(self):
        """Test that script tags are escaped."""
        malicious = "<script>alert('XSS')</script>"
        html = markdown(malicious, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "alert" in html  # Content is preserved but escaped

    def test_xss_img_onerror_protection(self):
        """Test that img onerror attributes are escaped."""
        malicious = '<img src=x onerror=alert("XSS")>'
        html = markdown(malicious, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert 'onerror=alert' not in html
        assert "&lt;img" in html

    def test_xss_iframe_protection(self):
        """Test that iframe tags are escaped."""
        malicious = '<iframe src="javascript:alert(\'XSS\')"></iframe>'
        html = markdown(malicious, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<iframe" not in html
        assert "&lt;iframe" in html

    def test_fenced_code_blocks(self):
        """Test that fenced code blocks are rendered."""
        markdown_text = """
```python
def hello():
    print("Hello, World!")
```
"""
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<pre>" in html or "<code>" in html
        assert "def hello" in html

    def test_headers(self):
        """Test that headers are rendered."""
        markdown_text = """
# Header 1
## Header 2
### Header 3
"""
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<h1>" in html
        assert "<h2>" in html
        assert "<h3>" in html

    def test_lists(self):
        """Test that lists are rendered."""
        markdown_text = """
- Item 1
- Item 2
- Item 3

1. Numbered 1
2. Numbered 2
"""
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<ul>" in html
        assert "<ol>" in html
        assert "<li>" in html

    def test_links(self):
        """Test that links are rendered safely."""
        markdown_text = "[Example](https://example.com)"
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert '<a href="https://example.com">' in html or 'href="https://example.com"' in html
        assert "Example" in html

    def test_emphasis(self):
        """Test that emphasis and strong are rendered."""
        markdown_text = "**bold** and *italic* and ***both***"
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<strong>" in html or "<b>" in html
        assert "<em>" in html or "<i>" in html

    def test_blockquote(self):
        """Test that blockquotes are rendered."""
        markdown_text = "> This is a quote"
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<blockquote>" in html

    def test_inline_code(self):
        """Test that inline code is rendered."""
        markdown_text = "This is `inline code` example."
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "<code>" in html
        assert "inline code" in html

    def test_combined_markdown_with_xss(self):
        """Test that complex markdown with XSS attempts works correctly."""
        markdown_text = """
# Safe Header

| Column 1 | Column 2 |
| -------- | -------- |
| Data     | <script>alert('XSS')</script> |

```python
def safe_code():
    return "<script>not executed</script>"
```

Normal text with **bold** and *italic*.

<img src=x onerror=alert('XSS')>
"""
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        # Check markdown is rendered
        assert "<h1>" in html
        assert "<table>" in html
        assert "<strong>" in html or "<b>" in html
        
        # Check XSS is escaped
        assert "<script>alert" not in html
        assert 'onerror=alert' not in html
        assert "&lt;script&gt;" in html or "alert" not in html.replace("&lt;", "").replace("&gt;", "")

    def test_chinese_content(self):
        """Test that Chinese content is rendered correctly."""
        markdown_text = """
# 牛頓運動定律

| 定律 | 描述 |
| ---- | ---- |
| 第一定律 | 物體保持靜止或等速直線運動 |
| 第二定律 | F = ma |

**重要**：這是一個測試。
"""
        html = markdown(markdown_text, extras=["fenced-code-blocks", "tables", "strikethrough", "task_lists"], safe_mode="escape")
        
        assert "牛頓運動定律" in html
        assert "定律" in html
        assert "描述" in html
        assert "<table>" in html
