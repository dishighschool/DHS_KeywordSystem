"""Tests for sitemap and robots.txt functionality."""
from urllib.parse import quote

import pytest
from flask import url_for


def _login_client(client, user) -> None:
    """Authenticate the provided test client as the given user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['user_id'] = str(user.id)
        sess['_fresh'] = True


def test_sitemap_exists(client):
    """Test that sitemap.xml is accessible."""
    response = client.get('/sitemap.xml')
    assert response.status_code == 200
    assert response.content_type == 'application/xml; charset=utf-8'


def test_sitemap_contains_homepage(client):
    """Test that sitemap includes homepage."""
    response = client.get('/sitemap.xml')
    data = response.data.decode('utf-8')
    
    assert '<?xml version="1.0" encoding="UTF-8"?>' in data
    assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in data
    assert '<loc>http://localhost/</loc>' in data
    assert '<priority>1.0</priority>' in data
    assert '<changefreq>daily</changefreq>' in data


def test_sitemap_contains_keywords(client, db_session, sample_keyword):
    """Test that sitemap includes keyword pages."""
    response = client.get('/sitemap.xml')
    data = response.data.decode('utf-8')
    
    # Should contain the keyword URL (now without /keywords/ prefix)
    encoded_category_slug = quote(sample_keyword.category.slug)
    encoded_keyword_slug = quote(sample_keyword.slug)
    assert f'http://localhost/{encoded_category_slug}/{encoded_keyword_slug}' in data
    assert '<changefreq>weekly</changefreq>' in data
    assert '<priority>0.8</priority>' in data


def test_sitemap_contains_aliases(client, db_session, sample_keyword):
    """Sitemap should include keyword alias URLs."""
    from app.models import KeywordAlias, slugify

    alias = KeywordAlias(
        keyword_id=sample_keyword.id,
        title='測試別名',
        slug=slugify('測試別名'),
    )
    db_session.add(alias)
    db_session.commit()

    response = client.get('/sitemap.xml')
    data = response.data.decode('utf-8')

    # Alias URLs now use same structure as keywords: /<category>/<alias>
    encoded_category_slug = quote(sample_keyword.category.slug)
    encoded_alias_slug = quote(alias.slug)
    assert f'http://localhost/{encoded_category_slug}/{encoded_alias_slug}' in data
    assert '<priority>0.6</priority>' in data


def test_sitemap_lastmod_format(client, db_session, sample_keyword):
    """Test that sitemap lastmod dates are properly formatted."""
    response = client.get('/sitemap.xml')
    data = response.data.decode('utf-8')
    
    # Should contain ISO date format (YYYY-MM-DD)
    assert '<lastmod>' in data
    import re
    assert re.search(r'<lastmod>\d{4}-\d{2}-\d{2}</lastmod>', data)


def test_robots_txt_exists(client):
    """Test that robots.txt is accessible."""
    response = client.get('/robots.txt')
    assert response.status_code == 200
    assert response.content_type == 'text/plain; charset=utf-8'


def test_robots_txt_content(client):
    """Test that robots.txt has correct content."""
    response = client.get('/robots.txt')
    data = response.data.decode('utf-8')
    
    assert 'User-agent: *' in data
    assert 'Allow: /' in data
    assert 'Sitemap: http://localhost/sitemap.xml' in data
    assert 'Disallow: /admin/' in data
    assert 'Disallow: /auth/' in data
    assert 'Allow: /static/' in data


def test_sitemap_admin_page_requires_auth(client):
    """Test that sitemap admin page requires authentication."""
    response = client.get('/admin/sitemap')
    # Should redirect to login
    assert response.status_code == 302


def test_sitemap_admin_page_requires_admin_role(client, auth_user):
    """Test that sitemap admin page requires admin role."""
    _login_client(client, auth_user)
    
    response = client.get('/admin/sitemap', follow_redirects=False)
    # Should return 403 Forbidden for non-admin
    assert response.status_code == 403


def test_sitemap_admin_page_accessible_by_admin(client, admin_user):
    """Test that sitemap admin page is accessible by admin."""
    _login_client(client, admin_user)
    
    response = client.get('/admin/sitemap')
    assert response.status_code == 200
    assert b'Sitemap' in response.data
    assert b'sitemap.xml' in response.data


def test_sitemap_generate_endpoint(client, admin_user):
    """Test sitemap generation endpoint."""
    _login_client(client, admin_user)
    
    response = client.post('/admin/sitemap/generate', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sitemap' in response.data


def test_sitemap_updates_with_new_keyword(client, db_session, sample_category, sample_user):
    """Test that sitemap automatically includes new keywords."""
    from app.models import LearningKeyword
    
    # Create new keyword
    new_keyword = LearningKeyword(
        title='New Test Keyword',
        slug='new-test-keyword',
        description_markdown='Test description',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    db_session.add(new_keyword)
    db_session.commit()
    
    # Check sitemap includes new keyword
    response = client.get('/sitemap.xml')
    data = response.data.decode('utf-8')
    
    assert 'new-test-keyword' in data


def test_sitemap_xml_well_formed(client):
    """Test that sitemap XML is well-formed."""
    response = client.get('/sitemap.xml')
    data = response.data.decode('utf-8')
    
    # Basic XML structure checks
    assert data.count('<urlset') == 1
    assert data.count('</urlset>') == 1
    assert data.count('<url>') == data.count('</url>')
    assert data.count('<loc>') == data.count('</loc>')
    assert data.count('<lastmod>') == data.count('</lastmod>')
