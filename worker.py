import asyncio
import time
import os
import json
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from db import (
    get_connection,
    get_pending_hmrc_queue,
    mark_hmrc_submitted,
    update_ledger_external_bill_id,
    update_ledger_attachment_status,
    get_identity_from_vault,
    store_identity_in_vault
)
from logger import get_logger
class HMRCApiError(Exception):
    def __init__(self, message, status_code, payload):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
from aes_gcm_security import TokenEncryptionEngine
from currency_converter import detect_currency, normalize_to_base_currency

logger = get_logger(__name__)

def get_twilio_client():
    from twilio.rest import Client
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')
    if sid and token: return Client(sid, token)
    return None

async def send_failure_sms(sender_id: str):
    if not sender_id or sender_id.startswith("demo_web_"): return
    import asyncio
    client = get_twilio_client()
    if not client: return
    to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
    from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034')
    try:
        await asyncio.to_thread(
            client.messages.create,
            body="Alert: Your expense submission failed due to an integration issue (e.g. token expired). Please re-authenticate.",
            from_=from_number,
            to=to_formatted
        )
    except Exception as e:
        logger.error("Failed to send Twilio SMS", error=str(e))


# Initialize Token Encryption Engine
encryption_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
if not encryption_key:
    raise ValueError("ENCRYPTION_MASTER_KEY_B64 environment variable is missing in worker.py.")
    
token_engine = TokenEncryptionEngine(encryption_key)

hmrc_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15)


from adapters.universal_adapter import UniversalAdapter
from models.unified_record import UnifiedFinancialRecord, TargetSystem

universal_adapter = UniversalAdapter()

HMRC_TO_XERO_ACCOUNT_MAP = {
    # Official HMRC Categories mapped to live Chart of Accounts
    "Turnover / Sales Income": "200",
    "Cost of goods sold": "310",
    "Construction industry costs": "485",
    "Staff costs": "477",
    "Travel costs": "404",
    "Premises running costs": "449",
    "Repairs and maintenance": "489",
    "Admin costs": "420",
    "Advertising and marketing": "400",
    "Interest on loans": "473",
    "Bank and financial charges": "416",
    "Professional fees": "412",
    "Depreciation and loss of assets": "710",
    "Other expenses": "429",
    "Non-allowable": "408",
    # Specific / alias categories
    "Phone, fax, stationery and other office costs": "420",
    "Office Supplies": "420",
    "Stationery": "420",
    "Printing & Stationery": "420",
    "Telephone & Internet": "441",
    "Utilities": "445",
    "Rent": "449",
    "Motor Vehicle Expenses": "453",
    "Subscriptions": "461",
    "Consulting & Accounting": "412",
    "Legal expenses": "437",
    "Insurance": "433",
    "Bad Debts": "469",
    "Wages and Salaries": "477",
    "Subcontractor Costs": "485",
    "General Expense": "429",
    "Other business expenses": "429"
}

def map_category_to_xero_account(category: str | None) -> str:
    if not category:
        return "429"
    if category in HMRC_TO_XERO_ACCOUNT_MAP:
        return HMRC_TO_XERO_ACCOUNT_MAP[category]
    cat_lower = str(category).lower()
    for hmrc_cat, code in HMRC_TO_XERO_ACCOUNT_MAP.items():
        if hmrc_cat.lower() in cat_lower or cat_lower in hmrc_cat.lower():
            return code
    return "429"

def normalize_date_str(date_val: str | None, fallback_val: str | None = None) -> str:
    clean_val = str(date_val or fallback_val or "").strip()
    if len(clean_val) >= 10 and clean_val[4] == '-' and clean_val[7] == '-':
        return clean_val[:10]
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(clean_val[:19], fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

async def submit_to_hmrc(item):
    try:
        if item.get("status") == "DUPLICATE_SUSPECTED" and not item.get("accountant_approved"):
            logger.warning("Item marked as DUPLICATE_SUSPECTED without approval. Skipping Xero submission to prevent duplication.", queue_id=item.get("id"))
            return
            
        sender_id = item.get("sender_id")
        if not sender_id and item.get("chat_id"):
            from db import get_connection
            async with get_connection() as conn:
                sender_id = await conn.fetchval("SELECT sender_id FROM chat_sessions WHERE id = $1", item["chat_id"])
        if not sender_id:
            sender_id = "447123456789"
            
        from accounting_client import AccountingClient
        client = AccountingClient(workspace_id=sender_id, provider="XERO")
        
        fin_data = {}
        if item.get("encrypted_financial_data"):
            import json
            enc_dict = json.loads(item["encrypted_financial_data"])
            decrypted_json = token_engine.decrypt_tokens(enc_dict, associated_data=str(item["chat_id"]))
            fin_data = json.loads(decrypted_json)
            amount = float(fin_data.get("gross_amount") or fin_data.get("amount", 0.0))
        else:
            amount = float(item["amount"])
        
        accountant_approved = item.get("accountant_approved", False)
        cap_threshold = 500.0
        if item.get("practice_id"):
            from db import get_connection
            async with get_connection() as conn:
                pt = await conn.fetchval("SELECT capitalisation_threshold_gbp FROM practices WHERE id = $1", item["practice_id"])
                if pt is not None:
                    cap_threshold = float(pt)

        if not accountant_approved and ((amount > cap_threshold and fin_data.get("transaction_type", "EXPENSE") != "INCOME") or fin_data.get("needs_accountant_review")):
            from db import get_connection
            async with get_connection() as conn:
                await conn.execute("UPDATE hmrc_ledger SET status = 'CAPITAL_ALLOWANCE' WHERE id = $1", item["id"])
            return
            
        def safe_float(val, default=0.0):
            if val is None: return float(default)
            try: return float(val)
            except: return float(default)
        
        net = safe_float(fin_data.get("net_amount", amount), amount)
        tax = safe_float(fin_data.get("vat_amount", 0.0), 0.0)
        gross = safe_float(fin_data.get("gross_amount", amount), amount)

        tx_date = normalize_date_str(fin_data.get("date") or fin_data.get("receipt_date") or fin_data.get("transaction_date"), item.get("timestamp"))
        due_date = normalize_date_str(fin_data.get("due_date"), tx_date)
        vendor_name = fin_data.get("vendor") or "Unknown Supplier"
        category_name = item.get("category") or fin_data.get("category") or "General Expense"

        # Multi-Currency & Overseas Reverse Charge Handling (VATA 1994 s8, Sch 6 Para 11 & VAT Notice 700 §7.6)
        raw_curr = fin_data.get("currency")
        if not raw_curr:
            raw_curr = detect_currency(
                f"{fin_data.get('vendor', '')} {fin_data.get('description', '')} {item.get('raw_message', '')}"
            )
        is_foreign = (raw_curr and raw_curr.upper() != "GBP")
        fx_annotation = ""
        is_reverse_charge = False
        if is_foreign and not fin_data.get("fx_metadata"):
            base_gross, base_vat, base_net, fx_meta = normalize_to_base_currency(
                amount=gross if gross > 0 else amount,
                currency=raw_curr,
                vat_amount=tax,
                vendor=vendor_name,
                description=fin_data.get("description"),
                category=category_name
            )
            gross = base_gross
            net = base_net
            tax = 0.0  # Base line tax is 0.0; deemed 20% output/input VAT is accounted via REVERSECHARGES
            is_reverse_charge = fx_meta.get("is_reverse_charge", False)
            fx_annotation = fx_meta.get("annotation", "")
            fin_data["gross_amount"] = gross
            fin_data["net_amount"] = net
            fin_data["vat_amount"] = tax
            fin_data["tax_code"] = "REVERSECHARGES" if is_reverse_charge else "NONE"
            fin_data["tax_type"] = "REVERSECHARGES" if is_reverse_charge else "NONE"
            fin_data["fx_metadata"] = fx_meta
        elif fin_data.get("fx_metadata"):
            fx_annotation = fin_data["fx_metadata"].get("annotation", "")
            is_reverse_charge = fin_data["fx_metadata"].get("is_reverse_charge", False)
        
        if abs((net + tax) - gross) > 0.01:
            raise Exception(f"Math Validation Failed: Net ({net}) + Tax ({tax}) != Gross ({gross})")
        
        # Priority for AccountCode: Accountant triage override -> AI classification -> Category map
        account_code = str(fin_data.get("account_code") or map_category_to_xero_account(category_name)).strip()
        
        # Match Contact (Name + ContactID if matched in live tenant)
        matched_contact = await client.find_contact(vendor_name)
        contact_payload = matched_contact if matched_contact else {"Name": vendor_name}

        inv_number = fin_data.get("invoice_number") or fin_data.get("receipt_number") or f"REC-{item['id']}"
        ref_code = fin_data.get("reference") or f"REC-{item['id']}"
        if fx_annotation and raw_curr and raw_curr.upper() != "GBP":
            ref_code = f"{ref_code} {raw_curr.upper()}"[:50]

        # Priority for TaxType: Foreign Reverse Charge -> Foreign None -> Accountant triage override -> Default INPUT/NONE
        if is_foreign:
            tax_code = "REVERSECHARGES" if is_reverse_charge else "NONE"
        elif fin_data.get("tax_type"):
            tax_code = str(fin_data.get("tax_type")).strip()
        elif fin_data.get("tax_code"):
            tax_code = str(fin_data.get("tax_code")).strip()
        else:
            tax_code = "INPUT" if tax > 0 else "NONE"

        detail_desc = fin_data.get("description") or fin_data.get("reasoning_step_2_nature_of_expense")
        if detail_desc:
            line_desc = f"{detail_desc} ({category_name})"
        else:
            line_desc = f"Purchased from {vendor_name} ({category_name})"
        if fx_annotation:
            line_desc = f"{line_desc} {fx_annotation}"

        line_items_data = fin_data.get("line_items")
        if line_items_data and isinstance(line_items_data, list) and len(line_items_data) > 0:
            formatted_lines = []
            for idx, li in enumerate(line_items_data):
                li_desc = li.get("description") or f"Item {idx+1} ({category_name})"
                if fx_annotation:
                    li_desc = f"{li_desc} {fx_annotation}"
                li_qty = safe_float(li.get("quantity", 1), 1.0)
                if li_qty <= 0:
                    li_qty = 1.0
                li_unit = safe_float(li.get("unit_amount") or li.get("net_amount") or li.get("amount", net), net)
                li_tax = 0.0 if is_foreign else safe_float(li.get("vat_amount") or li.get("tax_amount", 0.0), 0.0)
                li_acc = str(li.get("account_code") or fin_data.get("account_code") or map_category_to_xero_account(li.get("category") or category_name)).strip()
                if is_foreign:
                    li_tax_type = "REVERSECHARGES" if is_reverse_charge else "NONE"
                else:
                    li_tax_type = str(li.get("tax_type") or li.get("tax_code") or ("INPUT" if li_tax > 0 else "NONE")).strip()
                formatted_lines.append({
                    "Description": li_desc,
                    "Quantity": li_qty,
                    "UnitAmount": li_unit,
                    "AccountCode": li_acc,
                    "TaxType": li_tax_type,
                    "TaxAmount": li_tax
                })
        else:
            formatted_lines = [{
                "Description": line_desc,
                "Quantity": 1,
                "UnitAmount": net,
                "AccountCode": account_code,
                "TaxType": tax_code,
                "TaxAmount": tax
            }]


        bill_payload = {
            "Type": "ACCPAY",
            "Status": "DRAFT",
            "LineAmountTypes": "Exclusive",
            "Date": tx_date,
            "DueDate": due_date,
            "InvoiceNumber": inv_number,
            "Reference": ref_code,
            "Contact": contact_payload,
            "LineItems": formatted_lines
        }
        # Two-Phase Idempotency Engine
        # Step 1: Check if external_bill_id is already populated (in memory or database)
        invoice_id = item.get("external_bill_id")
        if not invoice_id and item.get("id"):
            from db import get_connection
            async with get_connection() as conn:
                invoice_id = await conn.fetchval(
                    "SELECT external_bill_id FROM hmrc_ledger WHERE id = $1", item["id"]
                )

        # Drop-before-ACK Pre-Flight Query on retries / crash recovery:
        # If this item has been retried (retry_count > 0) and invoice_id is still None,
        # query Xero by unique Reference to prevent duplicate bills if a previous attempt
        # timed out after Xero created the bill but before client received ACK.
        retry_count = item.get("retry_count") or 0
        if not invoice_id and retry_count > 0 and ref_code:
            try:
                logger.info("Drop-before-ACK Pre-Flight: Checking Xero for existing bill by Reference on retry...", queue_id=item["id"], retry_count=retry_count, reference=ref_code)
                existing_invoices = await client.get_invoices(where=f'Reference == "{ref_code}"')
                if existing_invoices and len(existing_invoices) > 0:
                    matched_inv = existing_invoices[0]
                    found_id = matched_inv.get("InvoiceID")
                    if found_id:
                        logger.warning(
                            "Drop-before-ACK Pre-Flight HIT: Found existing Xero bill by Reference. Adopting existing InvoiceID to avoid duplicate.",
                            queue_id=item["id"],
                            reference=ref_code,
                            invoice_id=found_id
                        )
                        await update_ledger_external_bill_id(item["id"], found_id)
                        invoice_id = found_id
                        item["external_bill_id"] = found_id
            except Exception as e:
                logger.error("Pre-flight reference lookup failed (proceeding to normal creation flow)", error=str(e), queue_id=item["id"])

        if not invoice_id:
            # Step 2: Create draft bill in Xero and IMMEDIATELY write external_bill_id to hmrc_ledger in database
            logger.info("Phase 1: Creating draft bill in Xero...", queue_id=item["id"])
            resp = await client.create_draft_bill(bill_payload)
            invoices = resp.get("Invoices", [])
            if not invoices or not invoices[0].get("InvoiceID"):
                raise Exception(f"Failed to obtain InvoiceID from Xero response: {resp}")
            invoice_id = invoices[0]["InvoiceID"]
            
            # Persist external_bill_id immediately before proceeding to attachment uploads
            await update_ledger_external_bill_id(item["id"], invoice_id)
            item["external_bill_id"] = invoice_id
            logger.info("Phase 1 Complete: Draft bill created & external_bill_id persisted immediately", queue_id=item["id"], external_bill_id=invoice_id)
        else:
            # Step 3: external_bill_id already populated (prior crash/retry) -> SKIP bill creation completely!
            logger.info("Phase 1 Skipped: external_bill_id already exists. Reusing existing bill (Idempotent replay)", queue_id=item["id"], external_bill_id=invoice_id)
            item["external_bill_id"] = invoice_id

        # Step 4: Proceed to attachment upload using external_bill_id (Failure-Isolated Two-Phase Commit)
        media_urls = item.get("media_urls") or []
        if isinstance(media_urls, str):
            try:
                import json
                media_urls = json.loads(media_urls)
            except Exception:
                media_urls = [media_urls] if media_urls.startswith("http") else []
        
        attachment_status = "NO_ATTACHMENT"
        last_sha256 = None
        last_att_id = None
        attachment_error = None

        if invoice_id and media_urls:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as dl_client:
                for idx, m_url in enumerate(media_urls):
                    try:
                        img_resp = await dl_client.get(m_url)
                        if img_resp.status_code == 200:
                            filename = f"receipt_{item['id']}_{idx}"
                            att_result = await client.upload_attachment(
                                invoice_id=invoice_id, 
                                filename=filename, 
                                file_bytes=img_resp.content
                            )
                            attachment_status = "ATTACHED"
                            last_sha256 = att_result.get("sha256")
                            last_att_id = att_result.get("attachment_id")
                            logger.info("Receipt attachment uploaded & cryptographically sealed", 
                                        queue_id=item["id"], 
                                        sha256=last_sha256, 
                                        attachment_id=last_att_id)
                        else:
                            attachment_status = "ATTACHMENT_FAILED"
                            attachment_error = f"HTTP {img_resp.status_code} downloading receipt from media URL"
                            logger.error("Failed to download receipt attachment", 
                                         queue_id=item["id"], 
                                         status_code=img_resp.status_code)
                    except Exception as upload_err:
                        attachment_status = "ATTACHMENT_FAILED"
                        attachment_error = str(upload_err)
                        logger.error("Failed to upload attachment to Xero (Failure Isolation: Draft bill retained)", 
                                     queue_id=item["id"], 
                                     error=str(upload_err))
            
            await update_ledger_attachment_status(
                item["id"], 
                status=attachment_status, 
                sha256=last_sha256, 
                xero_attachment_id=last_att_id, 
                error=attachment_error
            )
        else:
            await update_ledger_attachment_status(item["id"], status="NO_ATTACHMENT")

        # Step 5: Mark the item as SUBMITTED with attachment audit trail
        await mark_hmrc_submitted(
            item["id"], 
            external_bill_id=invoice_id,
            attachment_status=attachment_status,
            attachment_sha256=last_sha256,
            xero_attachment_id=last_att_id
        )
        logger.info("PROCESSING -> SUBMITTED", queue_id=item["id"], external_bill_id=invoice_id, attachment_status=attachment_status)
        
    except Exception as e:
        status_code = getattr(e, 'status_code', 500)
        logger.error("HMRC API Error", queue_id=item["id"], status=status_code, error=str(e))
        
        if status_code in (401, 403, 429, 500, 502, 503, 504):
            logger.info("Transient/Auth error, applying exponential backoff", queue_id=item["id"])
            from db import get_connection
            async with get_connection() as conn:
                if status_code in (401, 403):
                    logger.warning("401/403 Unauthorized - wiping token for re-auth", whatsapp_id=item["sender_id"])
                    await conn.execute("DELETE FROM accounting_connections WHERE workspace_id = $1", item["sender_id"])
                    await conn.execute("UPDATE hmrc_ledger SET status = 'AUTH_EXPIRED' WHERE id = $1", item["id"])
                    return
                else:
                    row = await conn.fetchrow("""
                        UPDATE hmrc_ledger 
                        SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                            retry_count = retry_count + 1,
                            next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                        WHERE id = $1
                        RETURNING status
                    """, item["id"])
                    if row and row["status"] == 'FAILED':
                        pass
                    raise e
        else:
            from db import get_connection
            async with get_connection() as conn:
                await conn.execute("UPDATE hmrc_ledger SET status = 'FAILED' WHERE id = $1", item["id"])
            logger.info("[91mPROCESSING -> FAILED[0m", queue_id=item["id"])
            raise e

async def process_hmrc_queue(semaphore):
    while True:
        try:
            pending_items = await get_pending_hmrc_queue()

            async def process_item(item):
                try:
                    async with semaphore:
                        logger.info("Submitting Queue ID to HMRC API", queue_id=item["id"])
                        await hmrc_breaker.async_call(submit_to_hmrc, item)
                    logger.info("Queue ID successfully submitted", queue_id=item["id"])
                except CircuitBreakerOpenException:
                    logger.warning("Circuit is OPEN. Pausing queue processing", recovery_timeout=hmrc_breaker.recovery_timeout)
                    from db import get_connection
                    async with get_connection() as conn:
                        await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE id = $1", item["id"])
                    raise
                except Exception as e:
                    # submit_to_hmrc handles DB updates (exponential backoff or permanent failure).
                    # We just log it here so it bubbles up to trigger the circuit breaker.
                    logger.error("Queue item failed (handled by submit_to_hmrc)", queue_id=item["id"], error=str(e))
                finally:
                    # Do not blindly update to PENDING if it's already FAILED or SUBMITTED.
                    pass

            if pending_items:
                for item in pending_items:
                    logger.info("\033[94mPENDING -> PROCESSING\033[0m", queue_id=item["id"])
                tasks = [process_item(item) for item in pending_items]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for r in results:
                    if isinstance(r, CircuitBreakerOpenException):
                        await asyncio.sleep(hmrc_breaker.recovery_timeout)
                        break
            else:
                await asyncio.sleep(1)  # idle wait if queue is empty
        except Exception as e:
            logger.critical("Worker critical error", error=str(e), retry_in="5s")
            await asyncio.sleep(5)


async def process_ttl_sweeper():
    while True:
        try:
            from db import get_expiring_staged_sessions
            expiring = await get_expiring_staged_sessions()
            if expiring:
                async with get_connection() as conn:
                    for item in expiring:
                        logger.warning(
                            "ALERT: Chat Session ID has expired! Purging PII to satisfy GDPR data minimisation.",
                            chat_id=item["id"],
                        )
                        await conn.execute(
                            "DELETE FROM chat_sessions WHERE id = $1 AND NOT EXISTS (SELECT 1 FROM hmrc_ledger WHERE chat_id = $1)",
                            item["id"]
                        )

            await asyncio.sleep(5)
        except Exception as e:
            logger.error("Sweeper error", error=str(e), retry_in="5s")
            await asyncio.sleep(5)


async def start_workers():
    logger.info("Starting background async workers...")
    semaphore = asyncio.Semaphore(5)
    await asyncio.gather(process_hmrc_queue(semaphore), process_ttl_sweeper())


if __name__ == "__main__":
    asyncio.run(start_workers())
