"""Pytest fixtures for the Flask application."""
from __future__ import annotations

import uuid

import pytest

from app import create_app
from app.extensions import db
from app.models import KeywordCategory, LearningKeyword, Role, User


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
        PREFERRED_URL_SCHEME="http",
    )

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    with app.app_context():
        try:
            yield db.session
        finally:
            db.session.rollback()
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
            db.session.remove()


@pytest.fixture()
def sample_category(db_session):
    from app.models import slugify
    
    category_name = f"測試分類-{uuid.uuid4().hex[:6]}"
    category = KeywordCategory(
        name=category_name,
        slug=slugify(category_name),
        description="測試分類描述",
        icon="bi-folder",
    )
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture()
def sample_user(db_session):
    user = User(
        discord_id=uuid.uuid4().hex,
        username="測試使用者",
        avatar_hash=None,
        role=Role.USER,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def admin_user(db_session):
    admin = User(
        discord_id=uuid.uuid4().hex,
        username="管理員",
        avatar_hash=None,
        role=Role.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture()
def auth_user(db_session):
    user = User(
        discord_id=uuid.uuid4().hex,
        username="一般成員",
        avatar_hash=None,
        role=Role.USER,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def sample_keyword(db_session, sample_category, sample_user):
    keyword = LearningKeyword(
        title=f"測試關鍵字-{uuid.uuid4().hex[:6]}",
        description_markdown="這是一個測試關鍵字內容。",
        category_id=sample_category.id,
        author_id=sample_user.id,
    )
    db_session.add(keyword)
    db_session.commit()
    return keyword
