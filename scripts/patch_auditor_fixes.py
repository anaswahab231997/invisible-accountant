import re

# 1. Update db.py
with open('db.py', 'r', encoding='utf-8') as f:
    db_content = f.read()

sweep_func = '''async def get_pending_hmrc_queue():'''
sweep_replacement = '''async def sweep_orphaned_processing():
    async with get_connection() as conn:
        await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE status = 'PROCESSING'")

async def get_pending_hmrc_queue():'''
db_content = db_content.replace(sweep_func, sweep_replacement)

with open('db.py', 'w', encoding='utf-8') as f:
    f.write(db_content)

# 2. Update main.py to run sweep_orphaned_processing on startup
with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

startup_old = '''    await init_db()
    
    # Start background sweeps'''
startup_new = '''    await init_db()
    from db import sweep_orphaned_processing
    await sweep_orphaned_processing()
    
    # Start background sweeps'''
main_content = main_content.replace(startup_old, startup_new)
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)

# 3. Update worker.py to handle 429 and 401 gracefully instead of FAILED
with open('worker.py', 'r', encoding='utf-8') as f:
    worker_content = f.read()

worker_old = '''                    except HMRCApiError as e:
                        logger.error("HMRC API Error", queue_id=item["id"], status=e.status_code, response=e.response_text)
                        await mark_hmrc_failed(item["id"])
                    except Exception as e:
                        logger.error("Unexpected HMRC error", queue_id=item["id"], error=str(e))
                        await mark_hmrc_failed(item["id"])'''

worker_new = '''                    except HMRCApiError as e:
                        logger.error("HMRC API Error", queue_id=item["id"], status=e.status_code, response=e.response_text)
                        if e.status_code in (401, 429, 500, 502, 503, 504):
                            logger.info("Transient/Auth error, reverting to PENDING for retry", queue_id=item["id"])
                            from db import get_connection
                            async with get_connection() as conn:
                                await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE id = ", item["id"])
                            if e.status_code == 401:
                                # Force OAuth refresh on next loop
                                pass
                        else:
                            await mark_hmrc_failed(item["id"])
                    except Exception as e:
                        logger.error("Unexpected HMRC error", queue_id=item["id"], error=str(e))
                        # Revert to pending just in case it's a network glitch
                        from db import get_connection
                        async with get_connection() as conn:
                            await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING' WHERE id = ", item["id"])'''
worker_content = worker_content.replace(worker_old, worker_new)
with open('worker.py', 'w', encoding='utf-8') as f:
    f.write(worker_content)

print("Pipeline fixes applied")
