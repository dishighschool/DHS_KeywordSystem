"""Basic smoke tests for public routes."""
from __future__ import annotations


def test_index_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_category_not_found(client):
    response = client.get("/unknown-category")
    assert response.status_code == 404


def test_keyword_not_found(client):
    response = client.get("/unknown-category/unknown-keyword")
    assert response.status_code == 404
