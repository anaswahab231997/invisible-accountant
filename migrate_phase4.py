import asyncio
from db import get_connection

async def migrate():
    async with get_connection() as conn:
        print("Applying Phase 4 schema updates to hmrc_ledger...")
        await conn.execute("""
            ALTER TABLE hmrc_ledger 
            ADD COLUMN IF NOT EXISTS attachment_sha256 VARCHAR(64),
            ADD COLUMN IF NOT EXISTS attachment_status VARCHAR(30) DEFAULT 'NONE',
            ADD COLUMN IF NOT EXISTS attachment_error TEXT,
            ADD COLUMN IF NOT EXISTS xero_attachment_id VARCHAR(100);
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hmrc_ledger_attachment_status 
            ON hmrc_ledger(attachment_status);
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_hmrc_ledger_attachment_sha256 
            ON hmrc_ledger(attachment_sha256);
        """)
        cols = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'hmrc_ledger' 
              AND column_name IN ('attachment_sha256', 'attachment_status', 'attachment_error', 'xero_attachment_id')
            ORDER BY column_name;
        """)
        for c in cols:
            print(f"Verified Column: {c['column_name']} ({c['data_type']})")
        print("Phase 4 schema updates successfully applied.")

if __name__ == "__main__":
    asyncio.run(migrate())
