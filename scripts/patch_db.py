import json

def append_to_file():
    with open('db.py', 'a', encoding='utf-8') as f:
        f.write('''

async def push_intake_queue(sender_id: str, message: str, media_urls: list, turn_count: int):
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        await conn.execute(
            """
            INSERT INTO intake_queue (timestamp, sender_id, message, media_urls, turn_count, status)
            VALUES ($1, $2, $3, $4, $5, 'PENDING')
            """,
            timestamp, sender_id, message, json.dumps(media_urls), turn_count
        )

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
        return dict(row) if row else None

async def mark_intake_done(item_id: int):
    async with get_connection() as conn:
        await conn.execute("UPDATE intake_queue SET status = 'DONE' WHERE id = $1", item_id)
''')

if __name__ == "__main__":
    append_to_file()
