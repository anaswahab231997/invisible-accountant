import asyncio
import time
from db import init_db, db_pool, create_chat_session, get_connection
from main import process_intake_task

async def simulate_traffic(num_requests=50):
    await init_db()
    print(f"Starting simulation of {num_requests} concurrent background tasks...")
    
    start_time = time.time()
    
    # 1. Create chat sessions (simulating the fast webhook part)
    chat_ids = []
    for i in range(num_requests):
        chat_id = await create_chat_session(sender_id=f"user_{i}", raw_message=f"lunch {i} amount 10", media_urls=[], turn_count=1)
        chat_ids.append(chat_id)
        
    print(f"Created {num_requests} DB chat sessions in {time.time() - start_time:.2f} seconds.")
    
    # 2. Run background tasks concurrently
    print("Executing background tasks concurrently (hitting Gemini & DB updates)...")
    tasks = []
    for i, chat_id in enumerate(chat_ids):
        tasks.append(
            process_intake_task(
                chat_id=chat_id, 
                sender_id=f"user_{i}", 
                message=f"lunch {i} amount 10", 
                turn_count=1, 
                media_urls=[]
            )
        )
        
    bg_start = time.time()
    # We use return_exceptions=True so one failure doesn't stop everything
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    errors = [r for r in results if isinstance(r, Exception)]
    
    print(f"Background tasks completed in {time.time() - bg_start:.2f} seconds.")
    print(f"Total Tasks: {num_requests}, Errors: {len(errors)}")
    
    if errors:
        print(f"Sample error: {errors[0]}")
        
    await db_pool.close_pool()

if __name__ == '__main__':
    asyncio.run(simulate_traffic(20))
