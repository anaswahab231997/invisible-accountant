import aiosqlite
import json
from datetime import datetime, timedelta

DB_FILE = "prototype_db.sqlite"

async def get_connection():
    conn = await aiosqlite.connect(DB_FILE)
    await conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = aiosqlite.Row
    return conn

async def init_db():
    conn = await get_connection()
    
    # Table for raw ingested messages
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS intake_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            sender_id TEXT,
            raw_message TEXT,
            media_urls TEXT,
            turn_count INTEGER DEFAULT 1,
            ttl_timestamp TEXT
        )
    ''')
    
    # Table for categorized expenses ready for HMRC queue
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS hmrc_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intake_id INTEGER,
            timestamp TEXT,
            vendor TEXT,
            amount REAL,
            category TEXT,
            is_ambiguous BOOLEAN,
            status TEXT,
            auditor_question TEXT,
            FOREIGN KEY(intake_id) REFERENCES intake_logs(id)
        )
    ''')
    
    await conn.commit()
    await conn.close()

async def log_intake(sender_id, raw_message, media_urls=None, turn_count=1):
    conn = await get_connection()
    
    timestamp = datetime.now().isoformat()
    # For prototype testing, TTL is set to 20 seconds from now (instead of 24h)
    ttl_timestamp = (datetime.now() + timedelta(seconds=20)).isoformat()
    media_urls_str = json.dumps(media_urls) if media_urls else "[]"
    
    cursor = await conn.execute('''
        INSERT INTO intake_logs (timestamp, sender_id, raw_message, media_urls, turn_count, ttl_timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (timestamp, sender_id, raw_message, media_urls_str, turn_count, ttl_timestamp))
    
    intake_id = cursor.lastrowid
    await conn.commit()
    await conn.close()
    
    return intake_id

async def queue_expense(intake_id, vendor, amount, category, is_ambiguous, auditor_question=""):
    conn = await get_connection()
    
    timestamp = datetime.now().isoformat()
    status = "DISAMBIGUATING" if is_ambiguous else "PENDING"
    
    cursor = await conn.execute('''
        INSERT INTO hmrc_queue (intake_id, timestamp, vendor, amount, category, is_ambiguous, status, auditor_question)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (intake_id, timestamp, vendor, amount, category, is_ambiguous, status, auditor_question))
    
    queue_id = cursor.lastrowid
    await conn.commit()
    await conn.close()
    
    return queue_id

async def get_pending_hmrc_queue():
    conn = await get_connection()
    cursor = await conn.execute('SELECT * FROM hmrc_queue WHERE status = "PENDING" ORDER BY timestamp ASC')
    rows = await cursor.fetchall()
    await conn.close()
    return [dict(row) for row in rows]

async def mark_hmrc_submitted(queue_id):
    conn = await get_connection()
    await conn.execute('UPDATE hmrc_queue SET status = "SUBMITTED" WHERE id = ?', (queue_id,))
    await conn.commit()
    await conn.close()

async def get_all_hmrc_queue():
    conn = await get_connection()
    cursor = await conn.execute('SELECT * FROM hmrc_queue ORDER BY timestamp ASC')
    rows = await cursor.fetchall()
    await conn.close()
    return [dict(row) for row in rows]

async def get_expiring_ambiguous_intakes():
    conn = await get_connection()
    
    now = datetime.now().isoformat()
    # Get ambiguous items where TTL has expired (or is close)
    cursor = await conn.execute('''
        SELECT i.*, h.category FROM intake_logs i 
        JOIN hmrc_queue h ON i.id = h.intake_id 
        WHERE h.status = "DISAMBIGUATING" AND i.ttl_timestamp <= ?
    ''', (now,))
    
    rows = await cursor.fetchall()
    await conn.close()
    return [dict(row) for row in rows]
