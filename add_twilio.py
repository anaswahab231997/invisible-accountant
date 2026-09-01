import re

with open('main.py', 'r') as f:
    content = f.read()

# Insert the imports
if "from fastapi import Form" not in content:
    content = content.replace("from fastapi import FastAPI, Request", "from fastapi import FastAPI, Request, Form")

# Insert the Twilio route right before receive_whatsapp
twilio_code = """
@app.post("/webhook/twilio")
async def receive_twilio(
    request: Request,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: int = Form(0),
):
    sender_id = From.replace("whatsapp:", "")
    masked_message = mask_pii(Body)
    chat_id = await create_chat_session(sender_id, masked_message, [], 1)
    
    if masked_message.strip().lower() == "proceed":
        unconfirmed = await get_unconfirmed_session(sender_id)
        if unconfirmed:
            await confirm_and_queue_to_ledger(unconfirmed["id"])
            reply_text = "🔒 All set! I've officially locked this into your tax ledger and it's queued for HMRC."
            
            from ws import manager
            await manager.broadcast({
                "type": "INTAKE_UPDATE",
                "chat_id": chat_id,
                "result": {"status": "CONFIRMED"}
            })
        else:
            reply_text = "You don't have any pending expenses to proceed with."
        
        twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply_text}</Message></Response>'
        from fastapi.responses import Response
        return Response(content=twiml, media_type="application/xml")
    
    # Process AI
    result = await process_expense_message(masked_message, 1, [])
    
    if result:
        # Anti-Hallucination Pipeline
        verification = await verify_expense_hallucination(masked_message, result)
        if verification.get("is_hallucinated"):
            result["is_ambiguous"] = True
            result["auditor_question"] = verification.get("corrected_question", "I got confused. Could you repeat the amount and vendor?")

        # Anti-Junk Guard
        if not result.get("amount") and not result.get("is_ambiguous"):
            result["is_ambiguous"] = True
            result["auditor_question"] = "I couldn't detect an expense amount. Could you clarify the amount?"
        
        await stage_expense(chat_id, result)
        
        from ws import manager
        await manager.broadcast({
            "type": "INTAKE_UPDATE",
            "chat_id": chat_id,
            "result": result
        })

        if result.get("is_ambiguous"):
            reply_text = result.get("auditor_question", "Could you clarify that?")
        else:
            amount_formatted = f"£{result['amount']:.2f}"
            vendor = result.get("vendor", "the vendor")
            category = result.get("category", "General")
            reply_text = f"I've noted down {amount_formatted} spent at {vendor} for {category}. Does this look right? Reply 'proceed' to lock this into your tax ledger, or just tell me what to change."
    else:
        reply_text = "I couldn't process that. Try sending an expense like '£5 for coffee'."

    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{reply_text}</Message></Response>'
    from fastapi.responses import Response
    return Response(content=twiml, media_type="application/xml")

"""

if "/webhook/twilio" not in content:
    content = content.replace("@app.post(\"/webhook/whatsapp\")", twilio_code + "\n@app.post(\"/webhook/whatsapp\")")

with open('main.py', 'w') as f:
    f.write(content)
