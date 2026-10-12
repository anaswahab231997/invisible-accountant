import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app

TEST_API_KEY = "test-fintech-secure-key-998877"

@pytest.fixture(autouse=True)
def set_env_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    import security
    monkeypatch.setattr(security, "API_KEY", TEST_API_KEY)

@pytest.fixture
def client():
    # follow_redirects=False to verify 303 Redirect responses and Location headers
    return TestClient(app, follow_redirects=False)

# ==============================================================================
# 1. Unauthenticated Access Protection Tests
# ==============================================================================

def test_unauthenticated_browser_navigation_redirects(client):
    """Browser navigation with Accept: text/html must redirect (303) to /dashboard/login?next=..."""
    response = client.get("/dashboard", headers={"Accept": "text/html,application/xhtml+xml"})
    assert response.status_code == 303
    assert response.headers["Location"] == "/dashboard/login?next=/dashboard"

def test_unauthenticated_api_request_returns_401(client):
    """API request with JSON or standard Accept must return 401 Unauthorized."""
    response = client.get("/dashboard", headers={"Accept": "application/json"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}

def test_unauthenticated_htmx_request_returns_401(client):
    """HTMX request with HX-Request: true must return 401 Unauthorized even if Accept contains text/html."""
    response = client.get(
        "/dashboard",
        headers={"Accept": "text/html", "HX-Request": "true"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}

@pytest.mark.parametrize("route,method", [
    ("/dashboard/edit/ledger/1", "GET"),
    ("/dashboard/triage/ledger/1", "POST"),
    ("/dashboard/reject/ledger/1", "POST"),
    ("/dashboard/approve/1", "POST"),
    ("/dashboard/edit/1", "GET"),
    ("/dashboard/bulk-approve", "POST"),
])
def test_all_dashboard_routes_protected_against_unauthenticated_access(client, route, method):
    """Verify that every single triage / edit / approve route rejects unauthenticated calls with 401."""
    if method == "GET":
        resp = client.get(route, headers={"HX-Request": "true"})
    else:
        resp = client.post(route, headers={"HX-Request": "true"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Authentication required"}

# ==============================================================================
# 2. Dual-Auth & Magic Link Verification Tests
# ==============================================================================

@patch("dashboard.get_connection")
def test_authenticated_via_cookie(mock_conn, client):
    """Authenticated via HTTP cookie accountant_session."""
    mock_db = AsyncMock()
    mock_db.fetch.return_value = []
    mock_db.fetchval.return_value = 0
    mock_conn.return_value.__aenter__.return_value = mock_db

    response = client.get(
        "/dashboard",
        cookies={"accountant_session": TEST_API_KEY},
        headers={"Accept": "text/html"}
    )
    assert response.status_code == 200
    assert "Accountant Triage" in response.text

@patch("dashboard.get_connection")
def test_authenticated_via_header(mock_conn, client):
    """Authenticated via HTTP header X-API-Key."""
    mock_db = AsyncMock()
    mock_db.fetch.return_value = []
    mock_db.fetchval.return_value = 0
    mock_conn.return_value.__aenter__.return_value = mock_db

    response = client.get(
        "/dashboard",
        headers={"X-API-Key": TEST_API_KEY, "Accept": "text/html"}
    )
    assert response.status_code == 200
    assert "Accountant Triage" in response.text

@patch("dashboard.get_connection")
def test_authenticated_via_magic_link_sets_cookie(mock_conn, client):
    """Magic link ?key=... authenticates and instructs route to set accountant_session cookie."""
    mock_db = AsyncMock()
    mock_db.fetch.return_value = []
    mock_db.fetchval.return_value = 0
    mock_conn.return_value.__aenter__.return_value = mock_db

    response = client.get(
        f"/dashboard?key={TEST_API_KEY}",
        headers={"Accept": "text/html"}
    )
    assert response.status_code == 200
    assert "set-cookie" in response.headers
    cookie_header = response.headers["set-cookie"]
    assert "accountant_session=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
    assert "Secure" in cookie_header
    assert "Max-Age=604800" in cookie_header

# ==============================================================================
# 3. Login & Logout Route Tests
# ==============================================================================

def test_get_login_page_unauthenticated(client):
    """GET /dashboard/login renders login template when unauthenticated."""
    response = client.get("/dashboard/login")
    assert response.status_code == 200
    assert "Accountant Portal" in response.text
    assert "access_key" in response.text

def test_get_login_page_already_authenticated_redirects(client):
    """GET /dashboard/login redirects to /dashboard if already authenticated."""
    response = client.get(
        "/dashboard/login",
        cookies={"accountant_session": TEST_API_KEY}
    )
    assert response.status_code == 303
    assert response.headers["Location"] == "/dashboard"

def test_post_login_invalid_key_renders_error(client):
    """POST /dashboard/login with invalid key returns 401 and error message."""
    response = client.post(
        "/dashboard/login",
        data={"access_key": "wrong-key", "next": "/dashboard"}
    )
    assert response.status_code == 401
    assert "Invalid API access key" in response.text

def test_post_login_valid_key_sets_cookie_and_redirects(client):
    """POST /dashboard/login with valid key sets secure cookie and redirects (303)."""
    response = client.post(
        "/dashboard/login",
        data={"access_key": TEST_API_KEY, "next": "/dashboard?tab=capital_allowances"}
    )
    assert response.status_code == 303
    assert response.headers["Location"] == "/dashboard?tab=capital_allowances"
    assert "set-cookie" in response.headers
    cookie_header = response.headers["set-cookie"]
    assert f"accountant_session={TEST_API_KEY}" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
    assert "Secure" in cookie_header
    assert "Max-Age=604800" in cookie_header

def test_get_logout_clears_cookie_and_redirects(client):
    """GET /dashboard/logout deletes accountant_session cookie and redirects to /dashboard/login."""
    response = client.get("/dashboard/logout")
    assert response.status_code == 303
    assert response.headers["Location"] == "/dashboard/login"
    assert "set-cookie" in response.headers
    cookie_header = response.headers["set-cookie"]
    assert "accountant_session=" in cookie_header
    assert "Max-Age=0" in cookie_header

if __name__ == "__main__":
    pytest.main(["-v", __file__])
