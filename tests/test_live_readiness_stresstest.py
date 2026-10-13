import pytest
import re
from fastapi.testclient import TestClient
from main import app
import security
import os

client = TestClient(app)

def test_landing_page_status_and_headers():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    html = response.text
    
    # 1. Dual audience funnel checks
    assert "hero-tab-practice" in html
    assert "hero-tab-soletrader" in html
    assert "Zero-Cost Receipt Capture" in html
    assert "Straight to Xero Draft Bills" in html
    assert "setHeroAudience" in html
    
    # 2. Trust strip checks
    assert "Xero Ecosystem" in html
    assert "ICAEW &amp; ACCA" in html or "ICAEW & ACCA" in html
    assert "eu-west-2" in html
    assert "Notice 700/22" in html
    assert "Zero LLM Model Training" in html or "Zero Model Training" in html
    
    # 3. Xero Draft Bill recreation checks
    assert "Bills to Pay" in html and "STATUS: DRAFT" in html
    assert "WA-COSTA-914" in html
    assert "BIM45014" in html
    assert "424 - Rent" in html
    assert "429 - Entertain." in html
    
    # 4. Practice calculator & commercial model
    assert "The £0 Practice Platform Model" in html or "calc-client-display" in html
    assert "ICAEW &amp; ACCA Section 330 Aligned" in html or "ICAEW & ACCA Section 330 Aligned" in html or "Section 330" in html
    assert "calc-clients-slider" in html
    assert "updatePracticeCalculator" in html
    
    # 5. Statutory footer & pre-incorporation checks
    assert "FinTech Pilot Initiative" in html or "Pre-incorporation FinTech Pilot" in html
    assert "Schedule 24 FA 2007" in html or "Schedule 24 Finance Act 2007" in html
    assert "Taxes Management Act 1970 s12B" in html
    # Strict negative check: No false Ltd claims
    assert "Invisible Accountant Ltd" not in html
    assert "Registered in England & Wales" not in html

def test_audience_query_parameter_handling():
    resp_practice = client.get("/?audience=practice")
    assert resp_practice.status_code == 200
    resp_soletrader = client.get("/?audience=soletrader")
    assert resp_soletrader.status_code == 200

def test_partner_portal_routes():
    # 1. Partner Register Page
    reg_page = client.get("/partner/register")
    assert reg_page.status_code == 200
    assert "Register Your Accountancy Firm" in reg_page.text
    
    # 2. Partner Login Page
    login_page = client.get("/partner/login")
    assert login_page.status_code == 200
    assert "Practice Partner Sign In" in login_page.text
    
    # 3. Unauthorized access to Partner Dashboard
    unauth_dash = client.get("/partner/dashboard", follow_redirects=False)
    assert unauth_dash.status_code in [302, 303, 307]
    assert "/partner/login" in unauth_dash.headers.get("location", "")

def test_accountant_review_dashboard_auth():
    # 1. Login page accessible
    login_page = client.get("/dashboard/login")
    assert login_page.status_code == 200
    assert "Accountant Portal" in login_page.text or "Practice API Key" in login_page.text
    
    # 2. Unauthorized browser request (Accept: text/html) redirects to login
    unauth_browser = client.get("/dashboard", headers={"Accept": "text/html"}, follow_redirects=False)
    assert unauth_browser.status_code == 303
    assert "/dashboard/login" in unauth_browser.headers.get("location", "")
    
    # 3. Unauthorized API request returns 401
    unauth_api = client.get("/dashboard", headers={"Accept": "application/json"}, follow_redirects=False)
    assert unauth_api.status_code == 401
    
    # 4. Authorized access via API Key header
    auth_key = security.API_KEY
    from unittest.mock import patch, AsyncMock
    with patch("dashboard.get_connection") as mock_conn:
        mock_ctx = AsyncMock()
        mock_conn.return_value.__aenter__.return_value = mock_ctx
        mock_ctx.fetch.return_value = []
        mock_ctx.fetchval.return_value = 0
        auth_dash = client.get("/dashboard", headers={"X-API-Key": auth_key})
        assert auth_dash.status_code == 200
        assert "Review Queue" in auth_dash.text or "Dashboard" in auth_dash.text or "Glass Ledger" in auth_dash.text

def test_whatsapp_simulation_api():
    from unittest.mock import patch, AsyncMock
    with patch("main.create_chat_session", new_callable=AsyncMock) as mock_create, \
         patch("db.push_intake_queue", new_callable=AsyncMock) as mock_push:
        mock_create.return_value = 12345
        resp = client.post("/api/simulate_whatsapp", json={
            "sender_id": "demo_web_stress_user_1",
            "message": "£4.50 coffee at Starbucks",
            "turn_count": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "success"
        assert data.get("chat_id") == 12345

def test_static_and_legal_pages():
    for route in ["/terms", "/privacy", "/accessibility"]:
        resp = client.get(route)
        assert resp.status_code == 200
        # Verify no false Ltd claims
        assert "Invisible Accountant Ltd" not in resp.text
        assert "Registered in England & Wales" not in resp.text
