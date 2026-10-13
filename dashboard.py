# -*- coding: utf-8 -*-
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import json
import os
import datetime
from db import get_connection, confirm_and_queue_to_ledger
from security import (
    verify_accountant_session,
    verify_api_key,
    is_authenticated_request,
    is_valid_api_key,
    set_accountant_session_cookie,
    clear_accountant_session_cookie,
    is_safe_redirect,
)
from aes_gcm_security import TokenEncryptionEngine
from currency_converter import detect_currency, normalize_to_base_currency
from rate_limiter import limiter
import logging

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

def return_dashboard_response(request: Request, response: HTMLResponse) -> HTMLResponse:
    """Helper to attach session cookie if authenticated via magic link query parameter."""
    if getattr(request.state, "should_set_cookie", False):
        set_accountant_session_cookie(response, getattr(request.state, "accountant_session", None), secure=True)
    return response

@router.get("/dashboard/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/dashboard"):
    """Renders login page or redirects to dashboard if already authenticated."""
    if is_authenticated_request(request):
        target = next if is_safe_redirect(next, "/dashboard") else "/dashboard"
        return RedirectResponse(url=target, status_code=303)
    
    template = templates.get_template("login.html")
    return HTMLResponse(content=template.render({"request": request, "error": None, "next": next}))

@router.post("/dashboard/login")
@limiter.limit("5/minute")
async def login_submit(
    request: Request,
    access_key: str = Form(""),
    next: str = Form("/dashboard")
):
    """Authenticates access key, sets accountant_session cookie, and redirects to dashboard."""
    clean_key = access_key.strip()
    if is_valid_api_key(clean_key):
        target = next if is_safe_redirect(next, "/dashboard") else "/dashboard"
        response = RedirectResponse(url=target, status_code=303)
        set_accountant_session_cookie(response, secure=True, max_age=604800)
        return response
    
    template = templates.get_template("login.html")
    context = {
        "request": request,
        "error": "Invalid API access key. Please verify your credentials and try again.",
        "next": next,
    }
    return HTMLResponse(content=template.render(context), status_code=401)

@router.get("/dashboard/logout")
async def logout(request: Request):
    """Deletes accountant_session cookie and redirects to /dashboard/login."""
    response = RedirectResponse(url="/dashboard/login", status_code=303)
    clear_accountant_session_cookie(response, secure=True)
    return response

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
    "EXEMPTINPUT": "Exempt (0%) [EXEMPTINPUT]",
    "REVERSECHARGES": "Reverse Charge Expenses (20%) [REVERSECHARGES]"
}

def format_ts(ts_val) -> str:
    try:
        dt = datetime.datetime.fromisoformat(str(ts_val))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts_val or "")

@router.get("/dashboard", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
async def view_dashboard(request: Request, tab: str = "all"):
    items = []
    counts_map = {}
    staged_count = 0
    try:
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
    except Exception as e:
        logger.error(f"Error fetching dashboard items: {e}")

    # Summary counts for tab headers
    try:
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
    except Exception as e:
        logger.error(f"Error fetching dashboard summary counts: {e}")

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
    return return_dashboard_response(request, HTMLResponse(content=template.render(context)))

@router.get("/dashboard/edit/{item_type}/{item_id}", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
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

    response = HTMLResponse(f"""
    <tr class="bg-indigo-50 border-2 border-indigo-300" id="row-{item_type}-{item_id}">
        <td colspan="9" class="p-4">
            <form hx-post="/dashboard/triage/{item_type}/{item_id}" hx-target="#row-{item_type}-{item_id}" hx-swap="outerHTML" class="space-y-3">
                <div class="flex items-center justify-between pb-2 border-b border-indigo-200">
                    <span class="text-xs font-bold uppercase tracking-wider text-indigo-900 flex items-center">
                        <svg class="w-4 h-4 mr-1 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>
                        Accountant Triage &amp; Statutory Classification &mdash; {vendor} (&pound;{amount:.2f})
                    </span>
                    <button type="button" hx-get="/dashboard" hx-target="body" class="text-xs text-gray-500 hover:text-gray-800">&times; Cancel</button>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                        <label class="block text-[11px] font-semibold text-gray-700 uppercase mb-1">Xero Account Code (P&amp;L vs Balance Sheet)</label>
                        <select name="account_code" class="w-full text-xs border border-gray-300 rounded p-1.5 bg-white font-mono focus:ring-2 focus:ring-indigo-500">
                            {acc_options_html}
                        </select>
                        <p class="text-[10px] text-gray-500 mt-1">Select 710/720 for Capital Allowances (CAA 2001) > &pound;500.</p>
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
    return return_dashboard_response(request, response)

@router.get("/dashboard/inspect/{item_type}/{item_id}", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
async def inspect_drawer(request: Request, item_type: str, item_id: int):
    """Renders slide-over inspection drawer with receipt image, WhatsApp chat, and provenance memo."""
    vendor = "Unknown Supplier"
    amount = 0.0
    net = 0.0
    vat = 0.0
    current_acc = "420"
    current_tax = "INPUT2"
    is_cap = False
    is_dup = False
    memo = ""
    raw_msg = ""
    reasoning = ""
    media_url = ""
    sender_id = "Client"
    created_at = ""

    try:
        async with get_connection() as conn:
            if item_type == "ledger":
                row = await conn.fetchrow("""
                    SELECT h.*, c.sender_id, c.raw_message, c.media_urls
                    FROM hmrc_ledger h
                    LEFT JOIN chat_sessions c ON h.chat_id = c.id
                    WHERE h.id = $1
                """, item_id)
                if row:
                    is_cap = (row["status"] == "CAPITAL_ALLOWANCE")
                    is_dup = (row["status"] == "DUPLICATE_SUSPECTED")
                    sender_id = row["sender_id"] or "Unknown Client"
                    raw_msg = row["raw_message"] or "WhatsApp receipt upload."
                    media_url = row["media_urls"] or ""
                    created_at = format_ts(row["timestamp"])
                    vendor = row["vendor"] or "Unknown Supplier"
                    amount = float(row["amount"] or 0.0)
                    current_acc = str(row["category"] or ("720" if is_cap else "420"))
                    if row["encrypted_financial_data"] and token_engine:
                        try:
                            dec = token_engine.decrypt_tokens(
                                json.loads(row["encrypted_financial_data"]),
                                associated_data=str(row["chat_id"])
                            )
                            fin = json.loads(dec)
                            vendor = fin.get("vendor", vendor)
                            amount = float(fin.get("gross_amount", amount))
                            net = float(fin.get("net_amount", amount))
                            vat = float(fin.get("vat_amount", 0.0))
                            memo = fin.get("memo") or fin.get("reasoning_step_2_nature_of_expense") or ""
                            reasoning = fin.get("reasoning") or fin.get("audit_memo") or ""
                            current_acc = str(fin.get("account_code") or current_acc)
                            current_tax = str(fin.get("tax_type") or fin.get("tax_code") or "INPUT2")
                        except Exception:
                            pass
            else: # staged
                row = await conn.fetchrow("SELECT * FROM chat_sessions WHERE id = $1", item_id)
                if row:
                    sender_id = row["sender_id"] or "Unknown Client"
                    raw_msg = row["raw_message"] or "WhatsApp receipt upload."
                    media_url = row["media_urls"] or ""
                    created_at = format_ts(row["timestamp"])
                    if row["staging_payload"]:
                        try:
                            payload = json.loads(row["staging_payload"])
                            vendor = payload.get("vendor", "Unknown Supplier")
                            amount = float(payload.get("amount") or payload.get("gross_amount") or 0.0)
                            net = float(payload.get("net_amount") or amount)
                            vat = float(payload.get("vat_amount") or 0.0)
                            memo = payload.get("memo") or ""
                            reasoning = payload.get("reasoning") or ""
                            is_cap = (amount >= 500.0)
                            current_acc = str(payload.get("account_code") or ("720" if is_cap else "420"))
                            current_tax = str(payload.get("tax_type") or payload.get("tax_code") or "INPUT2")
                        except Exception:
                            pass
    except Exception as e:
        logger.error(f"Error in inspect_drawer: {e}")

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
    dup_alert = ""
    if is_dup:
        dup_alert = """
        <div class="bg-rose-50 border border-rose-200 rounded p-2.5 text-xs text-rose-800 flex items-start space-x-2">
            <input type="checkbox" id="allow_duplicate" name="allow_duplicate" value="true" class="h-4 w-4 text-rose-600 rounded mt-0.5">
            <label for="allow_duplicate" class="font-semibold cursor-pointer">Override 90-Day Duplicate Warning (Force push to Xero)</label>
        </div>
        """

    # Schedule 24 Auditor Conflict Resolver (CRCO Compliance Engine)
    conflict_detected = False
    conflict_reason = ""
    lower_msg = (raw_msg or "").lower()
    lower_vendor = (vendor or "").lower()

    if any(k in lower_msg for k in ["personal", "home", "private", "present", "gift", "for my wife", "for my kid"]):
        conflict_detected = True
        conflict_reason = "Client indicated personal or non-business expenditure in WhatsApp dialogue. Reclaiming input tax or business expense may incur Schedule 24 FA 2007 carelessness penalties."
    elif any(s in lower_vendor for s in ["tesco", "sainsbury", "asda", "morrisons", "waitrose", "marks & spencer", "m&s"]):
        if any(w in lower_msg for w in ["tools", "materials", "van parts"]):
            conflict_detected = True
            conflict_reason = "Client claimed 'materials/tools' at a retail supermarket. High probability of non-deductible personal groceries or mixed-rate basket."
        elif "fuel" not in lower_msg and "petrol" not in lower_msg:
            conflict_detected = True
            conflict_reason = "Supermarket receipt without explicit fuel itemisation. Food items may be zero-rated or disallowable entertaining (BIM45000)."
    elif is_cap and current_acc in ("420", "429", "310", "400"):
        conflict_detected = True
        conflict_reason = f"Expenditure (&pound;{amount:.2f}) exceeds the &pound;500 threshold but is currently allocated to Expense code {current_acc}. AIA 100% Capital Allowance review required."

    conflict_banner = ""
    if conflict_detected:
        conflict_banner = f"""
        <div class="bg-amber-50 border-2 border-amber-300 rounded-lg p-3 text-xs text-amber-900 shadow-xs">
            <div class="flex items-center space-x-1.5 font-bold text-amber-900 mb-1">
                <svg class="w-4 h-4 text-amber-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>
                <span>SCHEDULE 24 AUDITOR CONFLICT WARNING</span>
            </div>
            <p class="leading-relaxed font-sans">{conflict_reason}</p>
            <div class="mt-2 text-[10px] text-amber-800 font-mono">
                Statutory Sign-off Required &bull; VATA 1994 s84 &amp; TMA 1970 s12B
            </div>
        </div>
        """

    drc_verification = ""
    if current_tax == "REVERSECHARGES":
        drc_verification = """
        <div class="bg-amber-50 border border-amber-300 rounded p-2 text-xs text-amber-900 flex items-start space-x-2">
            <input type="checkbox" id="drc_end_user" name="drc_end_user_confirmed" value="true" class="h-4 w-4 text-amber-600 rounded mt-0.5" required>
            <label for="drc_end_user" class="font-semibold cursor-pointer">
                Confirmed: Customer is CIS &amp; VAT registered and NOT an End User (HMRC Notice 735)
            </label>
        </div>
        """

    media_display = ""
    if media_url and media_url.startswith("http"):
        media_display = f"""
        <div class="bg-slate-950 rounded-lg p-2 relative flex flex-col items-center justify-center overflow-hidden border border-slate-700 min-h-64 max-h-96">
            <!-- Canvas Controls -->
            <div class="absolute top-2 right-2 z-10 flex items-center space-x-1 bg-slate-900/90 p-1 rounded border border-slate-700 text-xs backdrop-blur-xs">
                <button type="button" onclick="window.receiptZoom(0.2)" class="text-slate-300 hover:text-white px-1.5 py-0.5 rounded hover:bg-slate-800" title="Zoom In [+]">+</button>
                <button type="button" onclick="window.receiptZoom(-0.2)" class="text-slate-300 hover:text-white px-1.5 py-0.5 rounded hover:bg-slate-800" title="Zoom Out [-]">-</button>
                <button type="button" onclick="window.receiptRotate()" class="text-slate-300 hover:text-white px-1.5 py-0.5 rounded hover:bg-slate-800" title="Rotate 90deg [R]">Rotate</button>
                <button type="button" onclick="window.receiptToggleThermal()" class="text-amber-400 hover:text-amber-300 px-1.5 py-0.5 rounded hover:bg-slate-800 font-bold" title="Faded Thermal Receipt Enhance [T]">Thermal B&amp;W</button>
                <button type="button" onclick="window.receiptReset()" class="text-slate-400 hover:text-slate-200 px-1.5 py-0.5 rounded hover:bg-slate-800" title="Reset View [0]">100%</button>
            </div>
            
            <div id="receipt-canvas-viewport" class="overflow-auto w-full h-full flex items-center justify-center p-2">
                <img id="active-receipt-img" src="{media_url}" alt="Receipt Canvas" 
                     class="max-h-80 w-auto object-contain rounded transition-all duration-150 cursor-grab active:cursor-grabbing" 
                     style="transform: scale(1) rotate(0deg);">
            </div>
        </div>
        """
    else:
        media_display = """
        <div class="bg-slate-100 rounded-lg p-4 border border-slate-200 text-center flex flex-col items-center justify-center">
            <svg class="w-8 h-8 text-slate-400 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
            <span class="text-xs font-semibold text-slate-600">Digital Link Archive Record</span>
            <span class="text-[10px] text-slate-400">Notice 700/22 Section 3.3 Digital Link Verified</span>
        </div>
        """

    formatted_amount = "%.2f" % amount
    content = f"""
    <div class="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
        <div>
            <div class="flex items-center space-x-2">
                <span class="text-xs font-mono font-bold text-slate-500 uppercase">{item_type} #{item_id}</span>
                <span class="text-sm font-bold text-slate-900">{vendor}</span>
            </div>
            <span class="text-xs text-slate-500">{created_at} &bull; {sender_id}</span>
        </div>
        <div class="flex items-center space-x-3">
            <span class="text-base font-mono font-bold text-slate-900">&pound;{formatted_amount}</span>
            <button onclick="window.closeDrawer()" class="text-slate-400 hover:text-slate-700 text-sm p-1 rounded hover:bg-slate-200 transition-colors" title="Close Drawer [Esc]">&times;</button>
        </div>
    </div>

    <div class="p-4 space-y-4 overflow-y-auto flex-1">
        <!-- Receipt Canvas Viewer -->
        {media_display}

        <!-- Schedule 24 Conflict Banner (if any) -->
        {conflict_banner}

        <!-- WhatsApp Conversation Provenance -->
        <div class="bg-emerald-50/70 border border-emerald-200/80 rounded-lg p-3 text-xs">
            <div class="flex items-center space-x-1.5 text-emerald-800 font-bold mb-1">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.711 2.598 2.664-.699c.971.53 1.84.814 2.796.814 3.18 0 5.767-2.587 5.768-5.766.001-3.181-2.587-5.768-5.768-5.768zm0 10.355c-.868 0-1.666-.242-2.381-.7l-.17-.101-1.77.464.473-1.724-.112-.178c-.496-.789-.757-1.554-.757-2.35 0-2.532 2.06-4.593 4.593-4.593 2.534 0 4.594 2.061 4.594 4.593 0 2.533-2.06 4.594-4.593 4.594z"/></svg>
                <span>WhatsApp Client Intake Memo</span>
            </div>
            <p class="font-mono text-slate-700 bg-white/80 p-2 rounded border border-emerald-100 whitespace-pre-wrap">{raw_msg}</p>
        </div>

        <!-- Statutory Provenance Memo -->
        <div class="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-1">
            <div class="font-semibold text-slate-800 flex items-center space-x-1">
                <svg class="w-3.5 h-3.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                <span>Tax &amp; Compliance Audit Memo</span>
            </div>
            <p class="text-slate-600 leading-relaxed font-sans">{reasoning or 'Standard business expense classification under FRS 105 and VATA 1994.'}</p>
        </div>

        <!-- Triage & Allocation Form -->
        <form hx-post="/dashboard/triage/{item_type}/{item_id}" hx-target="#row-{item_type}-{item_id}" hx-swap="outerHTML" onsubmit="window.closeDrawer()" class="space-y-3 pt-2 border-t border-slate-200">
            <div>
                <label class="block text-[11px] font-bold text-slate-700 uppercase mb-1">Xero Nominal Code</label>
                <select name="account_code" class="w-full text-xs border border-slate-300 rounded p-1.5 bg-white font-mono focus:ring-2 focus:ring-blue-600">
                    {acc_options_html}
                </select>
            </div>

            <div>
                <label class="block text-[11px] font-bold text-slate-700 uppercase mb-1">VAT Treatment (VATA 1994)</label>
                <select name="tax_type" class="w-full text-xs border border-slate-300 rounded p-1.5 bg-white font-mono focus:ring-2 focus:ring-blue-600">
                    {tax_options_html}
                </select>
            </div>

            <div class="flex items-center space-x-2 pt-1">
                <input type="checkbox" id="drawer_is_cap" name="is_capital_asset" value="true" {cap_checked} class="h-4 w-4 text-blue-600 rounded">
                <label for="drawer_is_cap" class="text-xs font-medium text-slate-800 cursor-pointer">
                    Capital Asset (CAA 2001 &gt; &pound;500 AIA)
                </label>
            </div>

            {drc_verification}
            {dup_alert}

            <div class="flex items-center space-x-2 pt-3">
                <button type="submit" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs py-2 px-3 rounded shadow-sm transition-colors flex items-center justify-center space-x-1.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                    <span>Approve &amp; Push to Xero [Ctrl+Enter]</span>
                </button>
                <button type="button" hx-post="/dashboard/reject/{item_type}/{item_id}" hx-target="#row-{item_type}-{item_id}" hx-swap="outerHTML" onclick="window.closeDrawer()" class="bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-semibold py-2 px-3 rounded transition-colors">
                    Reject [Del]
                </button>
            </div>
        </form>
    </div>
    """
    return return_dashboard_response(request, HTMLResponse(content=content))

@router.post("/dashboard/triage/{item_type}/{item_id}", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
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
                vendor_val = fin.get("vendor") or fin.get("merchant")
                desc_val = fin.get("memo") or fin.get("description")
                cat_val = fin.get("category")
                base_gross, base_vat, base_net, fx_meta = normalize_to_base_currency(
                    gross, curr,
                    vendor=vendor_val,
                    description=desc_val,
                    category=cat_val
                )
                fin["gross_amount"] = base_gross
                fin["net_amount"] = base_net
                fin["vat_amount"] = base_vat
                fin["fx_metadata"] = fx_meta
                # Statutory rule (VATA 1994 s8): Retain Reverse Charge if applicable
                rc_tax = fx_meta.get("tax_type_override", "NONE")
                if tax_type and tax_type in ("REVERSECHARGES", "NONE", "INPUT2", "INPUT"):
                    fin["tax_type"] = tax_type
                    fin["tax_code"] = tax_type
                else:
                    fin["tax_type"] = rc_tax
                    fin["tax_code"] = rc_tax

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
            row = await conn.fetchrow("SELECT staging_payload FROM chat_sessions WHERE id = $1", item_id)
            if not row or not row["staging_payload"]:
                return HTMLResponse("<tr class='bg-rose-50'><td colspan='9' class='p-3 text-xs text-rose-700'>Staged payload not found</td></tr>", status_code=404)
            payload = json.loads(row["staging_payload"])
            payload["account_code"] = account_code
            payload["tax_type"] = tax_type
            payload["tax_code"] = tax_type
            payload["is_capital_allowance"] = is_capital_asset
            await conn.execute("UPDATE chat_sessions SET staging_payload = $1 WHERE id = $2", json.dumps(payload), item_id)

            try:
                queue_id = await confirm_and_queue_to_ledger(item_id, allow_duplicate=allow_duplicate)
            except ValueError as ve:
                return HTMLResponse(f"<tr class='bg-rose-50'><td colspan='9' class='p-3 text-xs text-rose-700'>{ve}</td></tr>", status_code=400)

            await conn.execute("""
                UPDATE hmrc_ledger 
                SET status = 'PENDING', 
                    accountant_approved = TRUE, 
                    updated_at = $1 
                WHERE id = $2
            """, now_ts, queue_id)

    response = HTMLResponse(f"""
    <tr class="bg-emerald-50 transition-colors" id="row-{item_type}-{item_id}">
        <td colspan="9" class="px-6 py-4 text-xs font-semibold text-emerald-800 text-center flex items-center justify-center space-x-2">
            <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            <span>Approved &amp; Released to Xero! (Account: {account_code} | Tax: {tax_type})</span>
        </td>
    </tr>
    """)
    return return_dashboard_response(request, response)

@router.post("/dashboard/reject/{item_type}/{item_id}", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
async def reject_item(request: Request, item_type: str, item_id: int):
    """Dismisses an item by setting status to REJECTED."""
    async with get_connection() as conn:
        if item_type == "ledger":
            await conn.execute("UPDATE hmrc_ledger SET status = 'REJECTED', updated_at = NOW() WHERE id = $1", item_id)
        else:
            await conn.execute("UPDATE chat_sessions SET staging_payload = NULL WHERE id = $1", item_id)

    response = HTMLResponse(f"""
    <tr class="bg-gray-100 transition-colors opacity-60" id="row-{item_type}-{item_id}">
        <td colspan="9" class="px-6 py-3 text-xs text-gray-500 text-center">
            Item dismissed by accountant.
        </td>
    </tr>
    """)
    return return_dashboard_response(request, response)

# Backward compatibility routes
@router.post("/dashboard/approve/{item_id}", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
async def approve_item(request: Request, item_id: int):
    """Direct one-click approval."""
    return await submit_triage(request, item_type="staged", item_id=item_id, account_code="420", tax_type="INPUT2")

@router.get("/dashboard/edit/{item_id}", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
async def legacy_edit_item(request: Request, item_id: int):
    return await get_edit_row(request, item_type="staged", item_id=item_id)

@router.post("/dashboard/bulk-approve", response_class=HTMLResponse, dependencies=[Depends(verify_accountant_session)])
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
