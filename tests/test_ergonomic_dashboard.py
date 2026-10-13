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
