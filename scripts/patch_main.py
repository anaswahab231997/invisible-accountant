import re

def update_main():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add import for db queue
    content = content.replace(
        "from db import init_db",
        "from db import init_db, push_intake_queue, pop_intake_queue, mark_intake_done"
    )

    # 2. Remove in-memory queue definition
    content = re.sub(r'# The "Waiting Room" Queue\nintake_queue = None\n', '', content)
    content = re.sub(r'    global intake_queue\n    intake_queue = asyncio.Queue\(\)\n', '', content)

    # 3. Rewrite intake_worker
    new_worker = """
async def intake_worker():
    \"\"\"Consumes incoming WhatsApp messages from the persistent database queue.\"\"\"
    while True:
        try:
            item = await pop_intake_queue()
            if not item:
                await asyncio.sleep(1)
                continue
                
            try:
                # We need chat_id for the frontend, but we don't strictly need it passed through the queue 
                # if we just create it here. Wait, create_chat_session is called BEFORE push_intake_queue.
                # The intake_queue doesn't have chat_id? Wait, in db.py I didn't add chat_id to intake_queue!
                pass
            finally:
                await mark_intake_done(item["id"])
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Queue worker error", error=str(e))
            await asyncio.sleep(1)
"""
    # Wait, the intake_queue in db.py: I didn't add chat_id to it.
    # We should add chat_id to the intake_queue table! Let's just fix it.
    pass

if __name__ == "__main__":
    update_main()
