import asyncio
import json
import os
from datetime import datetime, timedelta
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from security import mask_pii, compute_receipt_fingerprint
from aes_gcm_security import TokenEncryptionEngine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

import asyncio
db_pool = None
_pool_lock = None

async def init_pool():
    global db_pool, _pool_lock
    if _pool_lock is None:
        _pool_lock = asyncio.Lock()
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    async with _pool_lock:
        if db_pool is None:
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=8)

async def close_pool():
    global db_pool, _pool_lock
    if _pool_lock is None:
        return
    async with _pool_lock:
        if db_pool:
            await db_pool.close()
            db_pool = None

@asynccontextmanager
async def get_connection():
    if db_pool is None:
        await init_pool()
    async with db_pool.acquire() as conn:
        yield conn

async def init_db():
    # Database schema is now managed by Alembic migrations.
    pass

async def create_chat_session(sender_id: str, message: str, media_urls: list[str], turn_count: int) -> int:
    timestamp = datetime.now().isoformat()
    ttl = (datetime.now() + timedelta(hours=24)).isoformat()
    is_demo = sender_id.startswith("demo_web_")
    
    safe_message = mask_pii(message)
    
    async with get_connection() as conn:
        practice_id = await conn.fetchval(
            "SELECT practice_id FROM practice_clients WHERE client_sender_id = $1 LIMIT 1",
            sender_id
        )
        chat_id = await conn.fetchval('''
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, turn_count, ttl_timestamp, is_demo, practice_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        ''', timestamp, sender_id, safe_message, json.dumps(media_urls), turn_count, ttl, is_demo, practice_id)
        return chat_id

async def get_recent_intakes_by_sender(sender_id: str, limit: int = 5):
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT raw_message FROM chat_sessions WHERE sender_id = $1 ORDER BY timestamp DESC LIMIT $2",
            sender_id, limit
        )
        return [row["raw_message"] for row in reversed(rows)]

async def stage_expense(chat_id: int, payload: dict):
    payload_str = json.dumps(payload)
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE chat_sessions SET staging_payload = $1 WHERE id = $2",
            payload_str, chat_id
        )

async def get_unconfirmed_session(sender_id: str):
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT c.* FROM chat_sessions c
            LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
            WHERE c.sender_id = $1 AND c.staging_payload IS NOT NULL AND h.id IS NULL
            ORDER BY c.timestamp DESC LIMIT 1
            """,
            sender_id
        )
        return dict(row) if row else None

def safe_float(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    import re
    cleaned = re.sub(r'[^\d\.-]', '', str(val))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

async def check_active_duplicate_expense(fingerprint: str, days: int = 90) -> dict | None:
    if not fingerprint:
        return None
    async with get_connection() as conn:
        time_limit = (datetime.now() - timedelta(days=days)).isoformat()
        row = await conn.fetchrow(
            """
            SELECT * FROM hmrc_ledger
            WHERE receipt_fingerprint = $1
              AND timestamp >= $2
              AND status IN ('PENDING', 'PROCESSING', 'SUBMITTED', 'CAPITAL_ALLOWANCE', 'APPROVED')
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            fingerprint, time_limit
        )
        return dict(row) if row else None

async def confirm_and_queue_to_ledger(chat_id: int, allow_duplicate: bool = False):
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT staging_payload, is_demo, sender_id, practice_id FROM chat_sessions WHERE id = $1", chat_id)
        if not row or not row["staging_payload"]:
            raise ValueError("No staged payload to confirm.")
            
        payload = json.loads(row["staging_payload"])
        is_demo = row["is_demo"]
        sender_id = row.get("sender_id") or ""
        practice_id = row.get("practice_id")
        if not practice_id and sender_id:
            practice_id = await conn.fetchval(
                "SELECT practice_id FROM practice_clients WHERE client_sender_id = $1 LIMIT 1",
                sender_id
            )
        
        status = await conn.execute(
            "UPDATE chat_sessions SET staging_payload = NULL WHERE id = $1 AND staging_payload IS NOT NULL",
            chat_id
        )
        if status == "UPDATE 0":
            raise ValueError("Already confirmed by another request.")
        
        queue_status = "DEMO_SAVED" if is_demo else "PENDING"
        
        gross = safe_float(payload.get("gross_amount") or payload.get("amount", 0.0))
        vat = safe_float(payload.get("vat_amount", 0.0))
        net = safe_float(payload.get("net_amount") or (gross - vat if gross else 0.0))
        vendor = payload.get("vendor", "")
        tx_date = payload.get("transaction_date") or payload.get("date") or payload.get("receipt_date")

        # Deterministic Receipt Fingerprint
        receipt_fingerprint = compute_receipt_fingerprint(sender_id, vendor, gross, tx_date)

        # 90-day Duplicate Detection Gate
        if not is_demo and not allow_duplicate:
            time_limit_90d = (datetime.now() - timedelta(days=90)).isoformat()
            dup = await conn.fetchrow(
                """
                SELECT id FROM hmrc_ledger
                WHERE receipt_fingerprint = $1
                  AND timestamp >= $2
                  AND status IN ('PENDING', 'PROCESSING', 'SUBMITTED', 'CAPITAL_ALLOWANCE', 'APPROVED')
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                receipt_fingerprint, time_limit_90d
            )
            if dup:
                queue_status = "DUPLICATE_SUSPECTED"

        financial_data = {
            "vendor": vendor,
            "net_amount": net,
            "vat_amount": vat,
            "gross_amount": gross,
            "currency": payload.get("currency", "GBP"),
            "account_code": payload.get("account_code"),
            "tax_code": payload.get("tax_code") or payload.get("tax_type"),
            "tax_type": payload.get("tax_type") or payload.get("tax_code"),
            "description": payload.get("description") or payload.get("memo"),
            "category": payload.get("category"),
            "document_type": payload.get("document_type"),
            "vat_registration_number": payload.get("vat_registration_number"),
            "cis_deduction": payload.get("cis_deduction"),
            "line_items": payload.get("line_items", []),
            "transaction_type": payload.get("transaction_type"),
            "needs_accountant_review": payload.get("needs_accountant_review", False),
            "transaction_date": payload.get("transaction_date") or tx_date,
            "reference": payload.get("reference"),
            "invoice_number": payload.get("invoice_number")
        }
        
        master_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
        if master_key:
            engine = TokenEncryptionEngine(master_key)
            enc_dict = engine.encrypt_tokens(json.dumps(financial_data), associated_data=str(chat_id))
            encrypted_financial_data = json.dumps(enc_dict)
            plain_vendor = "ENCRYPTED"
            plain_amount = 0.0
        else:
            encrypted_financial_data = None
            plain_vendor = vendor
            plain_amount = gross
            
        real_amount = gross
        if not is_demo and queue_status != "DUPLICATE_SUSPECTED":
            if (payload.get("transaction_type", "EXPENSE") != "INCOME" and real_amount > 500.0) or payload.get("needs_accountant_review", False):
                if not payload.get("accountant_approved", False):
                    queue_status = "CAPITAL_ALLOWANCE"
        
        queue_id = await conn.fetchval(
            """
            INSERT INTO hmrc_ledger (chat_id, timestamp, vendor, amount, category, status, encrypted_financial_data, is_demo, receipt_fingerprint, external_bill_id, practice_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """,
            chat_id,
            timestamp,
            plain_vendor,
            plain_amount,
            payload.get("category"),
            queue_status,
            encrypted_financial_data,
            is_demo,
            receipt_fingerprint,
            None,
            practice_id
        )

        if practice_id and sender_id and not is_demo:
            await conn.execute(
                """
                UPDATE practice_clients
                SET total_receipts_count = total_receipts_count + 1,
                    last_receipt_at = NOW()
                WHERE practice_id = $1 AND client_sender_id = $2
                """,
                practice_id, sender_id
            )

        return queue_id

async def sweep_orphaned_processing():
    async with get_connection() as conn:
        time_limit = (datetime.now() - timedelta(minutes=10)).isoformat()
        await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE status = 'PROCESSING' AND updated_at < $1", time_limit)
        await conn.execute("UPDATE intake_queue SET status = 'PENDING' WHERE status = 'PROCESSING' AND updated_at < $1", time_limit)

async def get_pending_hmrc_queue(limit: int = 100):
    async with get_connection() as conn:
        rows = await conn.fetch(
            '''
            UPDATE hmrc_ledger 
            SET status = 'PROCESSING', updated_at = $2
            WHERE id IN (
                SELECT id 
                FROM hmrc_ledger 
                WHERE status = 'PENDING' 
                  AND (next_retry_at IS NULL OR next_retry_at <= NOW())
                ORDER BY timestamp ASC 
                LIMIT $1 
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
            ''',
            limit, datetime.now().isoformat()
        )
        if not rows:
            return []
            
        result_items = []
        for r in rows:
            chat_row = await conn.fetchrow(
                "SELECT sender_id, media_urls FROM chat_sessions WHERE id = $1", r["chat_id"]
            )
            item_dict = dict(r)
            item_dict["sender_id"] = chat_row["sender_id"] if chat_row else "unknown"
            raw_media = chat_row["media_urls"] if chat_row else None
            if raw_media and isinstance(raw_media, str):
                try:
                    import json
                    item_dict["media_urls"] = json.loads(raw_media)
                except Exception:
                    item_dict["media_urls"] = [raw_media]
            else:
                item_dict["media_urls"] = raw_media or []
            result_items.append(item_dict)
            
        return result_items

async def update_ledger_external_bill_id(queue_id: int, external_bill_id: str):
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE hmrc_ledger SET external_bill_id = $1, updated_at = $2 WHERE id = $3",
            external_bill_id, datetime.now().isoformat(), queue_id
        )

async def update_ledger_attachment_status(
    queue_id: int, 
    status: str, 
    sha256: str | None = None, 
    xero_attachment_id: str | None = None, 
    error: str | None = None
):
    async with get_connection() as conn:
        now_ts = datetime.now().isoformat()
        await conn.execute(
            """
            UPDATE hmrc_ledger 
            SET attachment_status = $1,
                attachment_sha256 = COALESCE($2, attachment_sha256),
                xero_attachment_id = COALESCE($3, xero_attachment_id),
                attachment_error = $4,
                updated_at = $5
            WHERE id = $6
            """,
            status, sha256, xero_attachment_id, error, now_ts, queue_id
        )

async def mark_hmrc_submitted(
    queue_id: int, 
    external_bill_id: str | None = None,
    attachment_status: str | None = None,
    attachment_sha256: str | None = None,
    xero_attachment_id: str | None = None
):
    async with get_connection() as conn:
        now_ts = datetime.now().isoformat()
        await conn.execute(
            """
            UPDATE hmrc_ledger 
            SET status = 'SUBMITTED', 
                external_bill_id = COALESCE(external_bill_id, $2),
                attachment_status = COALESCE($3, attachment_status),
                attachment_sha256 = COALESCE($4, attachment_sha256),
                xero_attachment_id = COALESCE($5, xero_attachment_id),
                updated_at = $6 
            WHERE id = $1
            """,
            queue_id, external_bill_id, attachment_status, attachment_sha256, xero_attachment_id, now_ts
        )

async def mark_hmrc_failed(queue_id):
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE hmrc_ledger SET status = 'FAILED' WHERE id = $1", queue_id
        )

async def get_hmrc_ledger_by_chat(chat_id: int):
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM hmrc_ledger WHERE chat_id = $1", chat_id
        )
        return dict(row) if row else None

async def get_expiring_staged_sessions():
    now = datetime.now().isoformat()
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT c.* FROM chat_sessions c
            LEFT JOIN hmrc_ledger h ON c.id = h.chat_id
            WHERE c.staging_payload IS NOT NULL AND h.id IS NULL AND c.ttl_timestamp <= $1
            """,
            now
        )
        return [dict(row) for row in rows]

async def store_identity_in_vault(whatsapp_id: str, encrypted_blob: bytes):
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO hmrc_identity_vault (whatsapp_id, encrypted_blob, updated_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (whatsapp_id) DO UPDATE SET 
                encrypted_blob = EXCLUDED.encrypted_blob,
                updated_at = EXCLUDED.updated_at
            """,
            whatsapp_id, encrypted_blob, timestamp
        )

async def get_identity_from_vault(whatsapp_id: str) -> bytes:
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT encrypted_blob FROM hmrc_identity_vault WHERE whatsapp_id = $1",
            whatsapp_id
        )
        return row["encrypted_blob"] if row else None

async def create_oauth_state(whatsapp_id: str, nonce_hash: str = None) -> str:
    import uuid
    state_uuid = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        await conn.execute(
            "INSERT INTO oauth_states (state_uuid, whatsapp_id, nonce_hash, created_at) VALUES ($1, $2, $3, $4)",
            state_uuid, whatsapp_id, nonce_hash, timestamp
        )
    return state_uuid

async def consume_oauth_state(state_uuid: str) -> dict:
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT whatsapp_id, nonce_hash FROM oauth_states WHERE state_uuid = $1",
            state_uuid
        )
        if row:
            await conn.execute("DELETE FROM oauth_states WHERE state_uuid = $1", state_uuid)
            return dict(row)
        return None


async def push_intake_queue(chat_id: int, sender_id: str, message: str, media_urls: list, turn_count: int):
    timestamp = datetime.now().isoformat()
    safe_message = mask_pii(message)
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO intake_queue (chat_id, timestamp, sender_id, message, media_urls, turn_count, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'PENDING')
            """,
            chat_id, timestamp, sender_id, safe_message, json.dumps(media_urls), turn_count
        )

import json
async def pop_intake_queue():
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE intake_queue 
            SET status = 'PROCESSING', updated_at = $1 
            WHERE id = (
                SELECT id 
                FROM intake_queue 
                WHERE status = 'PENDING' 
                ORDER BY timestamp ASC 
                LIMIT 1 
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
            """, datetime.now().isoformat()
        )
        if row:
            d = dict(row)
            d["media_urls"] = json.loads(d["media_urls"]) if d.get("media_urls") else []
            return d
        return None

async def mark_intake_done(item_id: int):
    async with get_connection() as conn:
        await conn.execute("UPDATE intake_queue SET status = 'DONE' WHERE id = $1", item_id)
async def get_all_hmrc_queue(limit: int = 100, offset: int = 0):
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM hmrc_ledger ORDER BY timestamp DESC LIMIT $1 OFFSET $2",
            limit, offset
        )
        return [dict(row) for row in rows]

async def store_accounting_connection(workspace_id: str, provider: str, provider_tenant_id: str, access_token: str, refresh_token: str, expires_in_seconds: int):
    from datetime import datetime, timedelta, timezone
    
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO accounting_connections (workspace_id, provider, provider_tenant_id, access_token, refresh_token, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (workspace_id, provider) DO UPDATE SET 
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                updated_at = NOW()
            """,
            workspace_id, provider, provider_tenant_id, access_token, refresh_token, expires_at
        )


# --- Practice & Multi-Tenancy Management ---

async def create_practice(
    name: str,
    slug: str,
    firm_code: str,
    contact_name: str,
    contact_email: str,
    contact_phone: str = "",
    company_number: str = "",
    regulatory_body: str = "ICAEW",
    regulatory_number: str = "",
    password_hash: str = "",
    primary_accounting_platform: str = "XERO"
) -> int:
    async with get_connection() as conn:
        practice_id = await conn.fetchval(
            """
            INSERT INTO practices (
                name, slug, firm_code, contact_name, contact_email, contact_phone,
                company_number, regulatory_body, regulatory_number, password_hash,
                primary_accounting_platform, commission_rate_gbp, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 3.00, 'ACTIVE')
            RETURNING id
            """,
            name, slug, firm_code, contact_name, contact_email, contact_phone,
            company_number, regulatory_body, regulatory_number, password_hash,
            primary_accounting_platform
        )
        return practice_id

async def get_practice_by_id(practice_id: int):
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM practices WHERE id = $1", practice_id)
        return dict(row) if row else None

async def get_practice_by_slug(slug: str):
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM practices WHERE slug = $1", slug)
        return dict(row) if row else None

async def get_practice_by_code(firm_code: str):
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM practices WHERE firm_code = $1", firm_code)
        return dict(row) if row else None

async def get_practice_by_email(email: str):
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT * FROM practices WHERE contact_email = $1", email)
        return dict(row) if row else None

async def link_client_to_practice(practice_id: int, client_sender_id: str, client_name: str = None, client_email: str = None):
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO practice_clients (practice_id, client_sender_id, client_name, client_email, status)
            VALUES ($1, $2, $3, $4, 'ACTIVE')
            ON CONFLICT (practice_id, client_sender_id) DO UPDATE SET
                client_name = COALESCE(EXCLUDED.client_name, practice_clients.client_name),
                client_email = COALESCE(EXCLUDED.client_email, practice_clients.client_email),
                status = 'ACTIVE'
            """,
            practice_id, client_sender_id, client_name, client_email
        )

async def get_practice_clients(practice_id: int):
    async with get_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM practice_clients
            WHERE practice_id = $1
            ORDER BY joined_at DESC
            """,
            practice_id
        )
        return [dict(row) for row in rows]

async def get_client_practice(client_sender_id: str):
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            SELECT p.* FROM practices p
            JOIN practice_clients pc ON p.id = pc.practice_id
            WHERE pc.client_sender_id = $1
            LIMIT 1
            """,
            client_sender_id
        )
        return dict(row) if row else None

async def increment_client_receipt_count(practice_id: int, client_sender_id: str):
    async with get_connection() as conn:
        await conn.execute(
            """
            UPDATE practice_clients
            SET total_receipts_count = total_receipts_count + 1,
                last_receipt_at = NOW()
            WHERE practice_id = $1 AND client_sender_id = $2
            """,
            practice_id, client_sender_id
        )

async def get_practice_stats(practice_id: int):
    async with get_connection() as conn:
        client_count = await conn.fetchval(
            "SELECT COUNT(*) FROM practice_clients WHERE practice_id = $1 AND status = 'ACTIVE'",
            practice_id
        ) or 0
        total_receipts = await conn.fetchval(
            "SELECT COALESCE(SUM(total_receipts_count), 0) FROM practice_clients WHERE practice_id = $1",
            practice_id
        ) or 0
        loi_count = await conn.fetchval(
            "SELECT COUNT(*) FROM practice_lois WHERE practice_id = $1",
            practice_id
        ) or 0
        
        commission_rate = 3.00
        accrued_commission = float(client_count) * commission_rate
        return {
            "active_clients": client_count,
            "total_receipts": total_receipts,
            "loi_signed": loi_count > 0,
            "commission_rate_gbp": commission_rate,
            "monthly_commission_accrued_gbp": accrued_commission,
            "annual_commission_projected_gbp": accrued_commission * 12
        }

async def record_practice_loi(
    practice_id: int,
    signatory_name: str,
    signatory_title: str,
    firm_legal_name: str,
    firm_crn: str,
    firm_address: str,
    pledged_client_seats: int,
    signature_data_url: str,
    signature_ip_address: str,
    document_sha256: str
) -> int:
    async with get_connection() as conn:
        loi_id = await conn.fetchval(
            """
            INSERT INTO practice_lois (
                practice_id, signatory_name, signatory_title, firm_legal_name,
                firm_crn, firm_address, pledged_client_seats, pilot_duration_days,
                signature_data_url, signature_ip_address, document_sha256, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, 90, $8, $9, $10, 'EXECUTED')
            RETURNING id
            """,
            practice_id, signatory_name, signatory_title, firm_legal_name,
            firm_crn, firm_address, pledged_client_seats, signature_data_url,
            signature_ip_address, document_sha256
        )
        return loi_id

async def get_practice_lois(practice_id: int):
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM practice_lois WHERE practice_id = $1 ORDER BY signed_at DESC",
            practice_id
        )
        return [dict(row) for row in rows]

