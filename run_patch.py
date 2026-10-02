import re
import os

with open(r'c:\Antigravity\UK MTD\invisible-accountant\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update WhatsAppPayload
content = re.sub(r'turn_count: int = Field\(\s*default=1,\s*ge=1,', r'turn_count: int = Field(\n        default=0, \n        ge=0,', content)

# 2. Update Twilio webhook download & upload
old_twilio = '''        media_urls = []
        if NumMedia > 0 and MediaUrl0:
            media_urls.append(MediaUrl0)
            
        if not media_urls:
            raise ValueError("An image or PDF receipt is strictly required for HMRC MTD compliance (digital links). Text-only expenses are not permitted.")
        
        # Create the session
        chat_id = await create_chat_session(sender_id, masked_message, media_urls, 1)
        
        # Push to background DB queue to avoid 15s Twilio timeout during LLM processing
        from db import push_intake_queue
        await push_intake_queue(
            chat_id,
            sender_id,
            masked_message,
            media_urls,
            1
        )'''

new_twilio = '''        from db import get_unconfirmed_session
        unconfirmed = await get_unconfirmed_session(sender_id)
        turn_count = 1 if unconfirmed else 0

        media_urls = []
        if NumMedia > 0 and MediaUrl0:
            import httpx
            import boto3
            import uuid
            import asyncio
            async with httpx.AsyncClient() as client:
                auth = (os.environ.get('TWILIO_ACCOUNT_SID', ''), os.environ.get('TWILIO_AUTH_TOKEN', '')) if os.environ.get('TWILIO_ACCOUNT_SID') else None
                try:
                    resp = await client.get(MediaUrl0, auth=auth)
                    if resp.status_code == 200:
                        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME", "invisible-accountant-uploads")
                        upload_id = str(uuid.uuid4())
                        ct = resp.headers.get('content-type', 'image/jpeg')
                        ext = 'pdf' if 'pdf' in ct else 'jpeg'
                        key = f"receipts/{upload_id}.{ext}"
                        s3_client = boto3.client('s3')
                        await asyncio.to_thread(s3_client.put_object, Bucket=bucket_name, Key=key, Body=resp.content, ContentType=ct)
                        media_urls.append(f"s3://{bucket_name}/{key}")
                    else:
                        media_urls.append(MediaUrl0)
                except Exception as e:
                    logger.error("Failed S3 upload", error=str(e))
                    media_urls.append(MediaUrl0)
            
        if turn_count == 0 and not media_urls:
            raise ValueError("An image or PDF receipt is strictly required for HMRC MTD compliance (digital links). Text-only expenses are not permitted.")
        
        # Create the session
        chat_id = await create_chat_session(sender_id, masked_message, media_urls, turn_count)
        
        # Push to background DB queue to avoid 15s Twilio timeout during LLM processing
        from db import push_intake_queue
        await push_intake_queue(
            chat_id,
            sender_id,
            masked_message,
            media_urls,
            turn_count
        )'''

content = content.replace(old_twilio, new_twilio)

# 3. Update £0.0 Logic Flaw in intake task
old_validation = '''            # Anti-Junk Guard
            has_amount = result.get("gross_amount") or result.get("net_amount") or (result.get("line_items") and len(result.get("line_items")) > 0)
            if not has_amount and not result.get("is_ambiguous"):'''

new_validation = '''            # Anti-Junk Guard
            gross_amount = result.get("gross_amount")
            net_amount = result.get("net_amount")
            has_amount = (gross_amount is not None and float(gross_amount) > 0) or (net_amount is not None and float(net_amount) > 0) or (result.get("line_items") and len(result.get("line_items")) > 0)
            if not has_amount and not result.get("is_ambiguous"):'''

content = content.replace(old_validation, new_validation)

# 4. Proceed override re-run validation
old_proceed = '''                await confirm_and_queue_to_ledger(unconfirmed["id"])
                success_msg = "✅ All set! I've officially locked this into your tax ledger and it's queued for HMRC."'''

new_proceed = '''                import json
                payload_str = unconfirmed.get("staging_payload")
                if payload_str:
                    payload = json.loads(payload_str)
                    gross = payload.get("gross_amount")
                    net = payload.get("net_amount")
                    if not ((gross is not None and float(gross) > 0) or (net is not None and float(net) > 0) or (payload.get("line_items") and len(payload.get("line_items")) > 0)):
                        err_msg = "Cannot proceed: No valid expense amount > 0 detected."
                        if not sender_id.startswith("demo_web_") and os.environ.get('TWILIO_ACCOUNT_SID'):
                            from twilio.rest import Client
                            client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
                            to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                            await asyncio.to_thread(client.messages.create, body=err_msg, from_=os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034'), to=to_formatted)
                        return
                await confirm_and_queue_to_ledger(unconfirmed["id"])
                success_msg = "✅ All set! I've officially locked this into your tax ledger and it's queued for HMRC."'''

content = content.replace(old_proceed, new_proceed)

# 5. verify_expense_hallucination signature change in main.py
old_verify = '''            verification = await verify_expense_hallucination(message, result, sender_id=sender_id)'''
new_verify = '''            verification = await verify_expense_hallucination(message, result, sender_id=sender_id, media_urls=media_urls)'''
content = content.replace(old_verify, new_verify)

with open(r'c:\Antigravity\UK MTD\invisible-accountant\main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched main.py')

# Patch worker.py
with open(r'c:\Antigravity\UK MTD\invisible-accountant\worker.py', 'r', encoding='utf-8') as f:
    wcontent = f.read()

sms_func = '''
def get_twilio_client():
    from twilio.rest import Client
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')
    if sid and token: return Client(sid, token)
    return None

async def send_failure_sms(sender_id: str):
    if not sender_id or sender_id.startswith("demo_web_"): return
    import asyncio
    client = get_twilio_client()
    if not client: return
    to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
    from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034')
    try:
        await asyncio.to_thread(
            client.messages.create,
            body="Alert: Your expense submission failed due to an integration issue (e.g. token expired). Please re-authenticate.",
            from_=from_number,
            to=to_formatted
        )
    except Exception as e:
        logger.error("Failed to send Twilio SMS", error=str(e))
'''

wcontent = wcontent.replace('logger = get_logger(__name__)', 'logger = get_logger(__name__)\n' + sms_func)

wcontent = wcontent.replace(
'''                    await conn.execute("UPDATE hmrc_ledger SET status = 'FAILED' WHERE id = $1", item["id"])
                    from adapters.base_adapter import AuthenticationError''',
'''                    await conn.execute("UPDATE hmrc_ledger SET status = 'FAILED' WHERE id = $1", item["id"])
                    await send_failure_sms(item["sender_id"])
                    from adapters.base_adapter import AuthenticationError'''
)

old_else_fail = '''        else:
            from db import mark_hmrc_failed
            await mark_hmrc_failed(item["id"])
            raise e'''
new_else_fail = '''        else:
            from db import mark_hmrc_failed
            await mark_hmrc_failed(item["id"])
            await send_failure_sms(item.get("sender_id"))
            raise e'''
wcontent = wcontent.replace(old_else_fail, new_else_fail)

old_retry_fail = '''                        UPDATE hmrc_ledger 
                        SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                            retry_count = retry_count + 1,
                            next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                        WHERE id = $1
                    """, item["id"])'''
new_retry_fail = '''                        UPDATE hmrc_ledger 
                        SET status = CASE WHEN retry_count >= 5 THEN 'FAILED' ELSE 'PENDING' END,
                            retry_count = retry_count + 1,
                            next_retry_at = NOW() + (INTERVAL '1 minute' * pow(2, retry_count))
                        WHERE id = $1
                        RETURNING status
                    """, item["id"])
                    if row and row["status"] == 'FAILED': await send_failure_sms(item.get("sender_id"))'''
# wait, fetchrow is needed instead of execute
wcontent = wcontent.replace('await conn.execute("""\n                        UPDATE hmrc_ledger', 'row = await conn.fetchrow("""\n                        UPDATE hmrc_ledger')
wcontent = wcontent.replace(old_retry_fail, new_retry_fail)

with open(r'c:\Antigravity\UK MTD\invisible-accountant\worker.py', 'w', encoding='utf-8') as f:
    f.write(wcontent)
print('Patched worker.py')

# Patch agents.py
with open(r'c:\Antigravity\UK MTD\invisible-accountant\agents.py', 'r', encoding='utf-8') as f:
    acontent = f.read()

acontent = acontent.replace(
'''    if not media_urls:
        raise ValueError("An image or PDF receipt is strictly required for HMRC MTD compliance (digital links). Text-only expenses are not permitted.")''',
'''    if turn_count == 0 and not media_urls:
        raise ValueError("An image or PDF receipt is strictly required for HMRC MTD compliance (digital links). Text-only expenses are not permitted.")'''
)

acontent = acontent.replace(
'''async def verify_expense_hallucination(raw_message: str, parsed_json: dict, sender_id: str = None) -> dict:''',
'''async def verify_expense_hallucination(raw_message: str, parsed_json: dict, sender_id: str = None, media_urls: list = None) -> dict:'''
)

acontent = acontent.replace(
'''            return await _do_verify_expense_hallucination(raw_message, parsed_json)''',
'''            return await _do_verify_expense_hallucination(raw_message, parsed_json, media_urls)'''
)

old_do_verify = '''async def _do_verify_expense_hallucination(raw_message: str, parsed_json: dict) -> dict:
    system_instruction = """
    You are an Anti-Hallucination Auditor. Your strict job is to compare the raw user text to the parsed JSON.
    Did the AI hallucinate a gross_amount, vendor, or date that the user did NOT actually say?
    For example, if the user says "lunch" and the AI outputs "vendor: Unknown, gross_amount: 0.0", that is a hallucination/failure.
    If the user says "spent 50 at tesco" and AI outputs "gross_amount: 50.0", that is valid.
    Return true for hallucination if the gross_amount or vendor is completely fabricated.
    """
    contents = [
        f"USER MESSAGE: {raw_message}",
        f"PARSED JSON: {json.dumps(parsed_json)}"
    ]'''

new_do_verify = '''async def _do_verify_expense_hallucination(raw_message: str, parsed_json: dict, media_urls: list = None) -> dict:
    system_instruction = """
    You are an Anti-Hallucination Auditor. Your strict job is to compare the raw user text to the parsed JSON.
    Did the AI hallucinate a gross_amount, vendor, or date that the user did NOT actually say?
    For example, if the user says "lunch" and the AI outputs "vendor: Unknown, gross_amount: 0.0", that is a hallucination/failure.
    If the user says "spent 50 at tesco" and AI outputs "gross_amount: 50.0", that is valid.
    Return true for hallucination if the gross_amount or vendor is completely fabricated.
    """
    contents = []
    if media_urls:
        import asyncio, httpx
        from google.genai import types
        async with httpx.AsyncClient() as http_client:
            async def fetch_media(url):
                try:
                    resp = await http_client.get(url, timeout=5.0)
                    if resp.status_code == 200:
                        mime_type = resp.headers.get("content-type", "image/jpeg")
                        return types.Part.from_bytes(data=resp.content, mime_type=mime_type)
                except Exception:
                    pass
                return None
            tasks = [fetch_media(url) for url in media_urls]
            parts = await asyncio.gather(*tasks)
            contents.extend([p for p in parts if p is not None])
    contents.append(f"USER MESSAGE: {raw_message}")
    contents.append(f"PARSED JSON: {json.dumps(parsed_json)}")'''

acontent = acontent.replace(old_do_verify, new_do_verify)

with open(r'c:\Antigravity\UK MTD\invisible-accountant\agents.py', 'w', encoding='utf-8') as f:
    f.write(acontent)
print('Patched agents.py')

