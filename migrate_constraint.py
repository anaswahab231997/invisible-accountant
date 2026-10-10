import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute('ALTER TABLE accounting_connections ADD CONSTRAINT unique_workspace_provider UNIQUE (workspace_id, provider);')
        print("Constraint added.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
