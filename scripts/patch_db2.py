import re

def patch():
    with open('db.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Connection pool locking & size
    content = content.replace(
"""db_pool = None

async def init_pool():
    global db_pool
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)

async def close_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None""",
"""import asyncio
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
            db_pool = None"""
    )

    # 2. Schema changes in init_db
    content = content.replace(
        "whatsapp_id TEXT,\n                created_at TEXT",
        "whatsapp_id TEXT,\n                nonce_hash TEXT,\n                created_at TEXT"
    )
    
    intake_queue_schema = """
        await conn.execute(\"\"\"
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
        \"\"\")
"""
    content = content.replace(
        '            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_sender_id ON chat_sessions(sender_id)"',
        intake_queue_schema + '\n        await conn.execute(\n            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_sender_id ON chat_sessions(sender_id)"'
    )

    # 3. SELECT FOR UPDATE SKIP LOCKED
    old_get_pending = """async def get_pending_hmrc_queue():
    async with get_connection() as conn:
        rows = await conn.fetch(
            '''SELECT h.*, c.sender_id 
               FROM hmrc_ledger h 
               JOIN chat_sessions c ON h.chat_id = c.id 
               WHERE h.status = 'PENDING' 
               ORDER BY h.timestamp ASC LIMIT 100'''
        )
        return [dict(row) for row in rows]"""

    new_get_pending = """async def get_pending_hmrc_queue():
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
            
        return result_items"""
    content = content.replace(old_get_pending, new_get_pending)

    # 4. Append new DB functions
    new_funcs = """

async def push_intake_queue(chat_id: int, sender_id: str, message: str, media_urls: list, turn_count: int):
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        await conn.execute(
            \"\"\"
            INSERT INTO intake_queue (chat_id, timestamp, sender_id, message, media_urls, turn_count, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'PENDING')
            \"\"\",
            chat_id, timestamp, sender_id, message, json.dumps(media_urls), turn_count
        )

import json
async def pop_intake_queue():
    async with get_connection() as conn:
        row = await conn.fetchrow(
            \"\"\"
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
            \"\"\"
        )
        if row:
            d = dict(row)
            d["media_urls"] = json.loads(d["media_urls"]) if d.get("media_urls") else []
            return d
        return None

async def mark_intake_done(item_id: int):
    async with get_connection() as conn:
        await conn.execute("UPDATE intake_queue SET status = 'DONE' WHERE id = $1", item_id)
"""
    content += new_funcs

    with open('db.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("db.py patched successfully.")

if __name__ == "__main__":
    patch()
