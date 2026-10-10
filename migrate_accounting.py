import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL not set.")
        return
        
    print(f"Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        print("Creating accounting_connections table...")
        await conn.execute('''
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            
            CREATE TABLE IF NOT EXISTS accounting_connections (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                workspace_id TEXT,
                provider VARCHAR(50) NOT NULL,
                provider_tenant_id VARCHAR(255) NOT NULL,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_accounting_provider ON accounting_connections(provider);
            CREATE INDEX IF NOT EXISTS idx_accounting_workspace ON accounting_connections(workspace_id);
        ''')
        print("Migration successful.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
