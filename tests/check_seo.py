"""Database-oriented regression checks for SEO content fields."""
from __future__ import annotations

from app.models import LearningKeyword


def test_keyword_defaults_have_no_seo_content(sample_keyword):
    assert sample_keyword.seo_content is None


def test_keyword_seo_content_persists(db_session, sample_category, sample_user):
    keyword = LearningKeyword(
        title="資料庫設計",
        slug="database-design",
        description_markdown="介紹資料庫設計的基本概念。",
        category_id=sample_category.id,
        author_id=sample_user.id,
        seo_content="關於資料庫設計的常見問題",
    )
    db_session.add(keyword)
    db_session.commit()

    saved = db_session.get(LearningKeyword, keyword.id)
    assert saved is not None
    assert saved.seo_content == "關於資料庫設計的常見問題"

