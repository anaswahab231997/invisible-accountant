import re

with open('worker.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace get_all_hmrc_queue if it exists in imports
text = text.replace('get_all_hmrc_queue,', 'get_pending_hmrc_queue,')
text = text.replace('await get_all_hmrc_queue()', 'await get_pending_hmrc_queue()')

# Rewrite the error handling block
old_block = '''        if e.status_code in (401, 429, 500, 502, 503, 504):
            logger.info("Transient/Auth error, reverting to PENDING for retry", queue_id=item["id"])
            from db import get_connection
            async with get_connection() as conn:
                await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE id = ", item["id"])
        else:
            from db import mark_hmrc_failed
            await mark_hmrc_failed(item["id"])
    except Exception as e:
        logger.error("Unexpected error in worker", queue_id=item["id"], error=str(e))
        from db import get_connection
        async with get_connection() as conn:
            await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE id = ", item["id"])'''

new_block = '''        if e.status_code in (401, 429, 500, 502, 503, 504):
            logger.info("Transient/Auth error, applying exponential backoff", queue_id=item["id"])
            from db import get_connection
            async with get_connection() as conn:
                # Force token wipe on 401
                if e.status_code == 401:
                    logger.warning("401 Unauthorized - wiping token for re-auth", whatsapp_id=item["sender_id"])
                    await conn.execute("DELETE FROM hmrc_identity_vault WHERE whatsapp_id = ", item["sender_id"])
                
                await conn.execute("""
                    UPDATE hmrc_ledger 
                    SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                        retry_count = retry_count + 1,
                        next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                    WHERE id = 
                """, item["id"])
        else:
            from db import mark_hmrc_failed
            await mark_hmrc_failed(item["id"])
    except Exception as e:
        logger.error("Unexpected error in worker", queue_id=item["id"], error=str(e))
        from db import get_connection
        async with get_connection() as conn:
            await conn.execute("""
                UPDATE hmrc_ledger 
                SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                    retry_count = retry_count + 1,
                    next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                WHERE id = 
            """, item["id"])'''

if old_block in text:
    text = text.replace(old_block, new_block)
    with open('worker.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched worker.py!")
else:
    print("Could not find the target block in worker.py!")
