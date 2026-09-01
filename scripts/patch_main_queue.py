import re

def patch():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    old_queue_put = """    # Place the message into the Waiting Room queue instead of unbounded background tasks
    await intake_queue.put((
        chat_id,
        payload.sender_id,
        llm_message,
        payload.turn_count,
        payload.media_urls or []
    ))"""

    new_queue_put = """    # Place the message into the durable database queue
    from db import push_intake_queue
    await push_intake_queue(
        chat_id,
        payload.sender_id,
        llm_message,
        payload.media_urls or [],
        payload.turn_count
    )"""
    content = content.replace(old_queue_put, new_queue_put)

    old_queue_put2 = """    await intake_queue.put((
        chat_id,
        payload.sender_id,
        llm_message,
        payload.turn_count,
        payload.media_urls or []
    ))"""
    
    new_queue_put2 = """    from db import push_intake_queue
    await push_intake_queue(
        chat_id,
        payload.sender_id,
        llm_message,
        payload.media_urls or [],
        payload.turn_count
    )"""
    content = content.replace(old_queue_put2, new_queue_put2)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch()
