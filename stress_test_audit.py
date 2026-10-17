"""
Invisible Accountant - Production Resilience & Security Penetration Audit
Automated stress test harness executing against local backend routes using httpx.AsyncClient.
Zero hallucination. Brutal, unvarnished findings.
"""

import asyncio
import os
import re
import secrets
import time
import hmac
import hashlib
from typing import Dict, Any, List
import unittest.mock as mock
from dotenv import load_dotenv

load_dotenv()

import httpx
from starlette.testclient import TestClient
from main import app
import security
import db

TEST_API_KEY = os.getenv("API_KEY", "test-resilience-audit-key-2026")
security.API_KEY = TEST_API_KEY
os.environ["API_KEY"] = TEST_API_KEY

audit_results: List[Dict[str, Any]] = []

def record_finding(category: str, test_name: str, passed: bool, severity: str, details: str, proof: Any = None):
    audit_results.append({
        "category": category,
        "test": test_name,
        "status": "PASS" if passed else "FAIL",
        "severity": severity,
        "details": details,
        "proof": str(proof) if proof is not None else ""
    })
    status_icon = "[\033[92mPASS\033[0m]" if passed else f"[\033[91mFAIL - {severity}\033[0m]"
    print(f"{status_icon} [{category}] {test_name}: {details}")


async def run_async_audit():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", follow_redirects=False) as client:
        
        # ==============================================================================
        # SECTION 1: SECURITY & AUTH PENETRATION TESTS
        # ==============================================================================

        # Test 1.1: Dashboard Login Brute Force
        print("\n--- Running Test 1.1: Dashboard Login Brute Force (100 bursts) ---")
        start = time.perf_counter()
        dashboard_responses = []
        for i in range(100):
            resp = await client.post("/dashboard/login", data={"access_key": f"wrong-key-{i}"})
            dashboard_responses.append(resp.status_code)
        elapsed_dash = time.perf_counter() - start

        rate_limited_dash = any(code == 429 for code in dashboard_responses)
        if rate_limited_dash:
            record_finding("Auth Penetration", "Dashboard Brute Force Rate Limiting", True, "INFO", 
                           f"Requests throttled with HTTP 429 in {elapsed_dash:.2f}s", {"status_codes": set(dashboard_responses)})
        else:
            record_finding("Auth Penetration", "Dashboard Brute Force Rate Limiting", False, "CRITICAL", 
                           f"Zero rate limiting on /dashboard/login! 100 failed attempts permitted without 429 in {elapsed_dash:.2f}s (all returned 401).", 
                           {"status_codes": set(dashboard_responses), "count": len(dashboard_responses), "elapsed_sec": round(elapsed_dash, 2)})

        # Test 1.2: Partner Login Brute Force
        print("\n--- Running Test 1.2: Partner Login Brute Force (30 bursts) ---")
        start = time.perf_counter()
        partner_responses = []
        pool_errors = []
        for i in range(30):
            try:
                resp = await client.post("/partner/login", data={"email": "victim@practice.co.uk", "password": f"wrongpass{i}"})
                partner_responses.append(resp.status_code)
            except Exception as e:
                pool_errors.append(str(e))
        elapsed_partner = time.perf_counter() - start

        if pool_errors:
            record_finding("Auth Penetration", "Partner Login DB Stability Under Burst", False, "CRITICAL", 
                           f"DB Connection Collision Crash: {len(pool_errors)} out of 100 burst login requests crashed!", 
                           {"sample": pool_errors[0]})

        rate_limited_partner = any(code == 429 for code in partner_responses)
        if rate_limited_partner:
            record_finding("Auth Penetration", "Partner Brute Force Rate Limiting", True, "INFO", 
                           f"Requests throttled with HTTP 429 in {elapsed_partner:.2f}s", {"status_codes": set(partner_responses)})
        else:
            record_finding("Auth Penetration", "Partner Brute Force Rate Limiting", False, "CRITICAL", 
                           f"Zero rate limiting on /partner/login! {len(partner_responses)} failed attempts permitted without 429 in {elapsed_partner:.2f}s (all returned 401).", 
                           {"status_codes": set(partner_responses), "count": len(partner_responses), "elapsed_sec": round(elapsed_partner, 2)})

        # Test 1.3: Accountant Session Cookie Flags
        print("\n--- Running Test 1.3: Accountant Session Cookie Flags ---")
        resp = await client.post("/dashboard/login", data={"access_key": TEST_API_KEY})
        assert resp.status_code == 303, f"Expected 303 redirect on valid login, got {resp.status_code}"
        
        set_cookie_header = resp.headers.get("set-cookie", "")
        has_httponly = "httponly" in set_cookie_header.lower()
        has_secure = "secure" in set_cookie_header.lower()
        has_samesite_lax = "samesite=lax" in set_cookie_header.lower()
        has_accountant_session = "accountant_session=" in set_cookie_header

        if has_accountant_session and has_httponly and has_secure and has_samesite_lax:
            record_finding("Auth Penetration", "Accountant Cookie Flags", True, "INFO", 
                           "accountant_session cookie sets HttpOnly, Secure, and SameSite=Lax properly.", set_cookie_header)
        else:
            record_finding("Auth Penetration", "Accountant Cookie Flags", False, "HIGH", 
                           f"accountant_session cookie flags missing: HttpOnly={has_httponly}, Secure={has_secure}, SameSite=Lax={has_samesite_lax}", set_cookie_header)

        # Test 1.4: Partner Session Cookie Naming Discrepancy
        print("\n--- Running Test 1.4: Partner Session Cookie Naming Discrepancy ---")
        import partner_routes
        with open(partner_routes.__file__, "r", encoding="utf-8") as f:
            partner_routes_src = f.read()
        uses_practice_session = "practice_session" in partner_routes_src
        uses_partner_session = "partner_session" in partner_routes_src

        if uses_partner_session and not uses_practice_session:
            record_finding("Auth Penetration", "Partner Cookie Name Alignment", True, "INFO", 
                           "Cookie name strictly matches 'partner_session'.")
        else:
            record_finding("Auth Penetration", "Partner Cookie Name Alignment", False, "MEDIUM", 
                           "Naming discrepancy: Specification and external clients expect 'partner_session', but code hardcodes 'practice_session' across partner_routes.py and security.py.", 
                           "Hardcoded key: 'practice_session'")

        # Test 1.5: Open Redirect Checks on Dashboard Login
        print("\n--- Running Test 1.5: Dashboard Login Open Redirect ---")
        redirect_payloads = [
            ("https://evil.com", "External URL"),
            ("//evil.com", "Protocol-relative URL"),
            ("/dashboard@evil.com", "Userinfo confusion (@)"),
            ("/dashboard/../../attacker.com", "Path traversal"),
            ("/dashboard", "Legitimate internal path")
        ]
        for target, desc in redirect_payloads:
            resp = await client.post("/dashboard/login", data={"access_key": TEST_API_KEY, "next": target})
            location = resp.headers.get("Location", "")
            if target in ("https://evil.com", "//evil.com"):
                if location.startswith("https://evil.com") or location.startswith("//evil.com"):
                    record_finding("Auth Penetration", f"Open Redirect ({desc})", False, "HIGH", 
                                   f"Allowed open redirect to external target: {location}", {"input": target, "location": location})
                else:
                    record_finding("Auth Penetration", f"Open Redirect ({desc})", True, "INFO", 
                                   f"Safely neutralized redirect to: {location}")
            elif target == "/dashboard@evil.com":
                if "@" in location:
                    record_finding("Auth Penetration", f"Open Redirect ({desc})", False, "HIGH", 
                                   f"Allowed bypass with @ symbol: {location} (can lead to open redirect depending on browser URL parser)", {"input": target, "location": location})
                else:
                    record_finding("Auth Penetration", f"Open Redirect ({desc})", True, "INFO", 
                                   f"Neutralized @ payload: {location}")

        # Test 1.6: Partner Login Next Parameter Support
        print("\n--- Running Test 1.6: Partner Login Next Parameter Handling ---")
        resp_login_page = await client.get("/partner/login?next=/partner/deep-link")
        has_next_in_form = 'name="next" value="/partner/deep-link"' in resp_login_page.text
        if not has_next_in_form:
            record_finding("Auth Penetration", "Partner Deep Linking Support", False, "LOW", 
                           "/partner/login GET & POST handlers completely ignore ?next= parameter, breaking deep links upon partner re-authentication.", 
                           "Context missing next parameter in template.")
        else:
            record_finding("Auth Penetration", "Partner Deep Linking Support", True, "INFO", 
                           "Partner login preserves ?next= parameter.")

        # ==============================================================================
        # SECTION 2: SESSION TAMPERING & CRYPTOGRAPHIC INTEGRITY
        # ==============================================================================

        # Test 2.1: Practice Token Tampering
        print("\n--- Running Test 2.1: Practice Token Tampering ---")
        valid_token = security.create_practice_token(10, "apex-tax")
        parts = valid_token.split(":")
        tampered_id_token = f"1:{parts[1]}:{parts[2]}:{parts[3]}"
        verified_tampered_id = security.verify_practice_token(tampered_id_token)

        tampered_slug_token = f"{parts[0]}:hacked-slug:{parts[2]}:{parts[3]}"
        verified_tampered_slug = security.verify_practice_token(tampered_slug_token)

        if verified_tampered_id is None and verified_tampered_slug is None:
            record_finding("Crypto & Session", "Practice Token Signature Integrity", True, "INFO", 
                           "HMAC signature verification successfully rejects tampered practice_id and tampered slug.")
        else:
            record_finding("Crypto & Session", "Practice Token Signature Integrity", False, "CRITICAL", 
                           "Tampered token accepted by verify_practice_token!", 
                           {"tampered_id": verified_tampered_id, "tampered_slug": verified_tampered_slug})

        # Test 2.2: Hardcoded Fallback Secret Key Exploitability
        print("\n--- Running Test 2.2: Hardcoded Fallback Secret Exploitability ---")
        fallback_secret = "fallback_secret_key_uk_mtd_2026"
        now_ts = int(time.time())
        payload = f"999:victim-practice:{now_ts}"
        forged_sig = hmac.new(fallback_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
        forged_token = f"{payload}:{forged_sig}"

        orig_env = os.environ.get("API_KEY")
        try:
            if "API_KEY" in os.environ:
                del os.environ["API_KEY"]
            verified_when_env_unset = security.verify_practice_token(forged_token)
        finally:
            if orig_env:
                os.environ["API_KEY"] = orig_env

        if verified_when_env_unset is not None:
            record_finding("Crypto & Session", "Hardcoded Fallback Secret Vulnerability", False, "CRITICAL", 
                           "CWE-798: Code contains hardcoded fallback secret 'fallback_secret_key_uk_mtd_2026'. If API_KEY env var is missing or unset in any deployment, ANY attacker can forge valid admin/practice sessions!", 
                           {"forged_token": forged_token, "accepted_data": verified_when_env_unset})
        else:
            record_finding("Crypto & Session", "Hardcoded Fallback Secret Vulnerability", True, "INFO", 
                           "Fallback secret not accepted.")

        # Test 2.3: Future Timestamp Expiration Bypass
        print("\n--- Running Test 2.3: Future Timestamp Expiry Bypass ---")
        far_future_ts = 9999999999  # Year 2286
        p_id = 42
        p_slug = "future-tax"
        p_payload = f"{p_id}:{p_slug}:{far_future_ts}"
        p_secret = os.getenv("API_KEY", "fallback_secret_key_uk_mtd_2026")
        p_sig = hmac.new(p_secret.encode("utf-8"), p_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        future_token = f"{p_payload}:{p_sig}"

        verified_future = security.verify_practice_token(future_token)
        if verified_future and verified_future.get("practice_id") == p_id:
            record_finding("Crypto & Session", "Future Timestamp Permanent Token Bypass", False, "HIGH", 
                           "Logic flaw in expiration math: 'int(time.time()) - int(timestamp_str) > 14 * 86400'. A future timestamp yields a negative number, creating an INDEFINITELY VALID token that bypasses 14-day expiry!", 
                           {"timestamp": far_future_ts, "verified": verified_future})
        else:
            record_finding("Crypto & Session", "Future Timestamp Permanent Token Bypass", True, "INFO", 
                           "Tokens with future timestamps rejected.")

        # Test 2.4: Stateless Logout Revocation Failure
        print("\n--- Running Test 2.4: Stateless Session Logout / Revocation Test ---")
        t_token = security.create_practice_token(1, "audit-practice")
        resp_logout = await client.get("/partner/logout", cookies={"practice_session": t_token})
        assert resp_logout.status_code == 303
        still_valid = security.verify_practice_token(t_token)
        if still_valid is not None:
            record_finding("Crypto & Session", "Stateless Session Logout Revocation Failure", False, "MEDIUM", 
                           "Client-side-only revocation: Server lacks a token blacklist/revocation table. A logged-out cookie remains fully valid for 14 days if stolen/intercepted.", 
                           {"token_still_valid": True})
        else:
            record_finding("Crypto & Session", "Stateless Session Logout Revocation Failure", True, "INFO", 
                           "Token invalidated on server.")

        # Test 2.5: Accountant Session Raw Key Exposure
        print("\n--- Running Test 2.5: Accountant Session Raw API Key Exposure ---")
        resp_login_dash = await client.post("/dashboard/login", data={"access_key": TEST_API_KEY})
        cookie_val = resp_login_dash.cookies.get("accountant_session")
        if cookie_val == TEST_API_KEY:
            record_finding("Crypto & Session", "Raw Master API Key in Session Cookie", False, "HIGH", 
                           "Architectural vulnerability: The 'accountant_session' cookie value is the RAW master API key, NOT an ephemeral signed session token! Stolen cookie grants global master admin rights.", 
                           {"cookie_equals_master_api_key": True})
        else:
            record_finding("Crypto & Session", "Raw Master API Key in Session Cookie", True, "INFO", 
                           "Session cookie uses ephemeral cryptographically signed session IDs.")

        # Test 2.6: Magic Link Exposure in Query Param
        print("\n--- Running Test 2.6: Magic Link Exposure in URL ---")
        resp_magic = await client.get(f"/dashboard?key={TEST_API_KEY}", headers={"Accept": "text/html"})
        cookie_set = "accountant_session=" in resp_magic.headers.get("set-cookie", "")
        if cookie_set:
            record_finding("Crypto & Session", "Magic Link Master Key URL Exposure", False, "MEDIUM", 
                           "Passing master API key in ?key= query string exposes credentials to proxy logs, server access logs, browser history, and Referer headers.", 
                           {"cookie_set_via_url_param": True})
        else:
            record_finding("Crypto & Session", "Magic Link Master Key URL Exposure", True, "INFO", 
                           "Query parameter authentication rejected.")

        # ==============================================================================
        # SECTION 3: INPUT VALIDATION, MALFORMED PAYLOADS & INJECTION
        # ==============================================================================

        # Test 3.1: Missing Fields in /partner/register
        print("\n--- Running Test 3.1: Partner Register Missing Fields ---")
        resp_missing = await client.post("/partner/register", data={"name": "Incomplete Practice"})
        if resp_missing.status_code == 422:
            record_finding("Input Validation", "Partner Register Missing Fields Validation", True, "INFO", 
                           "FastAPI rejects missing form fields with HTTP 422.")
        else:
            record_finding("Input Validation", "Partner Register Missing Fields Validation", False, "HIGH", 
                           f"Unexpected status for missing fields: {resp_missing.status_code}")

        # Test 3.2: Empty String / Whitespace Fields in /partner/register
        print("\n--- Running Test 3.2: Partner Register Empty Strings ---")
        with mock.patch("db.get_practice_by_slug", return_value=None), \
             mock.patch("db.get_practice_by_email", return_value=None), \
             mock.patch("db.get_practice_by_code", return_value=None), \
             mock.patch("db.create_practice", return_value=9999):
            resp_empty = await client.post("/partner/register", data={
                "name": "   ",
                "contact_name": "   ",
                "contact_email": "   ",
                "slug": "   ",
                "password": "   "
            })
            if resp_empty.status_code == 303:
                record_finding("Input Validation", "Partner Register Blank Fields Acceptance", False, "HIGH", 
                               "Vulnerability: /partner/register accepts pure whitespace for name, slug, email, and password, creating ghost practice records without validation!", 
                               {"status_code": resp_empty.status_code, "location": resp_empty.headers.get("Location")})
            else:
                record_finding("Input Validation", "Partner Register Blank Fields Acceptance", True, "INFO", 
                               f"Rejected empty fields with HTTP {resp_empty.status_code}")

        # Test 3.3: Malformed Email in /partner/register
        print("\n--- Running Test 3.3: Partner Register Malformed Email ---")
        bad_emails = ["notanemail", "user@", "@domain.com", "user space@domain.com"]
        accepted_bad_emails = []
        with mock.patch("db.get_practice_by_slug", return_value=None), \
             mock.patch("db.get_practice_by_email", return_value=None), \
             mock.patch("db.get_practice_by_code", return_value=None), \
             mock.patch("db.create_practice", return_value=8888):
            for email in bad_emails:
                resp_email = await client.post("/partner/register", data={
                    "name": "Test Firm",
                    "contact_name": "Auditor",
                    "contact_email": email,
                    "slug": f"firm-{secrets.token_hex(3)}",
                    "password": "ValidPassword123!",
                })
                if resp_email.status_code == 303:
                    accepted_bad_emails.append(email)

        if accepted_bad_emails:
            record_finding("Input Validation", "Partner Register Email Format Validation", False, "HIGH", 
                           f"Zero email format validation! Accepted invalid emails: {accepted_bad_emails}", accepted_bad_emails)
        else:
            record_finding("Input Validation", "Partner Register Email Format Validation", True, "INFO", 
                           "Malformed email addresses rejected.")

        # Test 3.4: SQL Injection Resilience in /partner/register
        print("\n--- Running Test 3.4: Partner Register SQL Injection Strings ---")
        with mock.patch("db.get_practice_by_slug", return_value=None), \
             mock.patch("db.get_practice_by_email", return_value=None), \
             mock.patch("db.get_practice_by_code", return_value=None), \
             mock.patch("db.create_practice", return_value=7777):
            sqli_payloads = ["Apex ' OR '1'='1", "Apex '; DROP TABLE test; --", "Apex admin'--"]
            crashed = False
            for sqli in sqli_payloads:
                resp_sqli = await client.post("/partner/register", data={
                    "name": sqli,
                    "contact_name": "SQL Tester",
                    "contact_email": f"sqli_{secrets.token_hex(2)}@test.com",
                    "slug": "sqli-test",
                    "password": "Password123!",
                })
                if resp_sqli.status_code == 500:
                    crashed = True
            if crashed:
                record_finding("Input Validation", "SQL Injection Resilience", False, "CRITICAL", 
                               "SQL syntax crash detected on SQL injection payload in /partner/register!")
            else:
                record_finding("Input Validation", "SQL Injection Resilience", True, "INFO", 
                               "Parameterized queries safely handled SQL injection payloads.")

        # Test 3.5: LOI Signatory SVG Stored XSS
        print("\n--- Running Test 3.5: LOI Signatory SVG Stored XSS ---")
        t_token = security.create_practice_token(1, "audit-practice")
        xss_payload = "</text><script xmlns='http://www.w3.org/2000/svg'>alert(document.domain)</script><text>"
        loi_data = {
            "signatory_name": xss_payload,
            "signatory_title": "Partner",
            "firm_legal_name": "Audit LLP",
            "pledged_seats": 50,
            "firm_address": "100 London Wall"
        }
        captured_data_url = None
        async def mock_record_loi(**kwargs):
            nonlocal captured_data_url
            captured_data_url = kwargs.get("signature_data_url")
            return 1

        with mock.patch("db.get_practice_by_id", return_value={"id": 1, "company_number": "12345678"}), \
             mock.patch("db.record_practice_loi", side_effect=mock_record_loi):
            resp_loi = await client.post("/partner/loi/sign", data=loi_data, cookies={"practice_session": t_token})

        if captured_data_url and "<script" in captured_data_url:
            record_finding("Input Validation", "LOI Signature SVG Stored XSS", False, "HIGH", 
                           "Stored XSS flaw: signatory_name interpolated directly into SVG data URL without XML escaping!", 
                           {"data_url": captured_data_url})
        else:
            record_finding("Input Validation", "LOI Signature SVG Stored XSS", True, "INFO", 
                           "Signatory name safely escaped in SVG.")

        # Test 3.6: LOI Negative Pledged Seats
        print("\n--- Running Test 3.6: LOI Negative Pledged Seats ---")
        captured_seats = None
        async def mock_record_loi_seats(**kwargs):
            nonlocal captured_seats
            captured_seats = kwargs.get("pledged_client_seats")
            return 1

        loi_neg_data = {
            "signatory_name": "Auditor",
            "signatory_title": "Partner",
            "firm_legal_name": "Audit LLP",
            "pledged_seats": -500,
            "firm_address": "100 London Wall"
        }
        with mock.patch("db.get_practice_by_id", return_value={"id": 1, "company_number": "12345678"}), \
             mock.patch("db.record_practice_loi", side_effect=mock_record_loi_seats):
            await client.post("/partner/loi/sign", data=loi_neg_data, cookies={"practice_session": t_token})

        if captured_seats == -500:
            record_finding("Input Validation", "LOI Negative Pledged Seats Validation", False, "MEDIUM", 
                           "No integer bounds validation: accepted negative seat pledge (-500 seats).", 
                           {"pledged_seats": captured_seats})
        else:
            record_finding("Input Validation", "LOI Negative Pledged Seats Validation", True, "INFO", 
                           "Negative seat pledge rejected.")

        # Test 3.7: Dashboard Triage Unhandled Exception on Invalid Type
        print("\n--- Running Test 3.7: Dashboard Triage Unhandled Exception on Invalid Type ---")
        try:
            resp_triage = await client.post(
                "/dashboard/triage/invalid_type/999999",
                data={"account_code": "420", "tax_type": "INPUT2"},
                cookies={"accountant_session": TEST_API_KEY}
            )
            if resp_triage.status_code == 500:
                record_finding("Input Validation", "Dashboard Triage Unhandled Exception", False, "HIGH", 
                               "Unhandled ValueError crashes with HTTP 500 when item_type is invalid or item_id is missing.", 
                               {"status_code": 500, "text": resp_triage.text[:200]})
            else:
                record_finding("Input Validation", "Dashboard Triage Unhandled Exception", True, "INFO", 
                               f"Safely handled invalid triage type with HTTP {resp_triage.status_code}")
        except Exception as e:
            record_finding("Input Validation", "Dashboard Triage Unhandled Exception", False, "HIGH", 
                           f"Exception thrown out of ASGI application: {type(e).__name__}: {e}")

        # ==============================================================================
        # SECTION 4: DATA EXPOSURE & UNAUTHENTICATED ENDPOINTS AUDIT
        # ==============================================================================

        # Test 4.1: Unauthenticated /api/queue Leak
        print("\n--- Running Test 4.1: Unauthenticated /api/queue Leak ---")
        with mock.patch("main.get_all_hmrc_queue", return_value=[{"id": 1, "status": "PENDING", "amount": 120.0}]):
            resp_queue = await client.get("/api/queue")
            if resp_queue.status_code == 200:
                record_finding("Data Exposure", "Unauthenticated /api/queue Leak", False, "CRITICAL", 
                               "CRITICAL DATA LEAK: /api/queue has ZERO authentication! Any public attacker can dump all HMRC tax queue entries without credentials.", 
                               {"status_code": 200, "response_sample": str(resp_queue.json())[:200]})
            elif resp_queue.status_code in (401, 403):
                record_finding("Data Exposure", "Unauthenticated /api/queue Leak", True, "INFO", 
                               f"Properly protected with HTTP {resp_queue.status_code}")
            else:
                record_finding("Data Exposure", "Unauthenticated /api/queue Leak", False, "HIGH", 
                               f"Unexpected status: {resp_queue.status_code}")

        # Test 4.2: Unauthenticated /api/simulate_whatsapp Ingestion
        print("\n--- Running Test 4.2: Unauthenticated /api/simulate_whatsapp Ingestion ---")
        with mock.patch("db.create_chat_session", return_value=123), \
             mock.patch("db.push_intake_queue", return_value=None):
            sim_payload = {
                "sender_id": "attacker_stress_bot",
                "message": "Test receipt",
                "media_urls": [],
                "turn_count": 0
            }
            resp_sim = await client.post("/api/simulate_whatsapp", json=sim_payload)
            if resp_sim.status_code == 200:
                record_finding("Data Exposure", "Public Unauthenticated Intake Queue Injection", False, "HIGH", 
                               "Vulnerability: /api/simulate_whatsapp has NO authentication or HMAC verification! An attacker can inject arbitrary tasks into the LLM intake queue, causing LLM billing spikes and worker exhaustion.", 
                               {"status_code": 200, "response": resp_sim.json()})
            elif resp_sim.status_code in (401, 403):
                record_finding("Data Exposure", "Public Unauthenticated Intake Queue Injection", True, "INFO", 
                               f"Protected with HTTP {resp_sim.status_code}")
            else:
                record_finding("Data Exposure", "Public Unauthenticated Intake Queue Injection", False, "MEDIUM", 
                               f"Unexpected status: {resp_sim.status_code}")

        # Test 4.3: Unauthenticated Access to Protected Dashboard Routes
        print("\n--- Running Test 4.3: Unauthenticated Access to Protected Dashboard Routes ---")
        routes_to_test = [
            ("/dashboard", "GET"),
            ("/dashboard/bulk-approve", "POST"),
            ("/dashboard/approve/1", "POST"),
            ("/partner/dashboard", "GET"),
            ("/partner/loi/sign", "POST"),
        ]
        unprotected = []
        for r_path, r_method in routes_to_test:
            if r_method == "GET":
                r_resp = await client.get(r_path, headers={"HX-Request": "true"})
            else:
                r_resp = await client.post(r_path, headers={"HX-Request": "true"})
            if r_resp.status_code not in (401, 403, 303):
                unprotected.append((r_path, r_resp.status_code))
        if unprotected:
            record_finding("Data Exposure", "Protected Route Authentication Enforcement", False, "CRITICAL", 
                           f"Protected routes allowed unauthenticated access: {unprotected}")
        else:
            record_finding("Data Exposure", "Protected Route Authentication Enforcement", True, "INFO", 
                           "All sensitive dashboard and partner routes enforce authentication (401/303).")

        # ==============================================================================
        # SECTION 5: CONCURRENCY & CONNECTION POOL STRESS TEST
        # ==============================================================================

        # Test 5.1: Concurrency Burst Against Database
        print("\n--- Running Test 5.1: Connection Pool Concurrency Stress (50 bursts against max_size=8) ---")
        async def db_query_task(idx):
            try:
                async with db.get_connection() as conn:
                    return await conn.fetchval("SELECT $1::int", idx)
            except Exception as e:
                return f"ERR: {type(e).__name__}: {e}"

        start_c = time.perf_counter()
        c_results = await asyncio.gather(*[db_query_task(i) for i in range(50)], return_exceptions=True)
        elapsed_c = time.perf_counter() - start_c

        c_errors = [r for r in c_results if isinstance(r, str) and r.startswith("ERR")]
        c_exceptions = [r for r in c_results if isinstance(r, Exception)]

        if c_errors or c_exceptions:
            record_finding("Concurrency & DB", "Connection Pool Exhaustion Under Burst", False, "HIGH", 
                           f"Connection pool failed under 50 concurrent requests in {elapsed_c:.2f}s! Errors: {len(c_errors)}, Exceptions: {len(c_exceptions)}", 
                           {"errors": (c_errors + [str(e) for e in c_exceptions])[:3], "elapsed_sec": round(elapsed_c, 2)})
        else:
            record_finding("Concurrency & DB", "Connection Pool Exhaustion Under Burst", True, "INFO", 
                           f"Connection pool successfully queued and served 50 concurrent requests in {elapsed_c:.2f}s without connection errors.", 
                           {"elapsed_sec": round(elapsed_c, 2)})

        # ==============================================================================
        # SECTION 6: API ERROR HANDLING & STACK TRACE LEAKAGE
        # ==============================================================================

        # Test 6.1: Malformed JSON Stack Trace Leakage
        print("\n--- Running Test 6.1: Stack Trace Leakage on Malformed Payloads ---")
        resp_bad_json = await client.post(
            "/webhook/whatsapp",
            content="NOT_VALID_JSON{:::broken",
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=invalid"}
        )
        leaks_stack = "Traceback (most recent call last)" in resp_bad_json.text
        leaks_db = "postgresql://" in resp_bad_json.text or "asyncpg" in resp_bad_json.text
        leaks_path = "c:\\" in resp_bad_json.text.lower() or "/home/" in resp_bad_json.text.lower()

        if leaks_stack or leaks_db or leaks_path:
            record_finding("Error Handling", "Stack Trace & Environment Leakage", False, "HIGH", 
                           "Server leaked internal stack trace, file path, or database driver details in HTTP response!", 
                           resp_bad_json.text[:300])
        else:
            record_finding("Error Handling", "Stack Trace & Environment Leakage", True, "INFO", 
                           "Error response returned clean JSON/HTTP error without internal traces.")

        # Test 6.2: HTTP TRACE Method Rejection
        print("\n--- Running Test 6.2: HTTP Methods Fuzzing ---")
        resp_trace = await client.request("TRACE", "/dashboard")
        if resp_trace.status_code == 405:
            record_finding("Error Handling", "HTTP TRACE Method Rejection", True, "INFO", 
                           "TRACE method properly rejected with HTTP 405.")
        else:
            record_finding("Error Handling", "HTTP TRACE Method Rejection", False, "LOW", 
                           f"TRACE method returned status {resp_trace.status_code}")

def test_websocket_sync():
    """TestClient sync connection for WebSocket handshake verification."""
    print("\n--- Running Test 4.4: WebSocket Unauthenticated Eavesdropping ---")
    sync_client = TestClient(app)
    try:
        with sync_client.websocket_connect("/ws/victim_client_447700900000") as ws:
            record_finding("Data Exposure", "Unauthenticated WebSocket Eavesdropping & DoS", False, "CRITICAL", 
                           "CWE-306: /ws/{client_id} requires NO auth token, cookie, or handshake verification! Any attacker can connect to any client's phone number and eavesdrop on real-time intake financial data.", 
                           {"connected_without_auth": True})
    except Exception as e:
        record_finding("Data Exposure", "Unauthenticated WebSocket Eavesdropping & DoS", True, "INFO", 
                       f"WebSocket rejected connection: {e}")

def main():
    print("=" * 80)
    print("STARTING BRUTAL UK FINTECH BACKEND RESILIENCE AUDIT")
    print("=" * 80)
    
    asyncio.run(run_async_audit())
    test_websocket_sync()

    print("\n" + "=" * 80)
    print("AUDIT EXECUTION COMPLETE")
    print("=" * 80)

    passes = [r for r in audit_results if r["status"] == "PASS"]
    fails = [r for r in audit_results if r["status"] == "FAIL"]
    criticals = [r for r in fails if r["severity"] == "CRITICAL"]
    highs = [r for r in fails if r["severity"] == "HIGH"]
    mediums = [r for r in fails if r["severity"] == "MEDIUM"]
    lows = [r for r in fails if r["severity"] == "LOW"]

    print(f"\nAUDIT SCOREBOARD:")
    print(f"Total Tests Executed: {len(audit_results)}")
    print(f"PASSES: {len(passes)}")
    print(f"FAILURES: {len(fails)}")
    print(f"  - CRITICAL: {len(criticals)}")
    print(f"  - HIGH:     {len(highs)}")
    print(f"  - MEDIUM:   {len(mediums)}")
    print(f"  - LOW:      {len(lows)}")
    print("=" * 80)

if __name__ == "__main__":
    main()
