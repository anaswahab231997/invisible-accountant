import asyncio
import time
from db import init_db, db_pool, create_chat_session, get_connection, close_pool
from main import process_intake_task

async def simulate_traffic():
    await init_db()
    try:
        messages = [
            "Bought a 1500 GBP laptop and a 5 GBP coffee from Pret. Wait, the laptop is 50% for personal use.",
            "Taxi to London for 40 GBP, no VAT receipt. Plus 10 GBP tip.",
            "Paid my accountant 200 GBP for software subscription.",
            "Customer Dave Jenkins paid me 450 GBP for bathroom tiling.",
            "Bought a new suit for client meetings, 200 GBP at Marks & Spencer."
        ]
        
        num_requests = len(messages)
        print(f"Starting simulation of {num_requests} complex edge-case background tasks...")
        
        start_time = time.time()
        
        # 1. Create chat sessions
        # Relies on the updated base schema (ExpenseCategorization) with tax_code in agents.py
        # to ensure the dashboard populates fully without needing dynamic enums.
        chat_ids = []
        for i, msg in enumerate(messages):
            chat_id = await create_chat_session(sender_id=f"demo_user_{i}", message=msg, media_urls=[], turn_count=1)
            chat_ids.append(chat_id)
            
        print(f"Created {num_requests} DB chat sessions in {time.time() - start_time:.2f} seconds.")
        
        # 2. Run background tasks concurrently
        print("Executing AI extraction pipeline concurrently (hitting Gemma 4 & DB updates)...")
        tasks = []
        for i, (chat_id, msg) in enumerate(zip(chat_ids, messages)):
            tasks.append(
                process_intake_task(
                    chat_id=chat_id, 
                    sender_id=f"demo_user_{i}", 
                    message=msg, 
                    turn_count=1, 
                    media_urls=[]
                )
            )
            
        bg_start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        errors = [r for r in results if isinstance(r, Exception)]
        
        print(f"AI Pipeline completed in {time.time() - bg_start:.2f} seconds.")
        print(f"Total Tasks: {num_requests}, Errors: {len(errors)}")
        
        if errors:
            print(f"Sample error: {errors[0]}")
            
    finally:
        await close_pool()

if __name__ == '__main__':
    asyncio.run(simulate_traffic())
