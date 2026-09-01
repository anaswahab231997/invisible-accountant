import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the process_expense_message call in process_intake_task
old_intake_task = '''        if message.strip().lower() == "proceed":
            unconfirmed = await get_unconfirmed_session(sender_id)
            if unconfirmed:
                await confirm_and_queue_to_ledger(unconfirmed["id"])
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message="? All set! I've officially locked this into your tax ledger and it's queued for HMRC.",
                )
                from ws import manager
                await manager.send_personal_message({"type": "INTAKE_UPDATE", "chat_id": chat_id, "result": {"status": "CONFIRMED"}}, sender_id)
                return
            else:
                logger.info("Outbound WhatsApp message", sender_id=sender_id, message="You don't have any pending expenses to proceed with.")
                return

        result = await process_expense_message(message, turn_count, media_urls)'''

new_intake_task = '''        unconfirmed = await get_unconfirmed_session(sender_id)
        if message.strip().lower() == "proceed":
            if unconfirmed:
                await confirm_and_queue_to_ledger(unconfirmed["id"])
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message="? All set! I've officially locked this into your tax ledger and it's queued for HMRC.",
                )
                from ws import manager
                await manager.send_personal_message({"type": "INTAKE_UPDATE", "chat_id": chat_id, "result": {"status": "CONFIRMED"}}, sender_id)
                return
            else:
                logger.info("Outbound WhatsApp message", sender_id=sender_id, message="You don't have any pending expenses to proceed with.")
                return

        import json
        previous_state = json.loads(unconfirmed["staging_payload"]) if unconfirmed else None
        result = await process_expense_message(message, turn_count, media_urls, previous_state)'''

content = content.replace(old_intake_task, new_intake_task)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)


with open('agents.py', 'r', encoding='utf-8') as f:
    agents_content = f.read()

old_agents_def = '''async def process_expense_message(
    raw_message: str, turn_count: int = 1, media_urls: list = None
):'''
new_agents_def = '''async def process_expense_message(
    raw_message: str, turn_count: int = 1, media_urls: list = None, previous_state: dict = None
):'''
agents_content = agents_content.replace(old_agents_def, new_agents_def)

old_agents_call1 = '''        result = await _call_gemini(
            system_instruction, raw_message, media_urls, model="gemini-2.5-flash"
        )'''
new_agents_call1 = '''        
        if previous_state:
            import json
            raw_message = f"PREVIOUS STATE:\\n{json.dumps(previous_state, indent=2)}\\n\\nUSER'S LATEST MESSAGE:\\n{raw_message}\\n\\nINSTRUCTION: The user is replying to your previous question. Merge this new information with the PREVIOUS STATE. If they answered your question, update the missing fields (e.g. amount, vendor, category). If everything is now complete, set is_ambiguous to false."
            
        result = await _call_gemini(
            system_instruction, raw_message, media_urls, model="gemini-2.5-flash"
        )'''
agents_content = agents_content.replace(old_agents_call1, new_agents_call1)

with open('agents.py', 'w', encoding='utf-8') as f:
    f.write(agents_content)

print("Memory patches applied")
