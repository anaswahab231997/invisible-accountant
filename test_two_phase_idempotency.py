import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from security import compute_receipt_fingerprint
from db import (
    get_connection,
    confirm_and_queue_to_ledger,
    check_active_duplicate_expense,
    create_chat_session,
    stage_expense,
    update_ledger_external_bill_id,
    mark_hmrc_submitted
)
from worker import submit_to_hmrc
from accounting_client import AccountingClient

WORKSPACE_ID = "447123456789"

async def test_deterministic_fingerprint():
    print("\n==========================================")
    print("TEST 1: Deterministic Receipt Fingerprinting")
    print("==========================================")

    # Variations of the same transaction
    fp1 = compute_receipt_fingerprint(
        sender_id="447123456789",
        vendor="Staples",
        gross_amount=120.00,
        transaction_date="2026-10-12"
    )
    fp2 = compute_receipt_fingerprint(
        sender_id="whatsapp:447123456789",
        vendor="  staples   ",
        gross_amount="120.0",
        transaction_date="12/10/2026"
    )
    fp3 = compute_receipt_fingerprint(
        sender_id="447123456789",
        vendor="STAPLES",
        gross_amount="£120.00",
        transaction_date="2026-10-12T14:30:00"
    )

    print(f"Fingerprint 1: {fp1}")
    print(f"Fingerprint 2: {fp2}")
    print(f"Fingerprint 3: {fp3}")

    assert fp1 == fp2 == fp3, f"Fingerprints must match across normalized inputs! Got {fp1} vs {fp2}"
    print("[PASS] Deterministic normalization check: All 3 variants generated identical SHA256.")

    # Different vendor / amount must generate a distinct fingerprint
    fp_diff = compute_receipt_fingerprint(
        sender_id="447123456789",
        vendor="Screwfix",
        gross_amount=120.00,
        transaction_date="2026-10-12"
    )
    assert fp1 != fp_diff, "Different vendor must generate different fingerprint!"
    print(f"Fingerprint Diff (Screwfix): {fp_diff}")
    print("[PASS] Distinct transaction check: Different inputs yield different SHA256.")


async def test_90_day_deduplication():
    print("\n==========================================")
    print("TEST 2: 90-Day Deduplication Gate")
    print("==========================================")

    unique_vendor = f"TestVendor-{uuid.uuid4().hex[:6]}"
    gross = 45.50
    net = 37.92
    vat = 7.58
    tx_date = "2026-10-12"

    payload = {
        "vendor": unique_vendor,
        "gross_amount": gross,
        "net_amount": net,
        "vat_amount": vat,
        "category": "Admin costs",
        "transaction_date": tx_date,
        "transaction_type": "EXPENSE",
        "description": "Office supplies test"
    }

    # Step 1: Create chat session 1 & stage expense
    chat_id_1 = await create_chat_session(
        sender_id=WORKSPACE_ID,
        message=f"Bought {unique_vendor} for £{gross}",
        media_urls=[],
        turn_count=1
    )
    await stage_expense(chat_id_1, payload)

    # Step 2: Confirm first expense
    ledger_id_1 = await confirm_and_queue_to_ledger(chat_id_1)
    async with get_connection() as conn:
        item_1 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id_1)
    
    print(f"First expense confirmed: Ledger ID #{item_1['id']}, Status: {item_1['status']}, Fingerprint: {item_1['receipt_fingerprint']}")
    assert item_1["status"] == "PENDING", f"Expected PENDING, got {item_1['status']}"
    assert item_1["receipt_fingerprint"] is not None, "Expected receipt_fingerprint to be populated"
    print("[PASS] First expense successfully inserted into ledger with status PENDING.")

    # Step 3: Now create chat session 2 with the EXACT SAME receipt
    chat_id_2 = await create_chat_session(
        sender_id=WORKSPACE_ID,
        message=f"Duplicate submission: Bought {unique_vendor} for £{gross}",
        media_urls=[],
        turn_count=1
    )
    await stage_expense(chat_id_2, payload)

    # Check deduplication gate before confirmation
    expected_fp = compute_receipt_fingerprint(WORKSPACE_ID, unique_vendor, gross, tx_date)
    dup = await check_active_duplicate_expense(expected_fp, days=90)
    assert dup is not None, "Deduplication check must find active matching item in last 90 days!"
    assert dup["id"] == ledger_id_1, f"Expected duplicate to point to ledger #{ledger_id_1}"
    print(f"[PASS] check_active_duplicate_expense detected existing active ledger entry #{dup['id']}.")

    # Confirm the duplicate chat session
    ledger_id_2 = await confirm_and_queue_to_ledger(chat_id_2)
    async with get_connection() as conn:
        item_2 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id_2)
    
    print(f"Second expense confirmed: Ledger ID #{item_2['id']}, Status: {item_2['status']}")
    assert item_2["status"] == "DUPLICATE_SUSPECTED", f"Expected DUPLICATE_SUSPECTED, got {item_2['status']}"
    print("[PASS] 90-Day Deduplication Gate: Duplicate flagged as DUPLICATE_SUSPECTED!")


async def test_two_phase_idempotency_live_xero():
    print("\n==========================================")
    print("TEST 3: Two-Phase Idempotency Live against Supabase & Xero Sandbox")
    print("==========================================")

    client = AccountingClient(workspace_id=WORKSPACE_ID, provider="XERO")
    
    unique_ref = f"IDEM-{uuid.uuid4().hex[:8]}"
    vendor = f"Screwfix {unique_ref}"
    gross = 85.00
    vat = 14.17
    net = 70.83
    tx_date = "2026-10-12"

    payload = {
        "vendor": vendor,
        "gross_amount": gross,
        "net_amount": net,
        "vat_amount": vat,
        "category": "Repairs and maintenance",
        "transaction_date": tx_date,
        "transaction_type": "EXPENSE",
        "description": f"Safety boots and drill bits ({unique_ref})",
        "reference": unique_ref,
        "invoice_number": unique_ref
    }

    # Step 1: Create session & confirm into ledger
    chat_id = await create_chat_session(
        sender_id=WORKSPACE_ID,
        message=f"Screwfix purchase £85.00 ref {unique_ref}",
        media_urls=["https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=800"],
        turn_count=1
    )
    await stage_expense(chat_id, payload)
    ledger_id = await confirm_and_queue_to_ledger(chat_id)

    async with get_connection() as conn:
        ledger_item = dict(await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id))
        chat_row = await conn.fetchrow("SELECT sender_id, media_urls FROM chat_sessions WHERE id = $1", chat_id)
        ledger_item["sender_id"] = chat_row["sender_id"]
        ledger_item["media_urls"] = json.loads(chat_row["media_urls"]) if chat_row["media_urls"] else []

    print(f"Created Ledger Entry #{ledger_id}, Status: {ledger_item['status']}, external_bill_id: {ledger_item.get('external_bill_id')}")
    assert ledger_item["external_bill_id"] is None, "external_bill_id must initially be None"

    # Step 2: Phase 1 execution via submit_to_hmrc
    print("\n--- Executing Initial submit_to_hmrc() ---")
    await submit_to_hmrc(ledger_item)

    # Verify database after initial submission
    async with get_connection() as conn:
        updated_item_1 = dict(await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id))
    
    first_bill_id = updated_item_1.get("external_bill_id")
    print(f"Post-submission Ledger #{ledger_id}: Status={updated_item_1['status']}, external_bill_id={first_bill_id}")
    assert updated_item_1["status"] == "SUBMITTED", f"Expected SUBMITTED, got {updated_item_1['status']}"
    assert first_bill_id is not None, "external_bill_id MUST be saved in database"

    # Verify invoice directly in Xero API
    print(f"Verifying invoice {first_bill_id} in live Xero API...")
    xero_invoice = await client.get_invoice(first_bill_id)
    inv_details = xero_invoice.get("Invoices", [{}])[0]
    print(f"Xero Invoice Confirmed: ID={inv_details.get('InvoiceID')}, Status={inv_details.get('Status')}, Ref={inv_details.get('Reference')}, Total={inv_details.get('Total')}")
    assert inv_details.get("InvoiceID") == first_bill_id, "InvoiceID in Xero must match external_bill_id in DB"
    assert inv_details.get("Reference") == unique_ref, "Invoice Reference must match unique test ref"

    # Step 3: Simulate Crash / Retry (Re-executing submit_to_hmrc)
    print("\n--- Simulating Crash / Retry with existing external_bill_id ---")
    # Reset status to PENDING or pass the item again
    async with get_connection() as conn:
        await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE id = $1", ledger_id)
        retry_item = dict(await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id))
        retry_item["sender_id"] = chat_row["sender_id"]
        retry_item["media_urls"] = json.loads(chat_row["media_urls"]) if chat_row["media_urls"] else []

    assert retry_item["external_bill_id"] == first_bill_id, "external_bill_id is present prior to retry"
    
    # Run submit_to_hmrc AGAIN
    await submit_to_hmrc(retry_item)

    # Verify database after retry
    async with get_connection() as conn:
        updated_item_2 = dict(await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", ledger_id))

    second_bill_id = updated_item_2.get("external_bill_id")
    print(f"Post-retry Ledger #{ledger_id}: Status={updated_item_2['status']}, external_bill_id={second_bill_id}")
    assert updated_item_2["status"] == "SUBMITTED", "Must be SUBMITTED after retry"
    assert second_bill_id == first_bill_id, f"external_bill_id must remain IDENTICAL: {second_bill_id} == {first_bill_id}"

    # Verify in Xero that NO duplicate invoice exists with this Reference
    invoices_with_ref = await client.get_invoices(where=f'Reference=="{unique_ref}"')
    print(f"Total Invoices in Xero with Reference '{unique_ref}': {len(invoices_with_ref)}")
    for inv in invoices_with_ref:
        print(f" - Found InvoiceID: {inv.get('InvoiceID')}, Number: {inv.get('InvoiceNumber')}")
    
    assert len(invoices_with_ref) == 1, f"Expected exactly 1 invoice in Xero, but found {len(invoices_with_ref)}! Duplicate was created!"
    print("[PASS] Two-Phase Idempotency: Re-running submit_to_hmrc() reused existing bill and created ZERO duplicates in Xero!")


async def main():
    print("Starting Phase 2 Remediation Verification Test Suite...")
    try:
        await test_deterministic_fingerprint()
        await test_90_day_deduplication()
        await test_two_phase_idempotency_live_xero()
        print("\n=======================================================")
        print("[SUCCESS] ALL TESTS PASSED: Two-Phase Idempotency & Deduplication fully verified!")
        print("=======================================================")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    asyncio.run(main())
