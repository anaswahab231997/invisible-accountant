import asyncio
import time
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from db import (
    get_connection,
    
    get_pending_hmrc_queue,
    mark_hmrc_submitted,
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

class OAuthManager:
    def __init__(self):
        self.client_id = os.getenv("XERO_CLIENT_ID")
        self.client_secret = os.getenv("XERO_CLIENT_SECRET")
        self.base_url = os.getenv("XERO_BASE_URL", "https://identity.xero.com")

    async def get_user_identity(self, whatsapp_id: str):
        encrypted_blob = await get_identity_from_vault(whatsapp_id)
        if not encrypted_blob:
            raise Exception("No identity found in secure vault for this user.")
            
        encrypted_payload = json.loads(encrypted_blob.decode("utf-8"))
        decrypted_json = token_engine.decrypt_tokens(
            encrypted_payload, 
            associated_data=f"hmrc_identity_{whatsapp_id}"
        )
        identity = json.loads(decrypted_json)
        
        # Check expiry with a 60-second buffer for network latency
        if time.time() + 60 > identity.get("expires_at", 0):
            logger.info("Access token expired. Refreshing token via Xero...", whatsapp_id=whatsapp_id)
            identity = await self.refresh_user_token(whatsapp_id, identity)
            
        return identity

    async def refresh_user_token(self, whatsapp_id: str, identity: dict):
        from security import generate_hmrc_fraud_headers
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/connect/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": identity.get("refresh_token")
                },
                headers=generate_hmrc_fraud_headers()
            )
            
            if resp.status_code != 200:
                logger.error("Token refresh failed. User must re-authenticate via Gov Gateway.", status=resp.status_code)
                raise Exception("OAuth 18-month grant expired or refresh token invalid.")
                
            token_data = resp.json()
            identity["access_token"] = token_data["access_token"]
            identity["refresh_token"] = token_data.get("refresh_token", identity["refresh_token"])
            identity["expires_at"] = time.time() + token_data.get("expires_in", 14400)
            
            # Re-encrypt and store
            encrypted_blob = token_engine.encrypt_tokens(
                plaintext=json.dumps(identity),
                associated_data=f"hmrc_identity_{whatsapp_id}"
            )
            await store_identity_in_vault(whatsapp_id, encrypted_blob)
            
            return identity

hmrc_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15)
oauth_manager = OAuthManager()


from adapters.universal_adapter import UniversalAdapter
from models.unified_record import UnifiedFinancialRecord, TargetSystem

universal_adapter = UniversalAdapter()

async def submit_to_hmrc(item):
    try:
        identity = await oauth_manager.get_user_identity(item["sender_id"])
    except Exception as e:
        logger.error("Auth expired or failed", error=str(e), queue_id=item["id"])
        from db import get_connection
        async with get_connection() as conn:
            await conn.execute("UPDATE hmrc_ledger SET status = 'AUTH_EXPIRED' WHERE id = $1", item["id"])
        return
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
    if not accountant_approved and ((amount > 500.0 and fin_data.get("transaction_type", "EXPENSE") != "INCOME") or fin_data.get("needs_accountant_review")):
        from db import get_connection
        async with get_connection() as conn:
            await conn.execute("UPDATE hmrc_ledger SET status = 'CAPITAL_ALLOWANCE' WHERE id = $1", item["id"])
        return

    record = UnifiedFinancialRecord(
        amount=amount,
        category=item.get("category", "Other business expenses"),
        timestamp=item["timestamp"],
        target_system=TargetSystem.XERO,
        sender_id=item.get("sender_id", "unknown_whatsapp_user"),
        extra_data={"id": item["id"], "media_urls": item.get("media_urls"), **fin_data}
    )
    
    if DRY_RUN:
        logger.info("\033[93mDRY RUN ACTIVE: Dumping payload instead of submitting\033[0m")
        with open("dry_run_payloads.json", "a") as f:
            f.write(record.json() + "\n")
        await mark_hmrc_submitted(item["id"])
        logger.info("\033[92mPROCESSING -> SUBMITTED (DRY RUN)\033[0m", queue_id=item["id"])
        return
    
    try:
        from accounting_client import AccountingClient
        client = AccountingClient(workspace_id=item.get("sender_id", ""), provider="XERO")
        
        # Enforce math verification as per plan (Trust but Verify)
        net = fin_data.get("net_amount", amount)
        tax = fin_data.get("vat_amount", 0.0)
        gross = fin_data.get("gross_amount", amount)
        
        if abs((net + tax) - gross) > 0.01:
            raise Exception("Math Validation Failed: Net + Tax != Gross")

        bill_payload = {
            "Type": "ACCPAY",
            "Status": "DRAFT",
            "Contact": {"Name": fin_data.get("vendor", "Unknown Supplier")},
            "LineItems": [{
                "Description": item.get("category", "General Expense"),
                "Quantity": 1,
                "UnitAmount": net,
                "TaxAmount": tax
            }]
        }
        resp = await client.create_draft_bill(bill_payload)
        invoice_id = resp.get("Invoices", [{}])[0].get("InvoiceID")
        
        # If there are receipt attachments, upload them
        media_urls = item.get("media_urls") or []
        if invoice_id and media_urls:
            import httpx
            async with httpx.AsyncClient() as dl_client:
                for idx, m_url in enumerate(media_urls):
                    try:
                        img_resp = await dl_client.get(m_url)
                        if img_resp.status_code == 200:
                            await client.upload_attachment(invoice_id, f"receipt_{idx}.jpg", img_resp.content, "image/jpeg")
                    except Exception as upload_err:
                        logger.error("Failed to upload attachment to Xero", error=str(upload_err))

        await mark_hmrc_submitted(item["id"])
        logger.info("[92mPROCESSING -> SUBMITTED[0m", queue_id=item["id"])
    except Exception as e:
        # Sanitize PII from the payload before logging
        def sanitize_pii(data):
            if isinstance(data, dict):
                return {k: sanitize_pii(v) for k, v in data.items() if k.lower() not in ['nino', 'utr', 'password', 'name', 'address', 'vrn']}
            elif isinstance(data, list):
                return [sanitize_pii(v) for v in data]
            return data
            
        safe_payload = sanitize_pii(e.payload)
        logger.error("HMRC API Error", queue_id=item["id"], status=e.status_code, payload=safe_payload)
        
        if e.status_code in (401, 429, 500, 502, 503, 504):
            logger.info("Transient/Auth error, applying exponential backoff", queue_id=item["id"])
            from db import get_connection
            async with get_connection() as conn:
                if e.status_code == 401:
                    logger.warning("401 Unauthorized - wiping token for re-auth", whatsapp_id=item["sender_id"])
                    await conn.execute("DELETE FROM hmrc_identity_vault WHERE whatsapp_id = $1", item["sender_id"])
                    await conn.execute("UPDATE hmrc_ledger SET status = 'AUTH_EXPIRED' WHERE id = $1", item["id"])
                    logger.info("\033[91mPROCESSING -> AUTH_EXPIRED\033[0m", queue_id=item["id"])
                    await send_failure_sms(item["sender_id"])
                    return  # Do not raise to prevent tripping circuit breaker
                else:
                    row = await conn.fetchrow("""
                        UPDATE hmrc_ledger 
                        SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                            retry_count = retry_count + 1,
                            next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                        WHERE id = $1
                        RETURNING status
                    """, item["id"])
                    if row:
                        logger.info(f"\033[93mPROCESSING -> {row['status']}\033[0m", queue_id=item["id"])
                        if row["status"] == 'FAILED': await send_failure_sms(item.get("sender_id"))
                    raise e
        else:
            from db import mark_hmrc_failed
            await mark_hmrc_failed(item["id"])
            logger.info("\033[91mPROCESSING -> FAILED\033[0m", queue_id=item["id"])
            await send_failure_sms(item.get("sender_id"))
            raise e
    except Exception as e:
        logger.error("Unexpected error in worker", queue_id=item["id"], error=str(e))
        from db import get_connection
        async with get_connection() as conn:
            row = await conn.fetchrow("""
                UPDATE hmrc_ledger 
                SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                    retry_count = retry_count + 1,
                    next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                WHERE id = $1
                RETURNING status
            """, item["id"])
            if row:
                logger.info(f"\033[91mPROCESSING -> {row['status']}\033[0m", queue_id=item["id"])
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
