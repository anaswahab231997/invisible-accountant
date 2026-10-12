from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json
import os
import datetime
from db import get_connection, confirm_and_queue_to_ledger
from security import verify_api_key
from aes_gcm_security import TokenEncryptionEngine
from currency_converter import detect_currency, normalize_to_base_currency
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

MASTER_KEY = os.getenv("ENCRYPTION_MASTER_KEY_B64")
token_engine = TokenEncryptionEngine(MASTER_KEY) if MASTER_KEY else None

ACCOUNT_CODE_LABELS = {
    "720": "720 - Computer Equipment (Fixed Asset)",
    "710": "710 - Office Equipment (Fixed Asset)",
    "764": "764 - Plant & Machinery (Fixed Asset)",
    "760": "760 - Motor Vehicles (Fixed Asset)",
    "420": "420 - Printing & Stationery (Expense)",
    "429": "429 - General Expenses (Expense)",
    "400": "400 - Advertising & Marketing (Expense)",
    "404": "404 - Travel costs (Expense)",
    "412": "412 - Professional fees (Expense)",
    "416": "416 - Bank & financial charges (Expense)",
    "441": "441 - Telephone & Internet (Expense)",
    "445": "445 - Utilities (Expense)",
    "449": "449 - Rent (Expense)",
    "477": "477 - Wages and Salaries (Expense)",
    "485": "485 - Subcontractor Costs (CIS)",
    "489": "489 - Repairs and Maintenance (Expense)",
    "310": "310 - Cost of Goods Sold",
    "200": "200 - Sales / Income",
}

TAX_CODE_LABELS = {
    "INPUT2": "20% (VAT on Expenses) [INPUT2]",
    "INPUT": "20% (Standard Input VAT) [INPUT]",
    "NONE": "No VAT (0%) [NONE]",
    "ZERORATEDINPUT": "Zero Rated (0%) [ZERORATEDINPUT]",
    "EXEMPTINPUT": "Exempt (0%) [EXEMPTINPUT]"
}

def format_ts(ts_val) -> str:
    try:
        dt = datetime.datetime.fromisoformat(str(ts_val))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts_val or "")

@router.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(verify_api_key)])
async def view_dashboard(request: Request, tab: str = "all"):
    items = []
    
    async with get_connection() as conn:
        # Source 1: Staged items from chat_sessions (unconfirmed)
        if tab in ("all", "pending", "staged"):
            rows_staged = await conn.fetch("""
                SELECT c.id, c.sender_id, c.timestamp as created_at, c.staging_payload as payload,
                       c.raw_message, c.media_urls
                FROM chat_sessions c
                LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
                WHERE c.staging_payload IS NOT NULL AND h.id IS NULL
                ORDER BY c.timestamp DESC
            """)
            for r in rows_staged:
                raw_payload = r['payload']
                is_failed_api = (raw_payload == 'FAILED_API_LIMIT')
                payload = {}
                if isinstance(raw_payload, str) and not is_failed_api:
                    try:
                        payload = json.loads(raw_payload)
                    except Exception:
                        payload = {}
                elif isinstance(raw_payload, dict):
                    payload = raw_payload

                acc = str(payload.get('account_code') or payload.get('category') or '429').strip()
                tax = str(payload.get('tax_code') or payload.get('tax_rate') or payload.get('tax_type') or 'NONE').strip()
                gross = float(payload.get('amount') or payload.get('gross_amount') or 0.0)
                
                # Check for currency
                detected_curr = detect_currency(payload.get('vendor', '') + " " + (r.get('raw_message') or ''))
                
                reasoning = payload.get('reasoning', payload.get('reasoning_steps', ''))
                if not reasoning:
                    parts = [str(v) for k, v in payload.items() if k.startswith('reasoning_step_')]
                    reasoning = "\n".join(parts)

                items.append({
                    "id": r['id'],
                    "item_type": "staged",
                    "sender_id": r['sender_id'],
                    "created_at": format_ts(r['created_at']),
                    "vendor": payload.get('vendor', 'Unknown Supplier'),
                    "memo": payload.get('memo', payload.get('reasoning_step_2_nature_of_expense', '')),
                    "amount": gross,
                    "account_code": acc,
                    "tax_code": tax,
                    "currency": detected_curr,
                    "raw_message": r.get('raw_message') or 'No message text.',
                    "media_urls": r.get('media_urls', ''),
                    "reasoning": reasoning or 'Pre-confirmed intake staged.',
                    "status": "STAGED",
                    "status_label": "Unconfirmed",
                    "flagged": payload.get('is_ambiguous', False) or gross >= 500.0,
                    "is_capital_allowance": gross >= 500.0,
                    "is_duplicate": False,
                    "allowable_business_amount": float(payload.get('allowable_business_amount', gross)),
                    "business_proportion_percentage": payload.get('business_proportion_percentage', 100),
                    "is_failed_api": is_failed_api,
                    "accountant_approved": False,
                    "external_bill_id": None
                })

        # Source 2: Active items from hmrc_ledger
        status_filter = []
        if tab == "all":
            status_filter = ["CAPITAL_ALLOWANCE", "DUPLICATE_SUSPECTED", "NEEDS_REVIEW", "PENDING", "SUBMITTED", "FAILED"]
        elif tab == "capital_allowances":
            status_filter = ["CAPITAL_ALLOWANCE"]
        elif tab == "duplicates":
            status_filter = ["DUPLICATE_SUSPECTED"]
        elif tab == "pending":
            status_filter = ["PENDING", "NEEDS_REVIEW"]
        elif tab == "submitted":
            status_filter = ["SUBMITTED"]

        if status_filter:
            rows_ledger = await conn.fetch("""
                SELECT h.id as ledger_id, h.chat_id, h.timestamp as created_at, h.vendor as ledger_vendor,
                       h.amount as ledger_amount, h.category, h.status, h.encrypted_financial_data,
                       h.accountant_approved, h.external_bill_id, h.receipt_fingerprint,
                       c.sender_id, c.raw_message, c.media_urls
                FROM hmrc_ledger h
                LEFT JOIN chat_sessions c ON h.chat_id = c.id
                WHERE h.status = ANY($1::text[])
                ORDER BY h.id DESC
            """, status_filter)

            for r in rows_ledger:
                fin = {}
                if r['encrypted_financial_data'] and token_engine:
                    try:
                        decrypted_str = token_engine.decrypt_tokens(
                            json.loads(r['encrypted_financial_data']),
                            associated_data=str(r['chat_id'])
                        )
                        fin = json.loads(decrypted_str)
                    except Exception as dec_err:
                        logger.error(f"Failed to decrypt ledger {r['ledger_id']}: {dec_err}")
                        fin = {}

                gross = float(fin.get('gross_amount') or r['ledger_amount'] or 0.0)
                net = float(fin.get('net_amount') or gross)
                vat = float(fin.get('vat_amount') or 0.0)
                vendor = fin.get('vendor') or r['ledger_vendor'] or 'Unknown Supplier'
                acc = str(fin.get('account_code') or fin.get('category') or r['category'] or '429').strip()
                tax = str(fin.get('tax_code') or fin.get('tax_type') or ('INPUT2' if vat > 0 else 'NONE')).strip()
                curr = fin.get('currency', 'GBP')
                status = r['status']

                # Compute user-facing badge label
                if status == "CAPITAL_ALLOWANCE":
                    status_label = "Capital Asset"
                elif status == "DUPLICATE_SUSPECTED":
                    status_label = "Duplicate Suspected"
                elif status == "NEEDS_REVIEW":
                    status_label = "Needs Review"
                elif status == "PENDING":
                    status_label = "Queued to Xero"
                elif status == "SUBMITTED":
                    status_label = "Submitted"
                else:
                    status_label = status

                items.append({
                    "id": r['ledger_id'],
                    "item_type": "ledger",
                    "sender_id": r['sender_id'] or 'Unknown',
                    "created_at": format_ts(r['created_at']),
                    "vendor": vendor,
                    "memo": fin.get('memo') or fin.get('reasoning_step_2_nature_of_expense') or r['category'] or 'No memo',
                    "amount": gross,
                    "net_amount": net,
                    "vat_amount": vat,
                    "account_code": acc,
                    "tax_code": tax,
                    "currency": curr,
                    "raw_message": r.get('raw_message') or 'WhatsApp transaction recorded.',
                    "media_urls": r.get('media_urls', ''),
                    "reasoning": fin.get('reasoning') or fin.get('audit_memo') or f"Status: {status}. CAA 2001 & VATA 1994 ledger record.",
                    "status": status,
                    "status_label": status_label,
                    "flagged": status in ("CAPITAL_ALLOWANCE", "DUPLICATE_SUSPECTED", "NEEDS_REVIEW"),
                    "is_capital_allowance": (status == "CAPITAL_ALLOWANCE") or (gross >= 500.0),
                    "is_duplicate": (status == "DUPLICATE_SUSPECTED"),
                    "allowable_business_amount": gross,
                    "business_proportion_percentage": 100,
                    "is_failed_api": False,
                    "accountant_approved": r['accountant_approved'],
                    "external_bill_id": r['external_bill_id']
                })

    # Summary counts for tab headers
    async with get_connection() as conn:
        counts_res = await conn.fetch("""
            SELECT status, count(*) as count 
            FROM hmrc_ledger 
            GROUP BY status
        """)
        counts_map = {r['status']: r['count'] for r in counts_res}
        staged_count = await conn.fetchval("""
            SELECT count(*) FROM chat_sessions c
            LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
            WHERE c.staging_payload IS NOT NULL AND h.id IS NULL
        """)

    tabs_summary = {
        "all": sum(counts_map.values()) + (staged_count or 0),
        "capital_allowances": counts_map.get("CAPITAL_ALLOWANCE", 0),
        "duplicates": counts_map.get("DUPLICATE_SUSPECTED", 0),
        "pending": counts_map.get("PENDING", 0) + (staged_count or 0),
        "submitted": counts_map.get("SUBMITTED", 0)
    }

    context = {
        "request": request,
        "items": items,
        "current_tab": tab,
        "tabs_summary": tabs_summary,
        "account_labels": ACCOUNT_CODE_LABELS,
        "tax_labels": TAX_CODE_LABELS
    }
    template = templates.get_template("dashboard.html")
    return HTMLResponse(content=template.render(context))

@router.get("/dashboard/edit/{item_type}/{item_id}", response_class=HTMLResponse)
async def get_edit_row(request: Request, item_type: str, item_id: int):
    """Renders interactive inline triage form row with nominal code and tax selectors."""
    async with get_connection() as conn:
        vendor = "Unknown"
        amount = 0.0
        current_acc = "420"
        current_tax = "INPUT2"
        is_cap = False
        is_dup = False

        if item_type == "ledger":
            row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", item_id)
            if row:
                is_cap = (row["status"] == "CAPITAL_ALLOWANCE")
                is_dup = (row["status"] == "DUPLICATE_SUSPECTED")
                if row["encrypted_financial_data"] and token_engine:
                    try:
                        dec = token_engine.decrypt_tokens(
                            json.loads(row["encrypted_financial_data"]),
                            associated_data=str(row["chat_id"])
                        )
                        fin = json.loads(dec)
                        vendor = fin.get("vendor", row["vendor"])
                        amount = float(fin.get("gross_amount", row["amount"] or 0.0))
                        current_acc = str(fin.get("account_code") or fin.get("category") or "720" if is_cap else "420")
                        current_tax = str(fin.get("tax_type") or fin.get("tax_code") or "INPUT2")
                    except Exception:
                        pass
        else: # staged
            row = await conn.fetchrow("SELECT * FROM chat_sessions WHERE id = $1", item_id)
            if row and row["staging_payload"]:
                try:
                    payload = json.loads(row["staging_payload"])
                    vendor = payload.get("vendor", "Unknown")
                    amount = float(payload.get("amount") or payload.get("gross_amount") or 0.0)
                    is_cap = (amount >= 500.0)
                    current_acc = str(payload.get("account_code") or ("720" if is_cap else "420"))
                    current_tax = str(payload.get("tax_type") or payload.get("tax_code") or "INPUT2")
                except Exception:
                    pass

    # Build options HTML
    acc_options = []
    for code, label in ACCOUNT_CODE_LABELS.items():
        sel = "selected" if code == current_acc or code in current_acc else ""
        acc_options.append(f'<option value="{code}" {sel}>{label}</option>')
    acc_options_html = "\n".join(acc_options)

    tax_options = []
    for code, label in TAX_CODE_LABELS.items():
        sel = "selected" if code == current_tax or code in current_tax else ""
        tax_options.append(f'<option value="{code}" {sel}>{label}</option>')
    tax_options_html = "\n".join(tax_options)

    cap_checked = "checked" if is_cap or amount >= 500.0 else ""
    dup_checkbox_html = ""
    if is_dup:
        dup_checkbox_html = """
        <div class="flex items-center space-x-2 mt-2 bg-rose-50 p-2 rounded border border-rose-200">
            <input type="checkbox" id="allow_duplicate" name="allow_duplicate" value="true" class="h-4 w-4 text-rose-600 rounded">
            <label for="allow_duplicate" class="text-xs font-semibold text-rose-800">Override 90-Day Duplicate Gate (Force Push to Xero)</label>
        </div>
        """

    return HTMLResponse(f"""
    <tr class="bg-indigo-50 border-2 border-indigo-300" id="row-{item_type}-{item_id}">
        <td colspan="9" class="p-4">
            <form hx-post="/dashboard/triage/{item_type}/{item_id}" hx-target="#row-{item_type}-{item_id}" hx-swap="outerHTML" class="space-y-3">
                <div class="flex items-center justify-between pb-2 border-b border-indigo-200">
                    <span class="text-xs font-bold uppercase tracking-wider text-indigo-900 flex items-center">
                        <svg class="w-4 h-4 mr-1 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        Accountant Triage & Statutory Classification — {vendor} (£{amount:.2f})
                    </span>
                    <button type="button" hx-get="/dashboard" hx-target="body" class="text-xs text-gray-500 hover:text-gray-800">✕ Cancel</button>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                        <label class="block text-[11px] font-semibold text-gray-700 uppercase mb-1">Xero Account Code (P&L vs Balance Sheet)</label>
                        <select name="account_code" class="w-full text-xs border border-gray-300 rounded p-1.5 bg-white font-mono focus:ring-2 focus:ring-indigo-500">
                            {acc_options_html}
                        </select>
                        <p class="text-[10px] text-gray-500 mt-1">Select 710/720 for Capital Allowances (CAA 2001) > £500.</p>
                    </div>
                    <div>
                        <label class="block text-[11px] font-semibold text-gray-700 uppercase mb-1">VAT Treatment (VATA 1994)</label>
                        <select name="tax_type" class="w-full text-xs border border-gray-300 rounded p-1.5 bg-white font-mono focus:ring-2 focus:ring-indigo-500">
                            {tax_options_html}
                        </select>
                        <p class="text-[10px] text-gray-500 mt-1">Use 'NONE' for overseas or non-VAT receipts.</p>
                    </div>
                    <div class="flex flex-col justify-center">
                        <label class="flex items-center space-x-2 text-xs font-medium text-gray-800 cursor-pointer">
                            <input type="checkbox" name="is_capital_asset" value="true" {cap_checked} class="h-4 w-4 text-indigo-600 rounded">
                            <span>Statutory Capital Asset (AIA 100% / Fixed Asset)</span>
                        </label>
                        {dup_checkbox_html}
                    </div>
                </div>

                <div class="flex items-center justify-end space-x-2 pt-2 border-t border-indigo-200">
                    <button type="button" hx-post="/dashboard/reject/{item_type}/{item_id}" hx-target="#row-{item_type}-{item_id}" hx-swap="outerHTML" class="bg-rose-100 hover:bg-rose-200 text-rose-800 text-xs font-semibold px-3 py-1.5 rounded transition-colors">
                        Reject / Dismiss
                    </button>
                    <button type="submit" class="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold px-4 py-1.5 rounded shadow-sm transition-colors flex items-center">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        Release &amp; Push to Xero
                    </button>
                </div>
            </form>
        </td>
    </tr>
    """)

@router.post("/dashboard/triage/{item_type}/{item_id}", response_class=HTMLResponse)
async def submit_triage(
    request: Request,
    item_type: str,
    item_id: int,
    account_code: str = Form("420"),
    tax_type: str = Form("INPUT2"),
    is_capital_asset: bool = Form(False),
    allow_duplicate: bool = Form(False)
):
    """Updates ledger row with accountant-overridden account code & tax type, and queues to Xero."""
    from datetime import datetime, timezone
    now_ts = datetime.now(timezone.utc).isoformat()
    
    async with get_connection() as conn:
        if item_type == "ledger":
            row = await conn.fetchrow("SELECT * FROM hmrc_ledger WHERE id = $1", item_id)
            if not row:
                return HTMLResponse("<tr class='bg-rose-50'><td colspan='9' class='p-3 text-xs text-rose-700'>Record not found</td></tr>")
            
            fin = {}
            if row["encrypted_financial_data"] and token_engine:
                try:
                    dec = token_engine.decrypt_tokens(
                        json.loads(row["encrypted_financial_data"]),
                        associated_data=str(row["chat_id"])
                    )
                    fin = json.loads(dec)
                except Exception:
                    fin = {}

            # Apply accountant overrides
            fin["account_code"] = account_code
            fin["tax_type"] = tax_type
            fin["tax_code"] = tax_type
            fin["is_capital_allowance"] = is_capital_asset
            fin["accountant_triage_ts"] = now_ts
            fin["accountant_approved"] = True

            # Multi-Currency check
            gross = float(fin.get("gross_amount", row["amount"] or 0.0))
            curr = fin.get("currency", "GBP")
            if curr != "GBP":
                base_gross, base_vat, base_net, fx_meta = normalize_to_base_currency(gross, curr)
                fin["gross_amount"] = base_gross
                fin["net_amount"] = base_net
                fin["vat_amount"] = base_vat
                fin["fx_metadata"] = fx_meta
                # Statutory rule: Override UK tax on foreign invoices to NONE (0%)
                fin["tax_type"] = "NONE"
                fin["tax_code"] = "NONE"

            re_encrypted = json.dumps(token_engine.encrypt_tokens(
                json.dumps(fin),
                associated_data=str(row["chat_id"])
            )) if token_engine else None

            # Release item into PENDING with accountant approval!
            norm_amount = base_gross if curr != "GBP" else gross
            await conn.execute("""
                UPDATE hmrc_ledger 
                SET status = 'PENDING', 
                    accountant_approved = TRUE,
                    amount = $1,
                    encrypted_financial_data = $2,
                    updated_at = $3
                WHERE id = $4
            """, norm_amount, re_encrypted, now_ts, item_id)

        else: # staged item
            # Update chat_sessions staging_payload with new codes
            row = await conn.fetchrow("SELECT staging_payload FROM chat_sessions WHERE id = $1", item_id)
            if row and row["staging_payload"]:
                payload = json.loads(row["staging_payload"])
                payload["account_code"] = account_code
                payload["tax_type"] = tax_type
                payload["tax_code"] = tax_type
                payload["is_capital_allowance"] = is_capital_asset
                await conn.execute("UPDATE chat_sessions SET staging_payload = $1 WHERE id = $2", json.dumps(payload), item_id)

            queue_id = await confirm_and_queue_to_ledger(item_id, allow_duplicate=allow_duplicate)
            await conn.execute("""
                UPDATE hmrc_ledger 
                SET status = 'PENDING', 
                    accountant_approved = TRUE, 
                    updated_at = $1 
                WHERE id = $2
            """, now_ts, queue_id)

    return HTMLResponse(f"""
    <tr class="bg-emerald-50 transition-colors" id="row-{item_type}-{item_id}">
        <td colspan="9" class="px-6 py-4 text-xs font-semibold text-emerald-800 text-center flex items-center justify-center space-x-2">
            <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            <span>Approved &amp; Released to Xero! (Account: {account_code} | Tax: {tax_type})</span>
        </td>
    </tr>
    """)

@router.post("/dashboard/reject/{item_type}/{item_id}", response_class=HTMLResponse)
async def reject_item(request: Request, item_type: str, item_id: int):
    """Dismisses an item by setting status to REJECTED."""
    async with get_connection() as conn:
        if item_type == "ledger":
            await conn.execute("UPDATE hmrc_ledger SET status = 'REJECTED', updated_at = NOW() WHERE id = $1", item_id)
        else:
            await conn.execute("UPDATE chat_sessions SET staging_payload = NULL WHERE id = $1", item_id)

    return HTMLResponse(f"""
    <tr class="bg-gray-100 transition-colors opacity-60" id="row-{item_type}-{item_id}">
        <td colspan="9" class="px-6 py-3 text-xs text-gray-500 text-center">
            Item dismissed by accountant.
        </td>
    </tr>
    """)

# Backward compatibility routes
@router.post("/dashboard/approve/{item_id}", response_class=HTMLResponse)
async def approve_item(request: Request, item_id: int):
    """Direct one-click approval."""
    return await submit_triage(request, item_type="staged", item_id=item_id, account_code="420", tax_type="INPUT2")

@router.get("/dashboard/edit/{item_id}", response_class=HTMLResponse)
async def legacy_edit_item(request: Request, item_id: int):
    return await get_edit_row(request, item_type="staged", item_id=item_id)

@router.post("/dashboard/bulk-approve", response_class=HTMLResponse)
async def bulk_approve(request: Request):
    async with get_connection() as conn:
        rows = await conn.fetch("""
            SELECT c.id 
            FROM chat_sessions c
            LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
            WHERE c.staging_payload IS NOT NULL AND h.id IS NULL
        """)
        for r in rows:
            try:
                queue_id = await confirm_and_queue_to_ledger(r["id"])
                await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING', accountant_approved = TRUE WHERE id = $1", queue_id)
            except Exception as e:
                logger.error(f"Failed to bulk-approve {r['id']}: {e}")

    return await view_dashboard(request, tab="all")
