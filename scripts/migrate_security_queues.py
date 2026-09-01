import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(DATABASE_URL)
    
    # Add nonce_hash to oauth_states
    await conn.execute("ALTER TABLE oauth_states ADD COLUMN IF NOT EXISTS nonce_hash TEXT;")
    
    # Create intake_queue table for persistent webhooks
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS intake_queue (
            id SERIAL PRIMARY KEY,
            timestamp TEXT,
            sender_id TEXT,
            message TEXT,
            media_urls TEXT,
            turn_count INTEGER,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    
    await conn.close()
    print("Migration successful.")

if __name__ == "__main__":
    asyncio.run(migrate())
