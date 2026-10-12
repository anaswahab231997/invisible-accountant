import asyncio
import io
import os
import hashlib
from datetime import datetime, timezone
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

from accounting_client import (
    AccountingClient, 
    XeroTenantRateLimiter, 
    inspect_and_validate_attachment
)
from db import (
    get_connection, 
    update_ledger_attachment_status, 
    mark_hmrc_submitted
)

def create_sample_jpeg() -> bytes:
    """Generates a minimal valid JPEG image in memory."""
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def create_sample_pdf() -> bytes:
    """Generates a minimal valid PDF in memory."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000120 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n210\n%%EOF"

async def test_1_concurrency_token_locking():
    print("\n--- TEST 1: High-Concurrency Double-Checked Token Locking ---")
    client = AccountingClient(workspace_id="447123456789", provider="XERO")
    
    # Spawn 5 concurrent coroutines calling get_valid_token()
    coros = [client.get_valid_token() for _ in range(5)]
    results = await asyncio.gather(*coros, return_exceptions=True)
    
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            raise AssertionError(f"Concurrency token failure in task {idx}: {r}")
        assert "access_token" in r, f"Task {idx} missing access_token"
        assert "tenant_id" in r, f"Task {idx} missing tenant_id"
    
    # Verify all coroutines got the same tenant_id
    tenant_ids = {r["tenant_id"] for r in results}
    assert len(tenant_ids) == 1, f"Mismatched tenant IDs across concurrent callers: {tenant_ids}"
    print(f"[PASS] 5/5 concurrent token requests succeeded without race condition. Tenant: {list(tenant_ids)[0]}")

async def test_2_rate_limiter_concurrency_ceiling():
    print("\n--- TEST 2: Rate Limiter Semaphore & Bucket Verification ---")
    limiter = await XeroTenantRateLimiter.get_limiter("test-tenant-rate-limit")
    
    active_concurrent = 0
    max_observed_concurrent = 0
    lock = asyncio.Lock()

    async def simulated_task(task_id):
        nonlocal active_concurrent, max_observed_concurrent
        async def _run():
            nonlocal active_concurrent, max_observed_concurrent
            async with lock:
                active_concurrent += 1
                if active_concurrent > max_observed_concurrent:
                    max_observed_concurrent = active_concurrent
            await asyncio.sleep(0.05)
            async with lock:
                active_concurrent -= 1
            class DummyResp:
                status_code = 200
                headers = {}
            return DummyResp()

        return await limiter.execute(_run)

    tasks = [simulated_task(i) for i in range(8)]
    await asyncio.gather(*tasks)

    print(f"Max observed concurrent in-flight requests: {max_observed_concurrent}")
    assert max_observed_concurrent <= 4, f"Rate limiter exceeded max concurrent ceiling of 4 (Observed {max_observed_concurrent})"
    print(f"[PASS] Concurrency semaphore held strictly at <= 4 (observed: {max_observed_concurrent}).")

def test_3_attachment_preflight_and_magic_bytes():
    print("\n--- TEST 3: Attachment Pre-Flight, Magic Bytes & SHA-256 Integrity ---")
    jpeg_bytes = create_sample_jpeg()
    pdf_bytes = create_sample_pdf()

    # 1. Valid JPEG
    fn, mime, sha, valid_bytes = inspect_and_validate_attachment(jpeg_bytes, "Receipt_Test #1.jpg")
    assert mime == "image/jpeg"
    assert fn.endswith(".jpg")
    assert sha == hashlib.sha256(jpeg_bytes).hexdigest()
    print(f"[PASS] JPEG pre-flight validated: {fn}, MIME: {mime}, SHA256: {sha[:16]}...")

    # 2. Valid PDF
    fn, mime, sha, valid_bytes = inspect_and_validate_attachment(pdf_bytes, "Tax Invoice 2026.pdf")
    assert mime == "application/pdf"
    assert fn.endswith(".pdf")
    assert sha == hashlib.sha256(pdf_bytes).hexdigest()
    print(f"[PASS] PDF pre-flight validated: {fn}, MIME: {mime}, SHA256: {sha[:16]}...")

    # 3. Reject Zero-Byte Payload
    try:
        inspect_and_validate_attachment(b"", "empty.jpg")
        assert False, "Should have rejected 0-byte file"
    except ValueError as e:
        assert "Empty" in str(e)
        print(f"[PASS] Correctly rejected 0-byte payload: {e}")

    # 4. Reject Oversized Payload (>10MB)
    try:
        oversized = b"0" * (10 * 1024 * 1024 + 1024)
        inspect_and_validate_attachment(oversized, "huge.jpg")
        assert False, "Should have rejected >10MB file"
    except ValueError as e:
        assert "exceeds Xero 10MB ceiling" in str(e)
        print(f"[PASS] Correctly rejected >10MB payload: {e}")

    # 5. Reject Invalid Format Garbage
    try:
        garbage = b"THIS IS NOT A VALID IMAGE OR PDF FILE AT ALL"
        inspect_and_validate_attachment(garbage, "garbage.exe")
        assert False, "Should have rejected unparseable garbage"
    except ValueError as e:
        assert "Unrecognized or corrupted" in str(e)
        print(f"[PASS] Correctly rejected corrupted binary: {e}")

async def test_4_live_xero_draft_bill_attachment():
    print("\n--- TEST 4: Live Xero Draft Bill & Attachment Upload End-to-End ---")
    client = AccountingClient(workspace_id="447123456789", provider="XERO")
    
    # 1. Create a draft bill in Xero Sandbox
    bill_payload = {
        "Type": "ACCPAY",
        "Status": "DRAFT",
        "LineAmountTypes": "Exclusive",
        "Date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "DueDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "InvoiceNumber": f"PHASE4-TEST-{int(datetime.now().timestamp())}",
        "Reference": "Phase 4 Attachment Verification",
        "Contact": {"Name": "Phase 4 Office Supplies"},
        "LineItems": [{
            "Description": "Phase 4 Receipt Attachment Audit Test",
            "Quantity": 1,
            "UnitAmount": 45.00,
            "AccountCode": "420",
            "TaxType": "INPUT2",
            "TaxAmount": 9.00
        }]
    }
    
    print("Creating draft bill in Xero Sandbox...")
    bill_resp = await client.create_draft_bill(bill_payload)
    invoice = bill_resp["Invoices"][0]
    invoice_id = invoice["InvoiceID"]
    print(f"Draft bill created successfully! InvoiceID: {invoice_id}")
    
    # 2. Upload sample JPEG receipt attachment
    jpeg_bytes = create_sample_jpeg()
    expected_sha256 = hashlib.sha256(jpeg_bytes).hexdigest()
    
    print(f"Uploading JPEG receipt attachment to Invoice {invoice_id}...")
    upload_res = await client.upload_attachment(
        invoice_id=invoice_id,
        filename="stationery_receipt.jpg",
        file_bytes=jpeg_bytes
    )
    
    assert upload_res["status"] == "success"
    assert upload_res["sha256"] == expected_sha256
    print(f"[PASS] Attachment upload succeeded! SHA256 matches: {upload_res['sha256']}")
    print(f"Attachment details: {upload_res['filename']} ({upload_res['mime_type']}, {upload_res['size_bytes']} bytes)")

    # 3. Verify Invoice in Xero returns the attachment
    invoice_details = await client.get_invoice(invoice_id)
    inv = invoice_details["Invoices"][0]
    has_attachments = inv.get("HasAttachments", False)
    attachments = inv.get("Attachments", [])
    print(f"Xero Invoice HasAttachments: {has_attachments}, Attachment Count: {len(attachments)}")
    assert has_attachments is True, "Xero Invoice should have HasAttachments=True"
    print(f"[PASS] Live verification confirmed: Attachment is permanently attached to bill {invoice_id} in Xero.")

async def test_5_failure_isolation_db_preservation():
    print("\n--- TEST 5: Failure Isolation & DB Ledger Integrity ---")
    async with get_connection() as conn:
        chat_id = await conn.fetchval("""
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, is_demo)
            VALUES (NOW()::text, 'test_user_isolation', 'Test isolation message', TRUE)
            RETURNING id
        """)

        test_id = await conn.fetchval("""
            INSERT INTO hmrc_ledger (chat_id, timestamp, vendor, amount, category, status, external_bill_id, is_demo)
            VALUES ($1, NOW(), 'Test Vendor Isolation', 120.00, 'Admin costs', 'PROCESSING', 'TEST-BILL-GUID-1234', TRUE)
            RETURNING id
        """, chat_id)
        
        # Simulate attachment failure
        err_msg = "HTTP 404 downloading receipt from expired S3 presigned URL"
        await update_ledger_attachment_status(
            queue_id=test_id,
            status="ATTACHMENT_FAILED",
            error=err_msg
        )
        
        # Mark submitted with failure isolation
        await mark_hmrc_submitted(
            queue_id=test_id,
            external_bill_id="TEST-BILL-GUID-1234",
            attachment_status="ATTACHMENT_FAILED"
        )
        
        row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", test_id)
        assert row["status"] == "SUBMITTED", "Status should be SUBMITTED"
        assert row["external_bill_id"] == "TEST-BILL-GUID-1234", "external_bill_id must NOT be wiped"
        assert row["attachment_status"] == "ATTACHMENT_FAILED", "attachment_status must record ATTACHMENT_FAILED"
        assert row["attachment_error"] == err_msg, "attachment_error must record root cause"
        
        # Clean up test rows
        await conn.execute("DELETE FROM hmrc_ledger WHERE id = $1", test_id)
        await conn.execute("DELETE FROM chat_sessions WHERE id = $1", chat_id)
        print(f"[PASS] Failure Isolation confirmed: Draft bill retained, attachment failure safely audited.")

async def main():
    print("=====================================================================")
    print("PHASE 4: COMMERCIAL HARDENING & ATTACHMENT INTEGRITY VERIFICATION SUITE")
    print("=====================================================================")
    await test_1_concurrency_token_locking()
    await test_2_rate_limiter_concurrency_ceiling()
    test_3_attachment_preflight_and_magic_bytes()
    await test_4_live_xero_draft_bill_attachment()
    await test_5_failure_isolation_db_preservation()
    print("\n=====================================================================")
    print("ALL PHASE 4 HARDENING TESTS PASSED WITH 100% SUCCESS!")
    print("=====================================================================")

if __name__ == "__main__":
    asyncio.run(main())
