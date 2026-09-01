import re

with open('agents.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove tenacity @retry from _call_gemini
retry_block_1 = '''@retry(
    wait=wait_exponential(multiplier=2, min=2, max=65),
    stop=stop_after_attempt(10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def _call_gemini(
    system_instruction: str,
    user_input: str,
    media_urls: list = None,
    model: str = "gemini-2.5-flash",
):'''
new_call_gemini = '''async def _call_gemini(
    system_instruction: str,
    user_input: str,
    media_urls: list = None,
    model: str = "gemini-2.5-flash",
    sender_id: str = None,
):
    import asyncio
    from ws import manager
    attempts = 0
    while attempts < 10:
        try:
            return await _do_call_gemini(system_instruction, user_input, media_urls, model)
        except Exception as e:
            attempts += 1
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if sender_id and attempts == 1:
                    await manager.send_personal_message({"type": "GRACEFUL_WARNING", "message": "I'm experiencing high traffic right now! Bear with me for a few seconds... ?"}, sender_id)
                await asyncio.sleep(min(65, 2 ** attempts))
            else:
                if attempts >= 5:
                    raise e
                await asyncio.sleep(min(10, 2 ** attempts))
    raise Exception("Max retries exceeded")

async def _do_call_gemini(
    system_instruction: str,
    user_input: str,
    media_urls: list = None,
    model: str = "gemini-2.5-flash",
):'''
content = content.replace(retry_block_1, new_call_gemini)

# 2. Add sender_id to process_expense_message and pass it to _call_gemini
content = content.replace('previous_state: dict = None\n):', 'previous_state: dict = None, sender_id: str = None\n):')
content = content.replace('media_urls, model="gemini-2.5-flash"\n        )', 'media_urls, model="gemini-2.5-flash", sender_id=sender_id\n        )')
content = content.replace('media_urls, model="gemini-2.5-flash"\n            )', 'media_urls, model="gemini-2.5-flash", sender_id=sender_id\n            )')

# 3. Remove tenacity @retry from verify_expense_hallucination
retry_block_2 = '''@retry(
    wait=wait_exponential(multiplier=2, min=2, max=65),
    stop=stop_after_attempt(10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def verify_expense_hallucination(raw_message: str, parsed_json: dict) -> dict:'''
new_verify = '''async def verify_expense_hallucination(raw_message: str, parsed_json: dict, sender_id: str = None) -> dict:
    import asyncio
    from ws import manager
    attempts = 0
    while attempts < 10:
        try:
            return await _do_verify_expense_hallucination(raw_message, parsed_json)
        except Exception as e:
            attempts += 1
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                if sender_id and attempts == 1:
                    await manager.send_personal_message({"type": "GRACEFUL_WARNING", "message": "Still thinking... checking HMRC guidelines... ??"}, sender_id)
                await asyncio.sleep(min(65, 2 ** attempts))
            else:
                if attempts >= 5:
                    raise e
                await asyncio.sleep(min(10, 2 ** attempts))
    raise Exception("Max retries exceeded")

async def _do_verify_expense_hallucination(raw_message: str, parsed_json: dict) -> dict:'''
content = content.replace(retry_block_2, new_verify)

with open('agents.py', 'w', encoding='utf-8') as f:
    f.write(content)

# 4. Update main.py to pass sender_id
with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()
    
main_content = main_content.replace('process_expense_message(message, turn_count, media_urls, previous_state)', 'process_expense_message(message, turn_count, media_urls, previous_state, sender_id=sender_id)')
main_content = main_content.replace('process_expense_message(masked_message, 1, [])', 'process_expense_message(masked_message, 1, [], sender_id=sender_id)')
main_content = main_content.replace('verify_expense_hallucination(message, result)', 'verify_expense_hallucination(message, result, sender_id=sender_id)')
main_content = main_content.replace('verify_expense_hallucination(masked_message, result)', 'verify_expense_hallucination(masked_message, result, sender_id=sender_id)')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)

# 5. Update landing_page.html to handle GRACEFUL_WARNING
with open('landing_page.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

ws_logic = '''                const data = JSON.parse(event.data);
                if (data.type === 'INTAKE_UPDATE') {'''
new_ws_logic = '''                const data = JSON.parse(event.data);
                if (data.type === 'GRACEFUL_WARNING') {
                    const typingIndicator = document.getElementById('typing-indicator');
                    if (typingIndicator) {
                        const warningDiv = document.createElement('div');
                        warningDiv.className = 'text-xs text-slate mt-1 italic animate-pulse';
                        warningDiv.innerText = data.message;
                        typingIndicator.appendChild(warningDiv);
                        document.getElementById('chatBody').scrollTop = document.getElementById('chatBody').scrollHeight;
                    }
                }
                if (data.type === 'INTAKE_UPDATE') {'''
html_content = html_content.replace(ws_logic, new_ws_logic)

with open('landing_page.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Graceful warning patched")
