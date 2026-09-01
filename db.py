import asyncio
import json
import os
from datetime import datetime, timedelta
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

import asyncio
db_pool = None
_pool_lock = asyncio.Lock()

async def init_pool():
    global db_pool
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    async with _pool_lock:
        if db_pool is None:
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=25)

async def close_pool():
    global db_pool
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
    async with get_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                timestamp TEXT,
                sender_id TEXT,
                raw_message TEXT,
                media_urls TEXT,
                turn_count INTEGER DEFAULT 1,
                ttl_timestamp TEXT,
                staging_payload TEXT,
                is_demo BOOLEAN DEFAULT FALSE
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS hmrc_ledger (
                id SERIAL PRIMARY KEY,
                chat_id INTEGER,
                timestamp TEXT,
                vendor TEXT,
                amount FLOAT,
                category TEXT,
                status TEXT,
                is_demo BOOLEAN DEFAULT FALSE,
                FOREIGN KEY(chat_id) REFERENCES chat_sessions(id)
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS hmrc_identity_vault (
                whatsapp_id TEXT PRIMARY KEY,
                encrypted_blob BYTEA,
                updated_at TEXT
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS oauth_states (
                state_uuid TEXT PRIMARY KEY,
                whatsapp_id TEXT,
                nonce_hash TEXT,
                created_at TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS intake_queue (
                id SERIAL PRIMARY KEY,
                chat_id INTEGER,
                timestamp TEXT,
                sender_id TEXT,
                message TEXT,
                media_urls TEXT,
                turn_count INTEGER,
                status TEXT DEFAULT 'PENDING'
            )
        """)

        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_sender_id ON chat_sessions(sender_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_ttl ON chat_sessions(ttl_timestamp)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_hmrc_ledger_status ON hmrc_ledger(status)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_hmrc_identity_vault_updated ON hmrc_identity_vault(updated_at)"
        )

async def create_chat_session(sender_id: str, message: str, media_urls: list[str], turn_count: int) -> int:
    timestamp = datetime.now().isoformat()
    ttl = (datetime.now() + timedelta(hours=24)).isoformat()
    is_demo = sender_id.startswith("demo_web_")
    
    async with get_connection() as conn:
        chat_id = await conn.fetchval('''
            INSERT INTO chat_sessions (timestamp, sender_id, raw_message, media_urls, turn_count, ttl_timestamp, is_demo)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        ''', timestamp, sender_id, message, json.dumps(media_urls), turn_count, ttl, is_demo)
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
        
        queue_id = await conn.fetchval(
            """
            INSERT INTO hmrc_ledger (chat_id, timestamp, vendor, amount, category, status, is_demo)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            chat_id,
            timestamp,
            payload.get("vendor"),
            float(payload.get("amount")),
            payload.get("category"),
            queue_status,
            is_demo
        )
        return queue_id

async def get_pending_hmrc_queue():
    async with get_connection() as conn:
        rows = await conn.fetch(
            '''
            UPDATE hmrc_ledger 
            SET status = 'PROCESSING' 
            WHERE id IN (
                SELECT id 
                FROM hmrc_ledger 
                WHERE status = 'PENDING' 
                ORDER BY timestamp ASC 
                LIMIT 100 
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
            '''
        )
        if not rows:
            return []
            
        result_items = []
        for r in rows:
            sender_id = await conn.fetchval(
                "SELECT sender_id FROM chat_sessions WHERE id = $1", r["chat_id"]
            )
            item_dict = dict(r)
            item_dict["sender_id"] = sender_id
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

async def get_all_hmrc_queue(limit: int = 100, offset: int = 0):
    async with get_connection() as conn:
        rows = await conn.fetch(
            "SELECT * FROM hmrc_ledger ORDER BY timestamp ASC LIMIT $1 OFFSET $2",
            limit, offset
        )
        return [dict(row) for row in rows]

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
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO intake_queue (chat_id, timestamp, sender_id, message, media_urls, turn_count, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'PENDING')
            """,
            chat_id, timestamp, sender_id, message, json.dumps(media_urls), turn_count
        )

import json
async def pop_intake_queue():
    async with get_connection() as conn:
        row = await conn.fetchrow(
            """
            UPDATE intake_queue 
            SET status = 'PROCESSING' 
            WHERE id = (
                SELECT id 
                FROM intake_queue 
                WHERE status = 'PENDING' 
                ORDER BY timestamp ASC 
                LIMIT 1 
                FOR UPDATE SKIP LOCKED
            )
            RETURNING *
            """
        )
        if row:
            d = dict(row)
            d["media_urls"] = json.loads(d["media_urls"]) if d.get("media_urls") else []
            return d
        return None

async def mark_intake_done(item_id: int):
    async with get_connection() as conn:
        await conn.execute("UPDATE intake_queue SET status = 'DONE' WHERE id = $1", item_id)
