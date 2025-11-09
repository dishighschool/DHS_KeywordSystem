"""Test markdown preview API endpoint."""
from html import unescape

import pytest
from markdown2 import markdown


def test_markdown_preview_api_with_tables(client, admin_user):
    """Test that the markdown preview API correctly renders tables."""
    # Login as admin
    with client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        # Test markdown with table
        test_markdown = """牛頓第一運動定律指出，若一物體所受的外力為零，則該物體將維持靜止或等速直線運動的狀態。

| 標題1 | 標題2 | 標題3 |
| ----- | ----- | ----- |
| 內容1 | 內容2 | 內容3 |
| 內容4 | 內容5 | 內容6 |
"""
        
        response = client.post(
            '/admin/api/markdown-preview',
            json={'markdown': test_markdown},
            follow_redirects=True
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert '<table>' in data['html']
        assert '<thead>' in data['html']
        assert '<tbody>' in data['html']
        assert '標題1' in data['html']
        assert '內容1' in data['html']


def test_markdown_preview_api_with_code_blocks(client, admin_user):
    """Test that the markdown preview API correctly renders code blocks."""
    with client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        test_markdown = """```python
def hello():
    print("Hello World")
```"""
        
        response = client.post(
            '/admin/api/markdown-preview',
            json={'markdown': test_markdown}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert '<code>' in data['html'] or '<pre>' in data['html']
        assert 'hello' in data['html']


def test_markdown_preview_api_unescape_entities(client, admin_user):
    """Test that the API unescapes HTML entities before rendering."""
    with client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        # Simulate content with HTML entities (e.g., from database)
        test_markdown = "| A &#124; B | C |\n| --- | --- |\n| 1 | 2 |"
        
        response = client.post(
            '/admin/api/markdown-preview',
            json={'markdown': test_markdown}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # After unescaping &#124; becomes |, so table should parse correctly
        assert '<table>' in data['html']


def test_markdown_preview_api_no_content(client, admin_user):
    """Test that the API handles missing content gracefully."""
    with client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        response = client.post(
            '/admin/api/markdown-preview',
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data


def test_markdown_preview_api_xss_protection(client, admin_user):
    """Test that the API protects against XSS with safe_mode='escape'."""
    with client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin_user.id)
        
        malicious_markdown = '<script>alert("XSS")</script>\n\n**Bold text**'
        
        response = client.post(
            '/admin/api/markdown-preview',
            json={'markdown': malicious_markdown}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        # Script tags should be escaped
        assert '<script>' not in data['html']
        assert '&lt;script&gt;' in data['html'] or '&amp;lt;' in data['html']
        # But markdown formatting should still work
        assert '<strong>' in data['html'] or '<b>' in data['html']
