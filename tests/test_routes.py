"""API tests changes. Covers: URL validation/normalization at the API boundary, Pydantic response
models, and the ON DELETE CASCADE schema fix for deleting clicked URLs.
"""

import pytest


def test_register_and_login(client):
    resp = client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "pw123456"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"message": "User registered successfully"}

    resp = client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "pw123456"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"


def test_create_url_returns_full_response_model(client, make_user):
    auth = make_user("alice", "alice@example.com")
    resp = client.post(
        "/urls", json={"original_url": "https://example.com/page?a=1"}, headers=auth
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body) == {"id", "short_code", "original_url", "click_count", "created_at"}
    assert body["original_url"] == "https://example.com/page?a=1"
    assert body["click_count"] == 0
    assert len(body["short_code"]) == 6
    assert body["id"] > 0
    assert body["created_at"]


@pytest.mark.parametrize(
    "bare,normalized",
    [
        ("example.com", "https://example.com"),
        ("http://example.com/x", "http://example.com/x"),
        ("HTTPS://Example.COM/Path", "https://example.com/Path"),
    ],
)
def test_create_url_normalizes_input(client, make_user, bare, normalized):
    auth = make_user("alice", "alice@example.com")
    resp = client.post("/urls", json={"original_url": bare}, headers=auth)
    assert resp.status_code == 200, resp.text
    assert resp.json()["original_url"] == normalized


@pytest.mark.parametrize(
    "bad_url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "ftp://example.com/file",
        "https://",
        "not a url",
    ],
)
def test_create_url_rejects_invalid_urls(client, make_user, bad_url):
    auth = make_user("alice", "alice@example.com")
    resp = client.post("/urls", json={"original_url": bad_url}, headers=auth)
    assert resp.status_code == 422, resp.text


def test_create_url_requires_auth(client):
    resp = client.post("/urls", json={"original_url": "https://example.com"})
    assert resp.status_code == 401


def test_list_urls_uses_response_model(client, make_user):
    auth = make_user("alice", "alice@example.com")
    client.post("/urls", json={"original_url": "https://a.example.com"}, headers=auth)
    client.post("/urls", json={"original_url": "https://b.example.com"}, headers=auth)

    resp = client.get("/urls", headers=auth)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    for entry in body:
        assert set(entry) == {"id", "short_code", "original_url", "click_count", "created_at"}


def test_redirect_records_click_and_counter_together(client, make_user):
    auth = make_user("alice", "alice@example.com")
    created = client.post(
        "/urls", json={"original_url": "https://example.com/dest"}, headers=auth
    ).json()

    resp = client.get(f"/{created['short_code']}", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com/dest"

    listed = client.get("/urls", headers=auth).json()
    assert listed[0]["click_count"] == 1

    summary = client.get(
        f"/urls/{created['id']}/analytics/summary", headers=auth
    ).json()
    assert summary["total_clicks"] == 1
    assert summary["first_click"] is not None
    assert summary["last_click"] is not None


def test_delete_url_with_clicks_succeeds(client, make_user):
    """Regression: clicks.url_id is ON DELETE CASCADE, so deleting a URL that
    has recorded clicks used to raise IntegrityError -> 500."""
    auth = make_user("alice", "alice@example.com")
    created = client.post(
        "/urls", json={"original_url": "https://example.com"}, headers=auth
    ).json()
    client.get(f"/{created['short_code']}", follow_redirects=False)

    resp = client.delete(f"/urls/{created['id']}", headers=auth)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"message": "URL deleted successfully"}
    assert client.get("/urls", headers=auth).json() == []


def test_analytics_endpoints_use_response_models(client, make_user):
    auth = make_user("alice", "alice@example.com")
    created = client.post(
        "/urls", json={"original_url": "https://example.com"}, headers=auth
    ).json()

    # Empty analytics still validates against the response models.
    summary = client.get(f"/urls/{created['id']}/analytics/summary", headers=auth)
    assert summary.status_code == 200
    assert set(summary.json()) == {"url_id", "total_clicks", "first_click", "last_click"}
    assert summary.json()["total_clicks"] == 0
    assert client.get(f"/urls/{created['id']}/analytics/daily", headers=auth).json() == []

    client.get(f"/{created['short_code']}", follow_redirects=False)
    client.get(f"/{created['short_code']}", follow_redirects=False)

    daily = client.get(f"/urls/{created['id']}/analytics/daily", headers=auth)
    assert daily.status_code == 200
    points = daily.json()
    assert len(points) == 1
    assert set(points[0]) == {"date", "clicks"}
    assert points[0]["clicks"] == 2


def test_duplicate_email_rejected(client, make_user):
    make_user("alice", "alice@example.com")
    resp = client.post(
        "/auth/register",
        json={"username": "alice2", "email": "alice@example.com", "password": "pw123456"},
    )
    assert resp.status_code == 400
