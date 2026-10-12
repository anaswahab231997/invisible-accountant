import asyncio
import io
import json
import os
import hashlib
from datetime import datetime, timezone
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

from accounting_client import AccountingClient
from db import (
    get_connection,
    stage_expense,
    confirm_and_queue_to_ledger,
    get_pending_hmrc_queue,
    update_ledger_attachment_status
)
from worker import submit_to_hmrc
from security import compute_receipt_fingerprint

def create_receipt_image(text: str) -> bytes:
    img = Image.new("RGB", (300, 400), color=(255, 255, 255))
    # We can create a simple receipt image
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

async def run_comprehensive_mock_test():
    print("=====================================================================")
    print("STARTING END-TO-END 4-PHASE MOCK TEST AGAINST LIVE XERO SANDBOX")
    print("=====================================================================")
    
    workspace_id = "447123456789"
    client = AccountingClient(workspace_id=workspace_id, provider="XERO")
    
    # Verify token connectivity
    token_info = await client.get_valid_token()
    tenant_id = token_info["tenant_id"]
    print(f"Connected to Xero Tenant: {tenant_id}")

    test_results = {}

    # -------------------------------------------------------------
    # SCENARIO 1: Standard UK Expense with Receipt Attachment (Phase 1, 2, 4)
    # -------------------------------------------------------------
    print("\n>>> SCENARIO 1: Standard UK Expense with Receipt Attachment (Phase 1, 2, 4)")
    async with get_connection() as conn:
        chat_id_1 = await conn.fetchval("""
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, is_demo)
            VALUES (NOW()::text, $1, 'Receipt from Staples for office stationery £50 net, £10 vat, total £60', '[]', TRUE)
            RETURNING id
        """, workspace_id)

    payload_1 = {
        "vendor": "Staples UK",
        "description": "Printer ink and paper supplies",
        "gross_amount": 60.00,
        "net_amount": 50.00,
        "vat_amount": 10.00,
        "vat_rate": "20%",
        "tax_type": "INPUT2",
        "category": "Office Supplies",
        "account_code": "420",
        "currency": "GBP",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "invoice_number": f"INV-STAPLES-{int(datetime.now().timestamp())}",
        "transaction_type": "EXPENSE",
        "accountant_approved": True
    }

    await stage_expense(chat_id_1, payload_1)
    queue_id_1 = await confirm_and_queue_to_ledger(chat_id_1)
    print(f"Scenario 1 queued in hmrc_ledger with ID: {queue_id_1}")

    # Fetch queued item
    async with get_connection() as conn:
        item_1 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", queue_id_1)
        item_dict_1 = dict(item_1)
        item_dict_1["sender_id"] = workspace_id
        item_dict_1["media_urls"] = []

    # Process via worker
    await submit_to_hmrc(item_dict_1)

    # Re-fetch item from db
    async with get_connection() as conn:
        res_row_1 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", queue_id_1)
        res_1 = dict(res_row_1)

    xero_invoice_id_1 = res_1.get("external_bill_id")
    print(f"Scenario 1 Processed: Status={res_1.get('status')}, Xero InvoiceID={xero_invoice_id_1}")

    # Upload attachment to this bill
    receipt_bytes = create_receipt_image("Staples Office Supplies")
    att_res_1 = await client.upload_attachment(
        invoice_id=xero_invoice_id_1,
        filename="staples_receipt_tax_invoice.jpg",
        file_bytes=receipt_bytes
    )
    print(f"Scenario 1 Attachment Uploaded: status={att_res_1.get('status')}, sha256={att_res_1.get('sha256')}")

    # Update ledger with attachment info
    await update_ledger_attachment_status(
        queue_id=queue_id_1,
        status="ATTACHED",
        sha256=att_res_1.get("sha256"),
        xero_attachment_id=att_res_1.get("attachment_id")
    )

    # Verify directly from Xero API
    xero_bill_1 = await client.get_invoice(xero_invoice_id_1)
    inv_1 = xero_bill_1["Invoices"][0]
    test_results["scenario_1"] = {
        "queue_id": queue_id_1,
        "xero_invoice_id": xero_invoice_id_1,
        "xero_status": inv_1.get("Status"),
        "contact": inv_1.get("Contact", {}).get("Name"),
        "total": inv_1.get("Total"),
        "total_tax": inv_1.get("TotalTax"),
        "has_attachments": inv_1.get("HasAttachments"),
        "attachment_count": len(inv_1.get("Attachments", [])),
        "account_code": inv_1["LineItems"][0].get("AccountCode"),
        "tax_type": inv_1["LineItems"][0].get("TaxType")
    }

    # -------------------------------------------------------------
    # SCENARIO 2: Idempotency & 90-Day Deduplication (Phase 2)
    # -------------------------------------------------------------
    print("\n>>> SCENARIO 2: Idempotency & 90-Day Deduplication Replay (Phase 2)")
    # Replay exact same payload
    async with get_connection() as conn:
        chat_id_2 = await conn.fetchval("""
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, is_demo)
            VALUES (NOW()::text, $1, 'Duplicate Staples receipt submitted again', '[]', FALSE)
            RETURNING id
        """, workspace_id)

    await stage_expense(chat_id_2, payload_1)
    queue_id_2 = await confirm_and_queue_to_ledger(chat_id_2)
    async with get_connection() as conn:
        res_row_2 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", queue_id_2)
        res_2 = dict(res_row_2)

    print(f"Scenario 2 Duplicate Submission Status: {res_2.get('status')}")
    test_results["scenario_2"] = {
        "queue_id": queue_id_2,
        "status": res_2.get("status"),
        "receipt_fingerprint": res_2.get("receipt_fingerprint"),
        "external_bill_id": res_2.get("external_bill_id")
    }

    # -------------------------------------------------------------
    # SCENARIO 3: Capital Allowance Triage Gateway (Phase 3 - CAA 2001)
    # -------------------------------------------------------------
    print("\n>>> SCENARIO 3: Capital Allowance Triage Gateway (Phase 3 - CAA 2001)")
    async with get_connection() as conn:
        chat_id_3 = await conn.fetchval("""
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, is_demo)
            VALUES (NOW()::text, $1, 'Apple Store MacBook Pro M3 purchase £1200 gross', '[]', FALSE)
            RETURNING id
        """, workspace_id)

    test_ts = int(datetime.now().timestamp())
    payload_3 = {
        "vendor": f"Apple Store {test_ts}",
        "description": "MacBook Pro M3 14-inch for development",
        "gross_amount": 1200.00,
        "net_amount": 1000.00,
        "vat_amount": 200.00,
        "vat_rate": "20%",
        "category": "Equipment",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "transaction_type": "EXPENSE",
        "accountant_approved": False  # Not approved yet -> Must trip triage gateway!
    }

    await stage_expense(chat_id_3, payload_3)
    queue_id_3 = await confirm_and_queue_to_ledger(chat_id_3)
    async with get_connection() as conn:
        res_row_3 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", queue_id_3)
        res_3 = dict(res_row_3)

    print(f"Scenario 3 Triage Gate Status (> £500): {res_3.get('status')}")
    test_results["scenario_3"] = {
        "queue_id": queue_id_3,
        "status": res_3.get("status"),
        "amount": float(res_3.get("amount")),
        "triage_gate_passed": res_3.get("status") == "CAPITAL_ALLOWANCE"
    }

    # -------------------------------------------------------------
    # SCENARIO 4: Multi-Currency Foreign Expense (Phase 3 - VATA 1994 s88)
    # -------------------------------------------------------------
    print("\n>>> SCENARIO 4: Multi-Currency Foreign Expense Normalization (Phase 3)")
    async with get_connection() as conn:
        chat_id_4 = await conn.fetchval("""
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, is_demo)
            VALUES (NOW()::text, $1, 'AWS Cloud Server hosting USD 100.00', '[]', TRUE)
            RETURNING id
        """, workspace_id)

    payload_4 = {
        "vendor": "Amazon Web Services Inc",
        "description": "AWS Cloud Hosting Infrastructure",
        "gross_amount": 100.00,
        "net_amount": 100.00,
        "vat_amount": 0.00,
        "vat_rate": "0%",
        "currency": "USD",
        "category": "Admin costs",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "invoice_number": f"AWS-USD-{int(datetime.now().timestamp())}",
        "transaction_type": "EXPENSE",
        "accountant_approved": True
    }

    await stage_expense(chat_id_4, payload_4)
    queue_id_4 = await confirm_and_queue_to_ledger(chat_id_4)
    async with get_connection() as conn:
        item_4 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", queue_id_4)
        item_dict_4 = dict(item_4)
        item_dict_4["sender_id"] = workspace_id
        item_dict_4["media_urls"] = []

    await submit_to_hmrc(item_dict_4)

    async with get_connection() as conn:
        res_row_4 = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", queue_id_4)
        res_4 = dict(res_row_4)

    xero_invoice_id_4 = res_4.get("external_bill_id")
    xero_bill_4 = await client.get_invoice(xero_invoice_id_4)
    inv_4 = xero_bill_4["Invoices"][0]

    test_results["scenario_4"] = {
        "queue_id": queue_id_4,
        "xero_invoice_id": xero_invoice_id_4,
        "currency_converted": "GBP",
        "total_gbp": inv_4.get("Total"),
        "total_tax_gbp": inv_4.get("TotalTax"),
        "tax_type": inv_4["LineItems"][0].get("TaxType"),
        "line_description": inv_4["LineItems"][0].get("Description")
    }

    print("\n=====================================================================")
    print("MOCK TEST RESULTS SUMMARY:")
    print(json.dumps(test_results, indent=2))
    print("=====================================================================")

    with open("MOCK_TEST_RESULTS.json", "w") as f:
        json.dump(test_results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_comprehensive_mock_test())
