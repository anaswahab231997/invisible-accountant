import pytest
from httpx import AsyncClient, ASGITransport
from main import app
import os

@pytest.mark.asyncio
async def test_dashboard_high_density_rendering():
    """Verify that dashboard renders with 30px high-density ledger table and hotkeys.js."""
    api_key = os.getenv("API_KEY", "super-secret-key")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Request dashboard with authentication
        resp = await ac.get(f"/dashboard?key={api_key}")
        assert resp.status_code == 200
        html = resp.text
        
        # Verify 30px high-density mode and hotkeys.js script
        assert "hotkeys.js" in html
        assert "30px High-Density Mode" in html
        assert "inspect-drawer" in html
        assert "drawer-overlay" in html
        assert "tabular-nums" in html
        assert "High-Density 30px Ledger Engine Active" in html
        assert ("triage-row" in html or "Review Queue Clear" in html)

@pytest.mark.asyncio
async def test_inspect_drawer_unauthenticated():
    """Verify that unauthenticated access to /dashboard/inspect redirects or is blocked."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/dashboard/inspect/ledger/1")
        # Should redirect to login or require auth
        assert resp.status_code in (303, 401)

@pytest.mark.asyncio
async def test_inspect_drawer_authenticated():
    """Verify authenticated access to /dashboard/inspect returns drawer content with controls."""
    api_key = os.getenv("API_KEY", "super-secret-key")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/dashboard/inspect/ledger/99999?key={api_key}")
        # Even if record doesn't exist, it gracefully renders default drawer view with status 200
        assert resp.status_code == 200
        html = resp.text
        assert "WhatsApp Client Intake Memo" in html
        assert "Tax &amp; Compliance Audit Memo" in html
        assert "Xero Nominal Code" in html
        assert "VAT Treatment" in html
        assert "Approve &amp; Push to Xero" in html
