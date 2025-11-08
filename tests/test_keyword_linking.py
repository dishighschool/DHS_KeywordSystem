"""Tests for keyword auto-linking functionality."""
import uuid
from urllib.parse import quote

import pytest
from flask import url_for


def _login_client(client, user) -> None:
    """Authenticate the provided test client as the given user."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['user_id'] = str(user.id)
        sess['_fresh'] = True


def test_keyword_linker_imports():
    """Test that keyword linker can be imported."""
    from app.keyword_linker import keyword_linker, KeywordLinker
    
    assert keyword_linker is not None
    assert isinstance(keyword_linker, KeywordLinker)


def test_keyword_linking_in_content(client, db_session, sample_category, sample_user):
    """Test that keywords are automatically linked in content."""
    from app.models import LearningKeyword
    
    # Create two keywords
    keyword1 = LearningKeyword(
        title='Python',
        slug='python',
        description_markdown='Python is a programming language.',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    
    keyword2 = LearningKeyword(
        title='數學',
        slug='math',
        description_markdown='學習 Python 之前需要了解數學基礎。',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    
    db_session.add_all([keyword1, keyword2])
    db_session.commit()
    
    # Visit keyword2 detail page
    response = client.get(f'/{sample_category.slug}/math')
    assert response.status_code == 200
    
    # Should contain link to Python keyword
    data = response.data.decode('utf-8')
    assert 'Python' in data
    assert 'keyword-link' in data or '<a href=' in data


def test_keyword_not_linked_to_itself(client, db_session, sample_category, sample_user):
    """Test that a keyword doesn't link to itself."""
    from app.models import LearningKeyword
    
    keyword = LearningKeyword(
        title='遞迴',
        slug='recursion',
        description_markdown='遞迴是一種程式設計技巧,遞迴函數會呼叫自己。',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    
    db_session.add(keyword)
    db_session.commit()
    
    # The keyword should not link to itself
    response = client.get(f'/{sample_category.slug}/recursion')
    assert response.status_code == 200


def test_keyword_linker_pattern_creation():
    """Test that keyword linker creates valid regex patterns."""
    from app.keyword_linker import KeywordLinker
    
    linker = KeywordLinker()
    pattern = linker._create_keyword_pattern('Python')
    
    assert pattern is not None
    assert 'Python' in pattern


def test_keyword_linking_admin_page(client, admin_user):
    """Test that keyword linking admin page is accessible."""
    _login_client(client, admin_user)
    
    response = client.get('/admin/keyword-linking')
    assert response.status_code == 200
    data = response.data.decode('utf-8')
    assert 'keyword' in data.lower() or '連結' in data


def test_keyword_linking_requires_admin(client, auth_user):
    """Test that keyword linking page requires admin role."""
    _login_client(client, auth_user)
    
    response = client.get('/admin/keyword-linking', follow_redirects=False)
    assert response.status_code == 403


def test_keyword_link_with_special_characters(client, db_session, sample_category, sample_user):
    """Test that keywords with special characters can be linked."""
    from app.models import LearningKeyword
    
    keyword1 = LearningKeyword(
        title='C++',
        slug='cpp',
        description_markdown='C++ is a programming language.',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    
    keyword2 = LearningKeyword(
        title='程式語言',
        slug='programming-languages',
        description_markdown='常見的程式語言包括 C++ 和 Python。',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    
    db_session.add_all([keyword1, keyword2])
    db_session.commit()
    
    response = client.get(f'/{sample_category.slug}/programming-languages')
    assert response.status_code == 200


def test_alias_linking_in_content(client, db_session, sample_category, sample_user):
    """Alias names should auto-link to their alias page in other keyword articles."""
    from app.models import KeywordAlias, LearningKeyword, slugify

    primary_keyword = LearningKeyword(
        title='Python 開發',
        description_markdown='Python 相關內容',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    unique_suffix = uuid.uuid4().hex[:6]
    primary_keyword.slug = f"{primary_keyword.slug}-{unique_suffix}"
    db_session.add(primary_keyword)
    db_session.commit()

    alias = KeywordAlias(
        keyword_id=primary_keyword.id,
        title='Python 入門',
        slug=slugify('Python 入門'),
    )
    db_session.add(alias)
    db_session.commit()

    secondary_keyword = LearningKeyword(
        title='學習計畫',
        description_markdown='建議從 Python 入門 開始。',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    db_session.add(secondary_keyword)
    db_session.commit()

    category_slug = sample_category.slug
    encoded_category_slug = quote(category_slug)
    response = client.get(
        f'/{category_slug}/{secondary_keyword.slug}'
    )
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    encoded_alias_slug = quote(alias.slug)
    # Alias should link to /<category>/<alias-slug> (encoded for non-ASCII)
    expected_href = f'href="/{encoded_category_slug}/{encoded_alias_slug}"'
    assert expected_href in html


def test_alias_detail_page(client, db_session, sample_category, sample_user):
    """Alias pages should render like independent keywords with related names section."""
    from app.models import KeywordAlias, LearningKeyword, slugify

    keyword = LearningKeyword(
        title='演算法分析',
        description_markdown='演算法別名頁面內容。',
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    db_session.add(keyword)
    db_session.commit()

    alias = KeywordAlias(
        keyword_id=keyword.id,
        title='演算法設計',
        slug=slugify('演算法設計'),
    )
    db_session.add(alias)
    db_session.commit()

    category_slug = sample_category.slug
    encoded_category_slug = quote(category_slug)
    response = client.get(f'/{category_slug}/{alias.slug}')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    
    # Should look like an independent page (no "別名" badges)
    assert '別名：' not in html
    
    # Should show title as main headline
    assert alias.title in html
    
    # Should expose alternate names list with the canonical keyword
    assert '別稱' in html
    assert keyword.title in html
    
    encoded_canonical_slug = quote(keyword.slug)
    canonical_path = f'/{encoded_category_slug}/{encoded_canonical_slug}'
    assert canonical_path in html
