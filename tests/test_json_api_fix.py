"""Regression tests for JSON admin endpoints."""
from __future__ import annotations

from typing import Callable

import pytest

from app.models import LearningKeyword


def _login_client(client, user) -> None:
	with client.session_transaction() as session:
		session["_user_id"] = str(user.id)
		session["user_id"] = str(user.id)
		session["_fresh"] = True


@pytest.fixture()
def login(client) -> Callable:
	def _login(user) -> None:
		_login_client(client, user)

	return _login


def test_admin_required_returns_json_forbidden(client, auth_user, login):
	login(auth_user)

	response = client.post(
		"/admin/categories",
		headers={"Accept": "application/json"},
		follow_redirects=False,
	)

	assert response.status_code == 403
	payload = response.get_json()
	assert payload == {"success": False, "message": "需要管理員權限"}


def test_regenerate_keyword_seo_returns_payload(
	client, db_session, sample_category, sample_user, login
):
	keyword = LearningKeyword(
		title="測試關鍵字",
		slug="test-keyword",
		description_markdown="內容",
		category_id=sample_category.id,
		author_id=sample_user.id,
		seo_auto_generate=False,
	)
	db_session.add(keyword)
	db_session.commit()

	login(sample_user)

	response = client.post(f"/admin/keywords/{keyword.id}/regenerate-seo")
	assert response.status_code == 200
	payload = response.get_json()
	assert payload["success"] is True
	assert "SEO 內容已重新生成" in payload["message"]
	assert "測試關鍵字" in payload["seo_content"]
