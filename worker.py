import asyncio
import time
import aiosqlite
from db import get_pending_hmrc_queue, mark_hmrc_submitted, get_expiring_ambiguous_intakes

async def process_hmrc_queue():
    while True:
        pending_items = await get_pending_hmrc_queue()
        
        for item in pending_items:
            print(f"[WORKER] Submitting Queue ID {item['id']} to HMRC API...")
            # Simulate HMRC network call
            await asyncio.sleep(0.1) 
            await mark_hmrc_submitted(item['id'])
            print(f"[WORKER] Queue ID {item['id']} successfully submitted.")
            
            # Strict Rate Limiting: 2.5 requests per second => 0.4 seconds between requests
            await asyncio.sleep(0.4) 
            
        await asyncio.sleep(1) # idle wait if queue is empty

async def process_ttl_sweeper():
    while True:
        expiring = await get_expiring_ambiguous_intakes()
        for item in expiring:
            print(f"[SWEEPER] ALERT: Intake ID {item['id']} is nearing the 24h WhatsApp policy limit!")
            print(f"[SWEEPER] Triggering batch template message to sender {item['sender_id']} for missing data.")
            # We would normally trigger a WhatsApp template message here, then maybe delete or mark the row.
            # To avoid infinite loop printing in prototype, we just update the TTL to far future or mark it.
            conn = await aiosqlite.connect("prototype_db.sqlite")
            await conn.execute("UPDATE intake_logs SET ttl_timestamp = '9999-12-31' WHERE id = ?", (item['id'],))
            await conn.commit()
            await conn.close()
            
        await asyncio.sleep(5)

async def start_workers():
    print("Starting background async workers...")
    await asyncio.gather(
        process_hmrc_queue(),
        process_ttl_sweeper()
    )

if __name__ == "__main__":
    asyncio.run(start_workers())
