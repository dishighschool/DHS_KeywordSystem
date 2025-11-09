"""Test XSS protection in markdown rendering."""

import pytest
from app import create_app


def test_markdown_xss_protection():
    """Test that markdown rendering escapes dangerous HTML tags."""
    app = create_app()

    with app.app_context():
        from app.main.routes import markdown

        # Test script tag is escaped
        malicious_input = '<script>alert("XSS")</script>'
        result = markdown(malicious_input, extras=["fenced-code-blocks"], safe_mode="escape")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

        # Test iframe tag is escaped
        malicious_iframe = '<iframe src="evil.com"></iframe>'
        result = markdown(malicious_iframe, extras=["fenced-code-blocks"], safe_mode="escape")
        assert "<iframe>" not in result
        assert "&lt;iframe" in result and "&gt;&lt;/iframe&gt;" in result

        # Test normal markdown still works
        normal_input = "# Hello World\n\nThis is **bold** text."
        result = markdown(normal_input, extras=["fenced-code-blocks"], safe_mode="escape")
        assert "<h1>Hello World</h1>" in result
        assert "<strong>bold</strong>" in result