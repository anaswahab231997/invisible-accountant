import asyncio
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    Form,
    Security,
)
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, HttpUrl
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agents import process_expense_message, verify_expense_hallucination
from db import (
    get_all_hmrc_queue,
    get_hmrc_ledger_by_chat,
    get_recent_intakes_by_sender,
    get_unconfirmed_session,
    stage_expense,
    confirm_and_queue_to_ledger,
    init_db,
    create_chat_session,
    store_identity_in_vault,
)
from logger import get_logger
from worker import process_hmrc_queue, process_ttl_sweeper

logger = get_logger(__name__)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Invisible Accountant Webhook Prototype (V2 Enterprise)")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)

_background_tasks = set()

@app.get("/health")
async def health_check():
    return {"status": "ok"}


class WhatsAppPayload(BaseModel):
    sender_id: str
    message: str = Field(..., max_length=1000)
    media_urls: list[HttpUrl] | None = None
    turn_count: int = Field(
        default=1, 
        ge=1, 
        le=10, 
        description="Number of conversational turns so far. Max 10."
    )





@app.get("/generate_presigned_url")
async def get_presigned_url():
    mock_upload_id = str(uuid.uuid4())
    return {
        "upload_url": f"https://mock-s3-bucket.amazonaws.com/uploads/{mock_upload_id}?AWSAccessKeyId=MOCK&Signature=MOCK",
        "expires_in": 3600,
    }


async def process_intake_task(
    chat_id: int, sender_id: str, message: str, turn_count: int, media_urls: list
):
    try:
        if message.strip().lower() == "proceed":
            unconfirmed = await get_unconfirmed_session(sender_id)
            if unconfirmed:
                await confirm_and_queue_to_ledger(unconfirmed["id"])
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message="✅ All set! I've officially locked this into your tax ledger and it's queued for HMRC.",
                )
                from ws import manager
                await manager.broadcast({
                    "type": "INTAKE_UPDATE",
                    "chat_id": chat_id,
                    "result": {"status": "CONFIRMED"}
                })
                return
            else:
                logger.info("Outbound WhatsApp message", sender_id=sender_id, message="You don't have any pending expenses to proceed with.")
                return

        result = await process_expense_message(message, turn_count, media_urls)

        if result:
            # Anti-Hallucination Pipeline
            verification = await verify_expense_hallucination(message, result)
            if verification.get("is_hallucinated"):
                result["is_ambiguous"] = True
                result["auditor_question"] = verification.get("corrected_question", "I got confused. Could you repeat the amount and vendor?")

            # Anti-Junk Guard
            if not result.get("amount") and not result.get("is_ambiguous"):
                result["is_ambiguous"] = True
                result["auditor_question"] = "I couldn't detect an expense amount. Could you clarify the amount?"
            
            # Staging Gate
            await stage_expense(chat_id, result)
            
            # Broadcast the update via WebSocket
            from ws import manager
            await manager.broadcast({
                "type": "INTAKE_UPDATE",
                "chat_id": chat_id,
                "result": result
            })

            if result.get("is_ambiguous"):
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message=result["auditor_question"],
                )
            else:
                amount_formatted = f"£{result['amount']:.2f}"
                vendor = result['vendor']
                category = result['category']
                layman_msg = f"I've noted down {amount_formatted} spent at {vendor} for {category}. Does this look right? Reply 'proceed' to lock this into your tax ledger, or just tell me what to change."
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message=layman_msg,
                )

    except Exception as e:
        logger.error("Error processing intake", chat_id=chat_id, error=str(e))
        from ws import manager
        await manager.broadcast({
            "type": "INTAKE_UPDATE",
            "chat_id": chat_id,
            "result": {"is_ambiguous": True, "auditor_question": "An internal error occurred."}
        })


from security import mask_pii, verify_whatsapp_signature, encrypt_token

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
API_KEY = os.environ.get("API_KEY")

if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable is missing.")

if not API_KEY:
    raise ValueError("API_KEY environment variable is missing.")

api_key_header = APIKeyHeader(name="X-API-Key")

# The "Waiting Room" Queue
intake_queue = None

async def intake_worker():
    """Consumes incoming WhatsApp messages from the queue to prevent API/DB overload."""
    while True:
        try:
            task = await intake_queue.get()
            try:
                chat_id, sender_id, message, turn_count, media_urls = task
                await process_intake_task(chat_id, sender_id, message, turn_count, media_urls)
            finally:
                intake_queue.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Queue worker error", error=str(e))


@app.on_event("startup")
async def startup_event():
    global intake_queue
    intake_queue = asyncio.Queue()
    
    await init_db()
    task1 = asyncio.create_task(process_hmrc_queue())
    task2 = asyncio.create_task(process_ttl_sweeper())
    _background_tasks.add(task1)
    _background_tasks.add(task2)
    
    # Spawn 5 dedicated AI workers for the Waiting Room
    for _ in range(5):
        worker = asyncio.create_task(intake_worker())
        _background_tasks.add(worker)


@app.on_event("shutdown")
async def shutdown_event():
    for task in _background_tasks:
        task.cancel()
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()
    
    from db import close_pool
    await close_pool()


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
            reply_text = "[LOCKED] All set! I've officially locked this into your tax ledger and it's queued for HMRC."
            
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
        verification = await verify_expense_hallucination(masked_message, result)
        if verification.get("is_hallucinated"):
            result["is_ambiguous"] = True
            result["auditor_question"] = verification.get("corrected_question", "I got confused. Could you repeat the amount and vendor?")

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

@app.post("/webhook/whatsapp")
async def receive_whatsapp(
    payload: WhatsAppPayload,
    request: Request,
    x_hub_signature_256: str = Header(None),
):
    # Our real security guard: WhatsApp's HMAC signature
    raw_body = await request.body()
    verify_whatsapp_signature(raw_body, x_hub_signature_256, WEBHOOK_SECRET)

    masked_message = mask_pii(payload.message)
    media_urls_str = [str(url) for url in (payload.media_urls or [])]

    chat_id = await create_chat_session(
        payload.sender_id, masked_message, media_urls_str, payload.turn_count
    )

    llm_message = masked_message
    if payload.turn_count > 1:
        history = await get_recent_intakes_by_sender(
            payload.sender_id, limit=payload.turn_count
        )
        llm_message = "\n---\n".join(history)

    # Place the message into the Waiting Room queue instead of unbounded background tasks
    await intake_queue.put((
        chat_id,
        payload.sender_id,
        llm_message,
        payload.turn_count,
        payload.media_urls or []
    ))

    return {
        "status": "success",
        "chat_id": chat_id,
        "message": "Payload received and queued in the waiting room.",
    }


def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


@app.get("/queue", dependencies=[Depends(verify_api_key)])
async def view_hmrc_queue(limit: int = 100, offset: int = 0):
    return {"queue": await get_all_hmrc_queue(limit=limit, offset=offset)}

@app.get("/api/queue")
async def view_hmrc_queue_bff(limit: int = 100, offset: int = 0):
    # BFF route for the frontend dashboard. In a real app, we'd check session cookies.
    return {"queue": await get_all_hmrc_queue(limit=limit, offset=offset)}


@app.get("/expense/{chat_id}", dependencies=[Depends(verify_api_key)])
async def get_expense_status(chat_id: int):
    record = await get_hmrc_queue_by_intake(chat_id)
    if not record:
        raise HTTPException(status_code=404, detail="Not processed yet")
    return record


from ws import manager
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/queue")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)

@app.post("/api/simulate_whatsapp")
async def api_simulate_whatsapp(
    payload: WhatsAppPayload,
):
    # This is the BFF route for the frontend Simulator. No HMAC required.
    masked_message = mask_pii(payload.message)
    media_urls_str = [str(url) for url in (payload.media_urls or [])]

    chat_id = await create_chat_session(
        payload.sender_id, masked_message, media_urls_str, payload.turn_count
    )

    llm_message = masked_message
    if payload.turn_count > 1:
        history = await get_recent_intakes_by_sender(
            payload.sender_id, limit=payload.turn_count
        )
        llm_message = "\n---\n".join(history)

    await intake_queue.put((
        chat_id,
        payload.sender_id,
        llm_message,
        payload.turn_count,
        payload.media_urls or []
    ))

    return {
        "status": "success",
        "chat_id": chat_id,
        "message": "Payload received and queued in the waiting room.",
    }

from db import create_oauth_state, consume_oauth_state

@app.get("/auth")
async def auth(whatsapp_id: str):
    client_id = os.environ.get("HMRC_CLIENT_ID", "mock_client_id")
    redirect_uri = os.environ.get("HMRC_REDIRECT_URI", "http://localhost:8000/callback")
    
    state_uuid = await create_oauth_state(whatsapp_id)
    url = f"https://test-api.service.hmrc.gov.uk/oauth/authorize?response_type=code&client_id={client_id}&scope=read:self-assessment write:self-assessment&state={state_uuid}&redirect_uri={redirect_uri}"
    return RedirectResponse(url)

@app.get("/callback")
async def callback(code: str, state: str):
    whatsapp_id = await consume_oauth_state(state)
    if not whatsapp_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
    client_id = os.environ.get("HMRC_CLIENT_ID")
    client_secret = os.environ.get("HMRC_CLIENT_SECRET")
    redirect_uri = os.environ.get("HMRC_REDIRECT_URI", "https://invisibleaccount.co.uk/callback")
    base_url = os.environ.get("HMRC_BASE_URL", "https://test-api.service.hmrc.gov.uk")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{base_url}/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {resp.text}")
            
        token_data = resp.json()
        
    # Store the actual tokens securely in the vault
    encrypted_dict = encrypt_token(json.dumps(token_data))
    await store_identity_in_vault(whatsapp_id, json.dumps(encrypted_dict).encode("utf-8"))
    
    return HTMLResponse("<h1>Success! Your identity has been securely vaulted. You can return to WhatsApp.</h1>")

# Serve the landing page at the root URL
@app.get("/")
async def serve_landing_page():
    from fastapi.responses import FileResponse
    return FileResponse("landing_page.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
