import asyncio
import os
import json
import uuid
import datetime
from dotenv import load_dotenv

load_dotenv()
os.environ["DRY_RUN"] = "false"

from db import get_connection, confirm_and_queue_to_ledger
from aes_gcm_security import TokenEncryptionEngine
from accounting_client import AccountingClient
from worker import submit_to_hmrc
from dashboard import view_dashboard, get_edit_row, submit_triage
from fastapi import Request

async def insert_chat_helper(sender_id, raw_message, staging_payload):
    async with get_connection() as conn:
        return await conn.fetchval("""
            INSERT INTO chat_sessions (sender_id, raw_message, staging_payload, is_demo, timestamp)
            VALUES ($1, $2, $3, FALSE, NOW())
            RETURNING id
        """, sender_id, raw_message, staging_payload)

async def wait_for_submission(ledger_id: int, max_wait_sec: int = 25) -> dict:
    """Waits for live Render worker to process, or processes locally if worker is idle."""
    for _ in range(max_wait_sec):
        async with get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id)
            if row and row["status"] == "SUBMITTED" and row["external_bill_id"]:
                return dict(row)
        await asyncio.sleep(1)
        
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id)
        if row and row["status"] != "SUBMITTED":
            item_dict = dict(row)
            item_dict["sender_id"] = WORKSPACE_ID
            await submit_to_hmrc(item_dict)
            row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id)
        return dict(row)

WORKSPACE_ID = "447123456789"
MASTER_KEY = os.getenv("ENCRYPTION_MASTER_KEY_B64")
token_engine = TokenEncryptionEngine(MASTER_KEY)

class DummyRequest(Request):
    def __init__(self, url_path="/dashboard"):
        scope = {
            "type": "http",
            "method": "GET",
            "path": url_path,
            "headers": [],
            "query_string": b"",
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }
        super().__init__(scope)

async def run_phase3_verification():
    print("=" * 80)
    print("PHASE 3 VERIFICATION: ACCOUNTANT TRIAGE, FIXED ASSETS & MULTI-CURRENCY")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # TEST 1: Capital Allowance (>£500) Triage into Fixed Asset 720 (Computer Equipment)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Capital Allowance Detection & Accountant Fixed Asset Triage (CAA 2001)")
    unique_ref = f"CAP-{uuid.uuid4().hex[:6]}"
    macbook_payload = {
        "vendor": f"Apple Store {unique_ref}",
        "amount": 1299.00,
        "gross_amount": 1299.00,
        "net_amount": 1082.50,
        "vat_amount": 216.50,
        "date": "2026-10-12",
        "description": "14-inch MacBook Pro M4 for engineering",
        "category": "Admin costs",  # Misclassified initially as P&L admin
        "account_code": "420",
        "tax_type": "INPUT2",
        "transaction_type": "EXPENSE"
    }

    # Step 1a: Simulate intake without accountant approval
    chat_id = await insert_chat_helper(
        sender_id=WORKSPACE_ID,
        raw_message=f"Bought new MacBook Pro for 1299 at Apple Store ref {unique_ref}",
        staging_payload=json.dumps(macbook_payload)
    )
    print(f"  -> Created chat session #{chat_id}")

    # Confirm into ledger
    ledger_id = await confirm_and_queue_to_ledger(chat_id)
    print(f"  -> Queued to hmrc_ledger #{ledger_id}")

    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id)
        assert row["status"] == "CAPITAL_ALLOWANCE", f"Expected CAPITAL_ALLOWANCE, got {row['status']}"
        assert not row["accountant_approved"], "Expected accountant_approved=False initially"
    print(f"  [PASS] Successfully trapped £1,299 asset in CAPITAL_ALLOWANCE status (prevented P&L expensing)")

    # Step 1b: Accountant triages item in dashboard: reclassifies to 720 (Computer Equipment)
    print("  -> Accountant triaging record: reclassifying to 720 (Fixed Asset)...")
    req = DummyRequest()
    await submit_triage(
        request=req,
        item_type="ledger",
        item_id=ledger_id,
        account_code="720",
        tax_type="INPUT2",
        is_capital_asset=True,
        allow_duplicate=False
    )

    async with get_connection() as conn:
        triaged_row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id)
        assert triaged_row["accountant_approved"] is True, "Expected accountant_approved=True"
        assert triaged_row["status"] in ("PENDING", "PROCESSING", "SUBMITTED")
        
        # Verify decrypted payload has 720
        dec = token_engine.decrypt_tokens(json.loads(triaged_row["encrypted_financial_data"]), associated_data=str(chat_id))
        fin = json.loads(dec)
        assert fin["account_code"] == "720", f"Expected 720, got {fin['account_code']}"
    print(f"  [PASS] Triage gateway updated nominal code to 720 and approved record")

    # Step 1c: Wait for worker submission to Xero sandbox
    print("  -> Awaiting draft bill creation in Xero Sandbox...")
    submitted_row = await wait_for_submission(ledger_id)
    assert submitted_row["status"] == "SUBMITTED", f"Expected SUBMITTED, got {submitted_row['status']}"
    assert submitted_row["external_bill_id"], "Expected external_bill_id"
    xero_inv_id = submitted_row["external_bill_id"]
    print(f"  -> Bill successfully pushed to Xero! External Bill ID: {xero_inv_id}")

    # Step 1d: Verify in Xero live tenant
    client = AccountingClient(WORKSPACE_ID)
    inv = await client.get_invoice(xero_inv_id)
    line = inv["Invoices"][0]["LineItems"][0]
    print(f"  -> Verified in Xero: AccountCode = {line['AccountCode']}, UnitAmount = £{line['UnitAmount']}, TaxType = {line.get('TaxType')}")
    assert line["AccountCode"] == "720", f"Xero AccountCode was {line['AccountCode']}, expected 720!"
    print("  [PASS] TEST 1 COMPLETE: CAA 2001 Fixed Asset 720 accurately posted to Xero Draft Bill!")

    # -------------------------------------------------------------------------
    # TEST 2: Duplicate Suspected Accountant Override Gateway
    # -------------------------------------------------------------------------
    print("\n[TEST 2] 90-Day Deduplication Gate & Accountant Override")
    dup_ref = f"DUP-{uuid.uuid4().hex[:6]}"
    dup_payload = {
        "vendor": f"Office Supplies Co {dup_ref}",
        "amount": 75.00,
        "gross_amount": 75.00,
        "net_amount": 62.50,
        "vat_amount": 12.50,
        "date": "2026-10-12",
        "description": "Printer ink and paper",
        "category": "Admin costs",
        "account_code": "420",
        "tax_type": "INPUT2",
        "transaction_type": "EXPENSE"
    }

    # First instance: normal confirm and submit
    chat1 = await insert_chat_helper(WORKSPACE_ID, f"Invoice {dup_ref}", json.dumps(dup_payload))
    led1 = await confirm_and_queue_to_ledger(chat1)
    sub1 = await wait_for_submission(led1)
    print(f"  -> Original receipt submitted as Xero ID {sub1.get('external_bill_id')}")

    # Second instance: identical fingerprint within 90 days
    chat2 = await insert_chat_helper(WORKSPACE_ID, f"Invoice {dup_ref}", json.dumps(dup_payload))
    led2 = await confirm_and_queue_to_ledger(chat2)
    async with get_connection() as conn:
        r2 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", led2)
        assert r2["status"] == "DUPLICATE_SUSPECTED", f"Expected DUPLICATE_SUSPECTED, got {r2['status']}"
        assert not r2["accountant_approved"]
    print(f"  [PASS] Duplicate receipt successfully blocked into DUPLICATE_SUSPECTED state")

    # Verify worker ignores unapproved duplicate
    await submit_to_hmrc(dict(r2))
    async with get_connection() as conn:
        r2_check = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", led2)
        assert r2_check["status"] == "DUPLICATE_SUSPECTED"
        assert r2_check["external_bill_id"] is None
    print(f"  [PASS] Worker correctly refused to push unapproved duplicate to Xero")

    # Accountant reviews and overrides duplicate via triage
    print("  -> Accountant overrides duplicate gate via triage gateway...")
    await submit_triage(
        request=req,
        item_type="ledger",
        item_id=led2,
        account_code="420",
        tax_type="INPUT2",
        is_capital_asset=False,
        allow_duplicate=True
    )

    r2_submitted = await wait_for_submission(led2)
    assert r2_submitted["status"] == "SUBMITTED"
    assert r2_submitted["external_bill_id"]
    print(f"  [PASS] TEST 2 COMPLETE: Duplicate safely overridden and pushed as Xero ID {r2_submitted['external_bill_id']}")

    # -------------------------------------------------------------------------
    # TEST 3: Multi-Currency Foreign Receipt Normalization (VATA 1994 s88 & VAT Notice 700 §7.6)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Multi-Currency Foreign Receipt Normalization ($199.00 USD -> Base GBP)")
    fx_ref = f"AWS-{uuid.uuid4().hex[:6]}"
    usd_payload = {
        "vendor": f"Amazon Web Services {fx_ref}",
        "amount": 199.00,
        "gross_amount": 199.00,
        "net_amount": 199.00,
        "vat_amount": 0.00,
        "currency": "USD",
        "date": "2026-10-12",
        "description": "AWS Cloud Hosting USD Monthly Invoice",
        "category": "Admin costs",
        "account_code": "420",
        "tax_type": "INPUT2",  # Naive or unadjusted tax type
        "needs_accountant_review": True,
        "transaction_type": "EXPENSE"
    }

    chat3 = await insert_chat_helper(WORKSPACE_ID, f"AWS USD $199 invoice {fx_ref}", json.dumps(usd_payload))
    led3 = await confirm_and_queue_to_ledger(chat3)
    
    async with get_connection() as conn:
        r3_init = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", led3)
        assert r3_init["status"] in ("CAPITAL_ALLOWANCE", "NEEDS_REVIEW")

    print("  -> Accountant triages foreign USD receipt via dashboard gateway...")
    await submit_triage(
        request=req,
        item_type="ledger",
        item_id=led3,
        account_code="420",
        tax_type="INPUT2",
        is_capital_asset=False,
        allow_duplicate=False
    )

    r3_submitted = await wait_for_submission(led3)
    assert r3_submitted["status"] == "SUBMITTED", f"Expected SUBMITTED, got {r3_submitted['status']}"
    assert r3_submitted["external_bill_id"]
    fx_bill_id = r3_submitted["external_bill_id"]

    inv_fx = await client.get_invoice(fx_bill_id)
    line_fx = inv_fx["Invoices"][0]["LineItems"][0]
    total_gbp = inv_fx["Invoices"][0]["Total"]
    print(f"  -> Verified in Xero: Converted GBP Total = £{total_gbp:.2f}, TaxType = {line_fx.get('TaxType')}")
    print(f"  -> Line Description: {line_fx.get('Description')}")
    
    # Assert statutory rules: zero input tax on foreign, base GBP converted total
    assert line_fx.get("TaxType") == "NONE", f"Expected TaxType 'NONE', got {line_fx.get('TaxType')}"
    assert abs(total_gbp - 155.22) < 0.1, f"Expected approx £155.22 (199 * 0.78), got £{total_gbp}"
    print("  [PASS] TEST 3 COMPLETE: Multi-currency USD converted to GBP with statutory 0% TaxType='NONE'")

    # -------------------------------------------------------------------------
    # TEST 4: Dashboard UI & Triage Endpoints Health Check
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Dashboard Queue & Interactive Triage HTMX Form Rendering")
    resp_dash = await view_dashboard(req, tab="capital_allowances")
    assert resp_dash.status_code == 200
    assert "Capital Allowances (>£500)" in resp_dash.body.decode("utf-8")
    assert "Duplicate Suspected" in resp_dash.body.decode("utf-8")
    print("  [PASS] GET /dashboard?tab=capital_allowances returned 200 OK with tabs and badges")

    resp_edit = await get_edit_row(req, item_type="ledger", item_id=ledger_id)
    assert resp_edit.status_code == 200
    assert "Xero Account Code (P&L vs Balance Sheet)" in resp_edit.body.decode("utf-8")
    assert "720 - Computer Equipment (Fixed Asset)" in resp_edit.body.decode("utf-8")
    print("  [PASS] GET /dashboard/edit/ledger/{id} returned 200 OK with interactive nominal selectors")

    print("\n" + "=" * 80)
    print("ALL PHASE 3 VERIFICATION TESTS PASSED WITH 100% SUCCESS (ZERO HALLUCINATION)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_phase3_verification())
