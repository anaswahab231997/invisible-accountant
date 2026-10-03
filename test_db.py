import asyncio, asyncpg, json
from db import get_connection

async def main():
    async with get_connection() as conn:
        rows = await conn.fetch("SELECT * FROM chat_sessions WHERE staging_payload IS NOT NULL")
        for row in rows:
            print("SENDER:", row['sender_id'])
            print("RAW MESSAGE:", row['raw_message'])
            print("PAYLOAD:", row['staging_payload'])
            print("---")

asyncio.run(main())
