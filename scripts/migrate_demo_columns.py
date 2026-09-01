import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def migrate():
    DATABASE_URL = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(DATABASE_URL)
    
    await conn.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;")
    await conn.execute("ALTER TABLE hmrc_ledger ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;")
    
    # Retroactively mark existing demo data
    await conn.execute("UPDATE chat_sessions SET is_demo = TRUE WHERE sender_id LIKE 'demo_web_%';")
    
    # For hmrc_ledger, we can join chat_sessions to mark retroactive ones
    await conn.execute("""
        UPDATE hmrc_ledger hl
        SET is_demo = TRUE
        FROM chat_sessions cs
        WHERE hl.chat_id = cs.id AND cs.is_demo = TRUE;
    """)
    
    # Also, mark retroactive demo ledgers as 'DEMO' status so the worker doesn't pick them up
    await conn.execute("""
        UPDATE hmrc_ledger
        SET status = 'DEMO_SAVED'
        WHERE is_demo = TRUE AND status = 'PENDING';
    """)
    
    await conn.close()
    print("Migration successful.")

if __name__ == "__main__":
    asyncio.run(migrate())
