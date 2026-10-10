import asyncio
import json
import os
from datetime import datetime, timedelta
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from security import mask_pii
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
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=25)

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
        chat_id = await conn.fetchval('''
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, turn_count, ttl_timestamp, is_demo)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        ''', timestamp, sender_id, safe_message, json.dumps(media_urls), turn_count, ttl, is_demo)
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

async def confirm_and_queue_to_ledger(chat_id: int):
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        row = await conn.fetchrow("SELECT staging_payload, is_demo FROM chat_sessions WHERE id = $1", chat_id)
        if not row or not row["staging_payload"]:
            raise ValueError("No staged payload to confirm.")
            
        payload = json.loads(row["staging_payload"])
        is_demo = row["is_demo"]
        
        status = await conn.execute(
            "UPDATE chat_sessions SET staging_payload = NULL WHERE id = $1 AND staging_payload IS NOT NULL",
            chat_id
        )
        if status == "UPDATE 0":
            raise ValueError("Already confirmed by another request.")
        
        queue_status = "DEMO_SAVED" if is_demo else "PENDING"
        
        financial_data = {
            "vendor": payload.get("vendor"),
            "net_amount": payload.get("net_amount"),
            "vat_amount": payload.get("vat_amount"),
            "gross_amount": payload.get("gross_amount"),
            "document_type": payload.get("document_type"),
            "vat_registration_number": payload.get("vat_registration_number"),
            "cis_deduction": payload.get("cis_deduction"),
            "line_items": payload.get("line_items", []),
            "transaction_type": payload.get("transaction_type"),
            "needs_accountant_review": payload.get("needs_accountant_review", False),
            "transaction_date": payload.get("transaction_date")
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
            plain_vendor = payload.get("vendor", "")
            plain_amount = safe_float(payload.get("gross_amount") or payload.get("amount", 0.0))
            
        real_amount = safe_float(payload.get("gross_amount") or payload.get("amount", 0.0))
        if not is_demo:
            if (payload.get("transaction_type", "EXPENSE") != "INCOME" and real_amount > 500.0) or payload.get("needs_accountant_review", False):
                if not payload.get("accountant_approved", False):
                    queue_status = "CAPITAL_ALLOWANCE"
        
        queue_id = await conn.fetchval(
            """
            INSERT INTO hmrc_ledger (chat_id, timestamp, vendor, amount, category, status, encrypted_financial_data, is_demo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """,
            chat_id,
            timestamp,
            plain_vendor,
            plain_amount,
            payload.get("category"),
            queue_status,
            encrypted_financial_data,
            is_demo
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
            item_dict["media_urls"] = chat_row["media_urls"] if chat_row else None
            result_items.append(item_dict)
            
        return result_items

async def mark_hmrc_submitted(queue_id):
    async with get_connection() as conn:
        await conn.execute(
            "UPDATE hmrc_ledger SET status = 'SUBMITTED' WHERE id = $1", queue_id
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
a s y n c   d e f   s t o r e _ a c c o u n t i n g _ c o n n e c t i o n ( w o r k s p a c e _ i d :   s t r ,   p r o v i d e r :   s t r ,   p r o v i d e r _ t e n a n t _ i d :   s t r ,   a c c e s s _ t o k e n :   s t r ,   r e f r e s h _ t o k e n :   s t r ,   e x p i r e s _ i n _ s e c o n d s :   i n t ) : 
 
         t i m e s t a m p   =   ( d a t e t i m e . n o w ( )   +   t i m e d e l t a ( s e c o n d s = e x p i r e s _ i n _ s e c o n d s ) ) . i s o f o r m a t ( ) 
 
         a s y n c   w i t h   g e t _ c o n n e c t i o n ( )   a s   c o n n : 
 
                 a w a i t   c o n n . e x e c u t e ( 
 
                         " 
 
                         I N S E R T   I N T O   a c c o u n t i n g _ c o n n e c t i o n s   ( w o r k s p a c e _ i d ,   p r o v i d e r ,   p r o v i d e r _ t e n a n t _ i d ,   a c c e s s _ t o k e n ,   r e f r e s h _ t o k e n ,   e x p i r e s _ a t ) 
 
                         V A L U E S   ( $ 1 ,   $ 2 ,   $ 3 ,   $ 4 ,   $ 5 ,   $ 6 ) 
 
                         O N   C O N F L I C T   ( i d )   D O   U P D A T E   S E T   
 
                                 a c c e s s _ t o k e n   =   E X C L U D E D . a c c e s s _ t o k e n , 
 
                                 r e f r e s h _ t o k e n   =   E X C L U D E D . r e f r e s h _ t o k e n , 
 
                                 e x p i r e s _ a t   =   E X C L U D E D . e x p i r e s _ a t , 
 
                                 u p d a t e d _ a t   =   N O W ( ) 
 
                         " , 
 
                         w o r k s p a c e _ i d ,   p r o v i d e r ,   p r o v i d e r _ t e n a n t _ i d ,   a c c e s s _ t o k e n ,   r e f r e s h _ t o k e n ,   t i m e s t a m p 
 
                 ) 
 
 
