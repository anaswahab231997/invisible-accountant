import asyncio
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from httpx import AsyncClient, ASGITransport
from dotenv import load_dotenv

load_dotenv()

from main import app
import db
from security import hash_practice_password, verify_practice_password, create_practice_token, verify_practice_token

async def run_e2e_tests():
    print("==================================================")
    print("🚀 RUNNING END-TO-END B2B PRACTICE MULTI-TENANCY TESTS")
    print("==================================================")
    
    await db.init_pool()
    
    test_slug = "apex-chartered-e2e-test"
    test_email = "e2e_partner@apexaccountancy.co.uk"
    test_code = "IA-8899"
    
    # 0. Cleanup previous test run if exists
    async with db.get_connection() as conn:
        await conn.execute("DELETE FROM practices WHERE slug = $1 OR contact_email = $2", test_slug, test_email)
    print("✅ Step 0: Test practice pre-clean completed.")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        
        # 1. Test Partner Registration via POST /partner/register
        print("\n--- Testing Partner Registration ---")
        reg_payload = {
            "name": "Apex Chartered Accountants LLP",
            "contact_name": "David Sterling, FCA",
            "contact_email": test_email,
            "contact_phone": "+44 20 7946 0912",
            "regulatory_body": "ICAEW",
            "regulatory_number": "ICAEW-998877",
            "company_number": "OC123456",
            "slug": test_slug,
            "password": "SecurePassword123!"
        }
        res_reg = await client.post("/partner/register", data=reg_payload, follow_redirects=False)
        assert res_reg.status_code == 303, f"Expected 303 redirect, got {res_reg.status_code}"
        assert res_reg.headers["location"] == "/partner/dashboard"
        assert "practice_session" in res_reg.cookies
        practice_cookie = res_reg.cookies["practice_session"]
        print(f"✅ Partner registered successfully. Cookie: {practice_cookie[:25]}...")
        
        # Verify in DB
        practice = await db.get_practice_by_slug(test_slug)
        assert practice is not None
        assert practice["name"] == "Apex Chartered Accountants LLP"
        assert practice["regulatory_body"] == "ICAEW"
        firm_code = practice["firm_code"]
        practice_id = practice["id"]
        print(f"✅ Practice found in Supabase DB: ID={practice_id}, Firm Code={firm_code}")
        
        # 2. Test Partner Dashboard Access via GET /partner/dashboard
        print("\n--- Testing Partner Dashboard Access ---")
        res_dash = await client.get("/partner/dashboard", cookies={"practice_session": practice_cookie})
        assert res_dash.status_code == 200, f"Expected 200, got {res_dash.status_code}"
        assert "Apex Chartered Accountants LLP" in res_dash.text
        assert "ICAEW" in res_dash.text
        assert firm_code in res_dash.text
        print("✅ Partner dashboard loaded with correct firm metadata and branding.")
        
        # 3. Test Client Join Splash Page via GET /join/{firm_slug}
        print(f"\n--- Testing Client Join Splash Page (/join/{test_slug}) ---")
        res_join = await client.get(f"/join/{test_slug}")
        assert res_join.status_code == 200, f"Expected 200, got {res_join.status_code}"
        assert "Apex Chartered Accountants LLP" in res_join.text
        assert f"JOIN_{firm_code}" in res_join.text
        print("✅ Client onboarding splash page correctly rendered firm badge and WhatsApp deep link.")
        
        # 4. Test WhatsApp Intake with Join Code (e.g. "JOIN_IA-XXXX")
        print("\n--- Testing WhatsApp Client Linking via Join Code ---")
        test_client_sender = "447999888777"
        
        # Clean any prior link
        async with db.get_connection() as conn:
            await conn.execute("DELETE FROM practice_clients WHERE client_sender_id = $1", test_client_sender)
            await conn.execute("DELETE FROM hmrc_ledger WHERE chat_id IN (SELECT id FROM chat_sessions WHERE sender_id = $1)", test_client_sender)
            await conn.execute("DELETE FROM chat_sessions WHERE sender_id = $1", test_client_sender)
            
        from main import process_intake_task
        chat_id_join = await db.create_chat_session(test_client_sender, f"JOIN_{firm_code}", [], 0)
        await process_intake_task(chat_id_join, test_client_sender, f"JOIN_{firm_code}", 0, [])
        
        # Verify client is linked to practice in DB
        linked_practice = await db.get_client_practice(test_client_sender)
        assert linked_practice is not None, "Client should be linked to practice"
        assert linked_practice["id"] == practice_id
        assert linked_practice["slug"] == test_slug
        print(f"✅ Client {test_client_sender} successfully linked to practice {practice_id} ({test_slug})!")
        
        # 5. Test Receipt Staging and Confirmation with Practice Association
        print("\n--- Testing Receipt Submission and Confirmation with Practice Link ---")
        chat_id_receipt = await db.create_chat_session(test_client_sender, "Materials at Screwfix £120.00 incl VAT", [], 0)
        test_receipt_payload = {
            "vendor": "Screwfix Direct",
            "amount": 120.00,
            "gross_amount": 120.00,
            "vat_amount": 20.00,
            "net_amount": 100.00,
            "category": "Direct Materials",
            "account_code": "300",
            "tax_type": "INPUT2",
            "is_ambiguous": False
        }
        await db.stage_expense(chat_id_receipt, test_receipt_payload)
        
        # Process 'proceed'
        await process_intake_task(chat_id_receipt, test_client_sender, "proceed", 1, [])
        
        # Verify ledger has practice_id
        async with db.get_connection() as conn:
            ledger_entry = await conn.fetchrow(
                "SELECT * FROM hmrc_ledger WHERE chat_id = $1",
                chat_id_receipt
            )
            assert ledger_entry is not None, "HMRC ledger entry must exist"
            assert ledger_entry["practice_id"] == practice_id, f"Expected practice_id={practice_id}, got {ledger_entry['practice_id']}"
            assert ledger_entry["status"] == "PENDING"
            
            # Verify practice_clients receipt count incremented
            client_record = await conn.fetchrow(
                "SELECT * FROM practice_clients WHERE practice_id = $1 AND client_sender_id = $2",
                practice_id, test_client_sender
            )
            assert client_record is not None
            assert client_record["total_receipts_count"] >= 1, f"Expected >= 1 receipt, got {client_record['total_receipts_count']}"
            print(f"✅ Receipt confirmed in HMRC ledger with practice_id={practice_id}. Practice client count={client_record['total_receipts_count']}")

        # 6. Test Practice Stats & Commission Calculations
        print("\n--- Testing Practice Stats and Revenue Share Calculation ---")
        stats = await db.get_practice_stats(practice_id)
        assert stats["active_clients"] == 1
        assert stats["total_receipts"] >= 1
        assert stats["monthly_commission_accrued_gbp"] == 3.00
        assert stats["annual_commission_projected_gbp"] == 36.00
        print(f"✅ Practice Stats verified: Active Clients={stats['active_clients']}, Monthly Commission=£{stats['monthly_commission_accrued_gbp']}, Projected Annual=£{stats['annual_commission_projected_gbp']}")

        # 7. Test Digital 90-Day Pilot LOI Execution
        print("\n--- Testing Digital 90-Day Pilot LOI Execution via POST /partner/loi/sign ---")
        loi_payload = {
            "signatory_name": "David Sterling, FCA",
            "signatory_title": "Senior Practice Partner",
            "firm_legal_name": "Apex Chartered Accountants LLP",
            "firm_crn": "OC123456",
            "firm_address": "10 Gresham Street, London EC2V 7JD",
            "pledged_seats": "75",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
        res_loi = await client.post(
            "/partner/loi/sign",
            data=loi_payload,
            cookies={"practice_session": practice_cookie},
            follow_redirects=False
        )
        assert res_loi.status_code == 303, f"Expected 303 redirect, got {res_loi.status_code}"
        
        # Verify in DB
        lois = await db.get_practice_lois(practice_id)
        assert len(lois) >= 1
        loi = lois[0]
        assert loi["signatory_name"] == "David Sterling, FCA"
        assert loi["pledged_client_seats"] == 75
        assert loi["pilot_duration_days"] == 90
        assert loi["status"] == "EXECUTED"
        assert loi["document_sha256"] is not None
        print(f"✅ Digital LOI executed! LOI ID={loi['id']}, Pledged Seats={loi['pledged_client_seats']}, SHA256={loi['document_sha256'][:20]}...")

        # 8. Test Partner Logout & Session Revocation
        print("\n--- Testing Partner Logout ---")
        res_logout = await client.get("/partner/logout", follow_redirects=False)
        assert res_logout.status_code == 303
        
        # Verify unauthenticated browser access to /partner/dashboard redirects to login
        res_browser_unauth = await client.get("/partner/dashboard", headers={"Accept": "text/html"}, follow_redirects=False)
        assert res_browser_unauth.status_code == 303
        assert "/partner/login" in res_browser_unauth.headers["location"]

        # Verify unauthenticated API access returns 401
        res_api_unauth = await client.get("/partner/dashboard", headers={"Accept": "application/json"}, follow_redirects=False)
        assert res_api_unauth.status_code == 401
        print("✅ Session logout and dual-mode route protection (303 redirect for browsers, 401 for API) verified.")

    print("\n==================================================")
    print("🎉 ALL 8 B2B PRACTICE END-TO-END TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
