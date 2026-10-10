import asyncio
import json
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import (Response,
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

from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, HttpUrl
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agents import process_expense_message, verify_expense_hallucination
from db import get_identity_from_vault
from adapters.universal_adapter import UniversalAdapter
universal_adapter = UniversalAdapter()
from models.unified_record import TargetSystem
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
from dashboard import router as dashboard_router
from dev_dashboard import router as dev_dashboard_router
from logger import get_logger
from worker import process_hmrc_queue, process_ttl_sweeper

logger = get_logger(__name__)
def get_real_ip(request: Request) -> str:
    return request.headers.get("CF-Connecting-IP", request.client.host if request.client else "127.0.0.1")
limiter = Limiter(key_func=get_real_ip)

app = FastAPI(
    title="Invisible Accountant",
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    return response

app.include_router(dashboard_router)
app.include_router(dev_dashboard_router)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
#title="Invisible Accountant Webhook Prototype (V2 Enterprise)", docs_url=None, redoc_url=None, openapi_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# HSTS Middleware removed to prevent localhost HTTPS lockouts

# Instrumentator().instrument(app).expose(app) # Disabled to fix Exposed Metrics Endpoint finding

_background_tasks = set()

@app.get("/health")
async def health_check():
    return {"status": "ok"}


class WhatsAppPayload(BaseModel):
    sender_id: str
    message: str = Field(..., max_length=1000)
    media_urls: list[HttpUrl] | None = None
    turn_count: int = Field(
        default=0, 
        ge=0, 
        le=10, 
        description="Number of conversational turns so far. Max 10."
    )





import boto3
from botocore.exceptions import ClientError

@app.get("/generate_presigned_url")
async def get_presigned_url(request: Request, content_type: str = "image/jpeg"):
    import secrets
    api_key = request.headers.get("X-API-Key")
    if not api_key or not os.environ.get("API_KEY") or not secrets.compare_digest(api_key, os.environ.get("API_KEY")):
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    upload_id = str(uuid.uuid4())
    s3_client = boto3.client('s3')
    bucket_name = os.environ.get("AWS_S3_BUCKET_NAME", "invisible-accountant-uploads")
    try:
        response = s3_client.generate_presigned_url('put_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': f"uploads/{upload_id}",
                                                            'ContentType': content_type},
                                                    ExpiresIn=3600)
    except ClientError as e:
        logger.error("Failed to generate presigned URL", error=str(e))
        raise HTTPException(status_code=500, detail="Could not generate upload URL")
    
    return {
        "upload_url": response,
        "expires_in": 3600,
    }


def safe_float(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    import re
    cleaned = re.sub(r'[^\d\.-]', '', str(val))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

async def process_intake_task(
    chat_id: int, sender_id: str, message: str, turn_count: int, media_urls: list
):
    try:
        if message.strip().lower() == "proceed":
            unconfirmed = await get_unconfirmed_session(sender_id)
            if unconfirmed:
                import json
                payload_str = unconfirmed.get("staging_payload")
                if payload_str:
                    payload = json.loads(payload_str)
                    gross = payload.get("gross_amount")
                    net = payload.get("net_amount")
                    line_items_sum = sum(safe_float(item.get("unit_amount") or item.get("net_amount") or item.get("amount") or 0.0) for item in payload.get("line_items", []))
                    if not ((gross is not None and safe_float(gross) != 0.0) or (net is not None and safe_float(net) != 0.0) or line_items_sum != 0.0):
                        err_msg = "Cannot proceed: No valid expense amount detected (net sum is 0.0)."
                        if not sender_id.startswith("demo_web_") and os.environ.get('TWILIO_ACCOUNT_SID'):
                            from twilio.rest import Client
                            client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
                            to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                            await asyncio.to_thread(client.messages.create, body=err_msg, from_=os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034'), to=to_formatted)
                        return
                await confirm_and_queue_to_ledger(unconfirmed["id"])
                success_msg = "✅ All set! I've officially locked this into your tax ledger and it's queued for HMRC."
                logger.info("Outbound WhatsApp message", sender_id=sender_id, message=success_msg)
                from ws import manager
                await manager.send_personal_message({"type": "INTAKE_UPDATE", "chat_id": chat_id, "result": {"status": "CONFIRMED"}}, sender_id)
                
                if not sender_id.startswith("demo_web_") and os.environ.get('TWILIO_ACCOUNT_SID'):
                    from twilio.rest import Client
                    client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
                    to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                    await asyncio.to_thread(client.messages.create, body=success_msg, from_=os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034'), to=to_formatted)
                return
            else:
                err_msg = "You don't have any pending expenses to proceed with."
                logger.info("Outbound WhatsApp message", sender_id=sender_id, message=err_msg)
                if not sender_id.startswith("demo_web_") and os.environ.get('TWILIO_ACCOUNT_SID'):
                    from twilio.rest import Client
                    client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
                    to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                    await asyncio.to_thread(client.messages.create, body=err_msg, from_=os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034'), to=to_formatted)
                return

        
        dynamic_enums = None
        identity = await get_identity_from_vault(sender_id)
        if identity:
            try:
                accounts = await universal_adapter.get_accounts(TargetSystem.XERO, identity)
                tax_rates = await universal_adapter.get_tax_rates(TargetSystem.XERO, identity)
                dynamic_enums = {"accounts": accounts, "tax_rates": tax_rates}
            except Exception as e:
                logger.error("Failed to fetch dynamic enums", error=str(e))
                
        result = await process_expense_message(message, turn_count, media_urls, sender_id=sender_id, dynamic_enums=dynamic_enums)


        if result:
            # Anti-Hallucination Pipeline
            verification = await verify_expense_hallucination(message, result, sender_id=sender_id, media_urls=media_urls)
            if verification.get("is_hallucinated"):
                result["is_ambiguous"] = True
                result["auditor_question"] = verification.get("corrected_question", "I got confused. Could you repeat the amount and vendor?")

            # Anti-Junk Guard
            gross_amount = result.get("gross_amount")
            net_amount = result.get("net_amount")
            line_items_sum = sum(safe_float(item.get("unit_amount") or item.get("net_amount") or item.get("amount") or 0.0) for item in result.get("line_items", []))
            has_amount = (gross_amount is not None and safe_float(gross_amount) != 0.0) or (net_amount is not None and safe_float(net_amount) != 0.0) or line_items_sum != 0.0
            if not has_amount and not result.get("is_ambiguous"):
                result["is_ambiguous"] = True
                result["auditor_question"] = "I couldn't detect an expense amount. Could you clarify the amount?"
            
            # Staging Gate
            await stage_expense(chat_id, result)
            
            # Broadcast the update via WebSocket
            from ws import manager
            await manager.send_personal_message({"type": "INTAKE_UPDATE", "chat_id": chat_id, "result": result}, sender_id)

            if result.get("is_ambiguous"):
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message=result["auditor_question"],
                )
                from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034')
                if not sender_id.startswith("demo_web_") and os.environ.get('TWILIO_ACCOUNT_SID'):
                    from twilio.rest import Client
                    client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
                    to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                    await asyncio.to_thread(client.messages.create, body=result["auditor_question"], from_=from_number, to=to_formatted)
            else:
                amount_val = result.get('gross_amount') or result.get('net_amount') or 0.0
                amount_formatted = f"£{amount_val:.2f}"
                vendor = result.get('vendor', 'Unknown Vendor')
                category = result.get('line_items', [{}])[0].get('description', 'expense') if result.get('line_items') else 'expense'
                layman_msg = f"I've noted down {amount_formatted} spent at {vendor} for {category}. Does this look right? Reply 'proceed' to lock this into your tax ledger, or just tell me what to change."
                logger.info(
                    "Outbound WhatsApp message",
                    sender_id=sender_id,
                    message=layman_msg,
                )
                from_number = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034')
                if not sender_id.startswith("demo_web_") and os.environ.get('TWILIO_ACCOUNT_SID'):
                    from twilio.rest import Client
                    client = Client(os.environ.get('TWILIO_ACCOUNT_SID'), os.environ.get('TWILIO_AUTH_TOKEN'))
                    to_formatted = f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                    await asyncio.to_thread(client.messages.create, body=layman_msg, from_=from_number, to=to_formatted)

    except Exception as e:
        logger.error("Error processing intake", chat_id=chat_id, error=str(e))
        from ws import manager
        await manager.send_personal_message({"type": "INTAKE_UPDATE", "chat_id": chat_id, "result": {"is_ambiguous": True, "auditor_question": "An internal error occurred."}}, sender_id)
        if not sender_id.startswith("demo_web_"):
            try:
                from twilio.rest import Client
                account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
                if account_sid and auth_token:
                    client = Client(account_sid, auth_token)
                    await asyncio.to_thread(
                        client.messages.create,
                        body="I'm sorry, my systems are currently experiencing an internal error. Please try again later.",
                        from_='whatsapp:+14155238886', # Typical Twilio sandbox number; update in prod
                        to=f"whatsapp:{sender_id}" if not sender_id.startswith("whatsapp:") else sender_id
                    )
            except Exception as twilio_err:
                logger.error("Failed to send Twilio error fallback", error=str(twilio_err))


from security import mask_pii, verify_whatsapp_signature, encrypt_token, verify_api_key

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable is missing.")



# We are using a persistent DB queue instead of an in-memory queue.
async def intake_worker():
    """Consumes incoming WhatsApp messages from the DB queue."""
    from db import pop_intake_queue, mark_intake_done
    while True:
        try:
            task = await pop_intake_queue()
            if not task:
                await asyncio.sleep(1)
                continue
            try:
                # task keys: chat_id, sender_id, message, turn_count, media_urls
                media = json.loads(task.get("media_urls", "[]")) if isinstance(task.get("media_urls"), str) else task.get("media_urls", [])
                await process_intake_task(
                    task["chat_id"], task["sender_id"], task["message"], task["turn_count"], media
                )
            finally:
                await mark_intake_done(task["id"])
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Queue worker error", error=str(e))
            await asyncio.sleep(1)


import db

async def sweep_loop():
    while True:
        try:
            await db.sweep_orphaned_processing()
        except Exception as e:
            logger.error("Error in sweep_orphaned_processing loop", error=str(e))
        await asyncio.sleep(300)

db.sweep_loop = sweep_loop

@app.on_event("startup")
async def startup_event():
    await init_db()
    
    sweeper_loop_task = asyncio.create_task(db.sweep_loop())
    _background_tasks.add(sweeper_loop_task)
    
    # Spawn 5 dedicated AI workers for the persistent Waiting Room
    for _ in range(5):
        worker = asyncio.create_task(intake_worker())
        _background_tasks.add(worker)
        
    # Re-enable the HMRC submission queue and TTL sweeper
    hmrc_semaphore = asyncio.Semaphore(10)
    hmrc_worker = asyncio.create_task(process_hmrc_queue(hmrc_semaphore))
    _background_tasks.add(hmrc_worker)
    
    ttl_worker = asyncio.create_task(process_ttl_sweeper())
    _background_tasks.add(ttl_worker)


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
    MediaUrl0: str = Form(None),
):
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(os.environ.get("TWILIO_AUTH_TOKEN", ""))
        
        # Render proxies might change the scheme, ensure it matches Twilio's expected URL
        url = str(request.url).replace("http://", "https://")
        signature = request.headers.get("X-Twilio-Signature", "")
        form_data = await request.form()
        
        # Validate HMAC signature
        if not validator.validate(url, form_data, signature):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
            
        sender_id = From.replace("whatsapp:", "")
        masked_message = mask_pii(Body)
        
        from db import get_unconfirmed_session
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
                        
                        def upload_to_s3():
                            s3_client = boto3.client('s3')
                            s3_client.put_object(Bucket=bucket_name, Key=key, Body=resp.content, ContentType=ct)
                            
                        await asyncio.to_thread(upload_to_s3)
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
        )
        
        # Return empty TwiML immediately so Twilio knows we received it
        from fastapi.responses import Response
        return Response(content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>', media_type="application/xml")
    except ValueError as e:
        from fastapi.responses import Response
        return Response(
            content=f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{str(e)}</Message></Response>',
            media_type="application/xml"
        )

@app.post("/webhook/whatsapp")
async def receive_whatsapp(
    payload: WhatsAppPayload,
    request: Request,
    background_tasks: BackgroundTasks,
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

    # Process the message in the background
    background_tasks.add_task(
        process_intake_task,
        chat_id,
        payload.sender_id,
        llm_message,
        payload.turn_count,
        payload.media_urls or []
    )

    return {
        "status": "success",
        "chat_id": chat_id,
        "message": "Payload received and processing in the background.",
    }




@app.get("/queue", dependencies=[Depends(verify_api_key)])
async def view_hmrc_queue(limit: int = 100, offset: int = 0):
    return {"queue": await get_all_hmrc_queue(limit=limit, offset=offset)}

@app.get("/api/queue")
async def view_hmrc_queue_bff(limit: int = 100, offset: int = 0):
    # BFF route for the frontend dashboard. In a real app, we'd check session cookies.
    return {"queue": await get_all_hmrc_queue(limit=limit, offset=offset)}


@app.get("/expense/{chat_id}", dependencies=[Depends(verify_api_key)])
async def get_expense_status(chat_id: int):
    record = await get_hmrc_ledger_by_chat(chat_id)
    if not record:
        raise HTTPException(status_code=404, detail="Not processed yet")
    return record


from ws import manager
from fastapi import WebSocket, WebSocketDisconnect

import asyncio

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    async def heartbeat():
        try:
            while True:
                await asyncio.sleep(15)
                await websocket.send_json({"type": "PING"})
        except Exception as e:
            logger.error("Heartbeat exception", error=str(e))

    hb_task = asyncio.create_task(heartbeat())
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        logger.error("WebSocket receive exception", error=str(e))
    finally:
        hb_task.cancel()
        manager.disconnect(websocket, client_id)

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

    from db import push_intake_queue
    await push_intake_queue(
        chat_id,
        payload.sender_id,
        llm_message,
        payload.media_urls or [],
        payload.turn_count
    )

    return {
        "status": "success",
        "chat_id": chat_id,
        "message": "Payload received and queued in the waiting room.",
    }

from db import create_oauth_state, consume_oauth_state

import hashlib
@app.get("/auth")
async def auth(whatsapp_id: str, response: Response):
    client_id = os.environ.get("XERO_CLIENT_ID", "mock_client_id")
    redirect_uri = os.environ.get("XERO_REDIRECT_URI", "https://invisibleaccountant.co.uk/callback")
    base_url = os.environ.get("XERO_BASE_URL", "https://login.xero.com/identity")
    
    nonce = secrets.token_urlsafe(32)
    nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
    
    state_uuid = await create_oauth_state(whatsapp_id, nonce_hash)
    url = f"{base_url}/connect/authorize?response_type=code&client_id={client_id}&scope=offline_access accounting.invoices accounting.attachments accounting.contacts app.connections&state={state_uuid}&redirect_uri={redirect_uri}"
    
    res = RedirectResponse(url)
    res.set_cookie(key="oauth_nonce", value=nonce, httponly=True, secure=True, samesite="lax")
    return res

@app.get("/callback")
async def callback(request: Request, code: str, state: str):
    state_data = await consume_oauth_state(state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
    nonce = request.cookies.get("oauth_nonce")
    if not nonce:
        raise HTTPException(status_code=400, detail="Missing OAuth nonce cookie")
        
    expected_hash = state_data.get("nonce_hash")
    actual_hash = hashlib.sha256(nonce.encode()).hexdigest()
    
    if not expected_hash or not secrets.compare_digest(expected_hash, actual_hash):
        raise HTTPException(status_code=403, detail="CSRF token mismatch. Session fixation attempt prevented.")
        
    whatsapp_id = state_data["whatsapp_id"]
        
    client_id = os.environ.get("XERO_CLIENT_ID")
    client_secret = os.environ.get("XERO_CLIENT_SECRET")
    redirect_uri = os.environ.get("XERO_REDIRECT_URI", "https://invisibleaccountant.co.uk/callback")
    base_url = os.environ.get("XERO_BASE_URL", "https://identity.xero.com")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{base_url}/connect/token",
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
        
        connections_resp = await client.get(
            "https://api.xero.com/connections",
            headers={
                "Authorization": f"Bearer {token_data['access_token']}",
                "Accept": "application/json"
            }
        )
        if connections_resp.status_code == 200:
            connections = connections_resp.json()
            if not connections:
                raise HTTPException(status_code=400, detail="No Xero tenants connected")
            token_data["xero_tenant_id"] = connections[0]["tenantId"]
    # Store the tokens in the new accounting_connections table
    from db import store_accounting_connection
    from aes_gcm_security import TokenEncryptionEngine
    master_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
    if master_key:
        engine = TokenEncryptionEngine(master_key)
        enc_access = engine.encrypt_tokens(token_data["access_token"], associated_data=whatsapp_id)
        enc_refresh = engine.encrypt_tokens(token_data["refresh_token"], associated_data=whatsapp_id)
        access_token_store = json.dumps(enc_access)
        refresh_token_store = json.dumps(enc_refresh)
    else:
        access_token_store = token_data["access_token"]
        refresh_token_store = token_data["refresh_token"]

    await store_accounting_connection(
        workspace_id=whatsapp_id,
        provider="XERO",
        provider_tenant_id=token_data.get("xero_tenant_id", ""),
        access_token=access_token_store,
        refresh_token=refresh_token_store,
        expires_in_seconds=token_data.get("expires_in", 1800)
    )
    
    return HTMLResponse("<h1>Success! Your identity has been securely vaulted. You can return to WhatsApp.</h1>")

# Serve the landing page at the root URL
@app.get("/")
async def serve_landing_page():
    from fastapi.responses import FileResponse
    return FileResponse("landing_page.html")

@app.post("/admin/review/{item_id}/approve", dependencies=[Depends(verify_api_key)])
async def approve_review_item(item_id: int):
    from db import get_connection
    async with get_connection() as conn:
        result = await conn.execute("UPDATE hmrc_ledger SET status = 'PENDING', accountant_approved = TRUE WHERE id = $1 AND status = 'NEEDS_REVIEW'", item_id)
        if result == "UPDATE 0":
            raise HTTPException(status_code=404, detail="Item not found or not in NEEDS_REVIEW status.")
        return {"status": "success", "message": "Item approved and queued for processing"}

@app.get("/admin/dashboard", response_class=HTMLResponse, dependencies=[Depends(verify_api_key)])
async def admin_dashboard():
    from db import get_connection
    from aes_gcm_security import TokenEncryptionEngine
    master_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
    token_engine = TokenEncryptionEngine(master_key) if master_key else None
    
    async with get_connection() as conn:
        intake_rows = await conn.fetch("SELECT * FROM intake_queue ORDER BY timestamp DESC LIMIT 50")
        ledger_rows = await conn.fetch("SELECT * FROM hmrc_ledger ORDER BY timestamp DESC LIMIT 50")
    
    log_lines = []
    try:
        if os.path.exists("invisible_accountant.log"):
            with open("invisible_accountant.log", "r", encoding="utf-8") as f:
                log_lines = f.readlines()[-20:]
        else:
            log_lines = ["No log file found."]
    except Exception as e:
        log_lines = [f"Error reading logs: {e}"]

    def status_badge(status):
        status = status.upper() if status else "UNKNOWN"
        if status in ("DONE", "SUBMITTED", "CONFIRMED"):
            return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{status}</span>'
        elif status in ("FAILED", "AUTH_EXPIRED", "ERROR"):
            return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">{status}</span>'
        else:
            return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">{status}</span>'

    html = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        "<title>Glass Ledger Admin Dashboard</title>",
        '<script src="https://cdn.tailwindcss.com"></script>',
        "</head>",
        '<body class="bg-gray-50 text-gray-900 font-sans p-8">',
        '<div class="max-w-7xl mx-auto space-y-8">',
        '<header class="mb-8 border-b pb-4">',
        '<h1 class="text-3xl font-bold text-gray-900">The Glass Ledger</h1>',
        '<p class="text-sm text-gray-500 mt-1">Enterprise Monitoring & Compliance Dashboard</p>',
        '</header>'
    ]
    
    html.append('<section class="bg-white rounded-lg shadow p-6">')
    html.append('<h2 class="text-xl font-semibold mb-4 text-gray-800">System Alerts & Errors</h2>')
    html.append('<div class="bg-gray-900 rounded p-4 overflow-x-auto">')
    html.append('<pre><code class="text-xs text-green-400 font-mono">')
    import html as ht
    for line in log_lines:
        html.append(ht.escape(line.strip()) + "\\n")
    html.append('</code></pre></div></section>')

    html.append('<section class="bg-white rounded-lg shadow overflow-hidden">')
    html.append('<div class="px-6 py-4 border-b border-gray-200"><h2 class="text-xl font-semibold text-gray-800">Intake Queue</h2></div>')
    html.append('<div class="overflow-x-auto"><table class="min-w-full divide-y divide-gray-200">')
    html.append('<thead class="bg-gray-50"><tr><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chat ID</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sender</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th></tr></thead>')
    html.append('<tbody class="bg-white divide-y divide-gray-200">')
    
    for row in intake_rows:
        html.append(f"<tr><td class='px-6 py-4 whitespace-nowrap text-sm text-gray-900'>{row['id']}</td>")
        html.append(f"<td class='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>{row['chat_id']}</td>")
        html.append(f"<td class='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>{row['timestamp']}</td>")
        html.append(f"<td class='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>{row['sender_id']}</td>")
        html.append(f"<td class='px-6 py-4 whitespace-nowrap'>{status_badge(row['status'])}</td></tr>")
    html.append("</tbody></table></div></section>")

    html.append('<section class="bg-white rounded-lg shadow overflow-hidden">')
    html.append('<div class="px-6 py-4 border-b border-gray-200"><h2 class="text-xl font-semibold text-gray-800">HMRC Ledger</h2></div>')
    html.append('<div class="overflow-x-auto"><table class="min-w-full divide-y divide-gray-200">')
    html.append('<thead class="bg-gray-50"><tr><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Raw AI JSON</th><th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mapped Xero JSON</th></tr></thead>')
    html.append('<tbody class="bg-white divide-y divide-gray-200">')
    
    for row in ledger_rows:
        raw_json = "{}"
        mapped_json = "{}"
        
        if row["encrypted_financial_data"] and token_engine:
            try:
                enc_dict = json.loads(row["encrypted_financial_data"])
                decrypted_json = token_engine.decrypt_tokens(enc_dict, associated_data=str(row["chat_id"]))
                fin_data = json.loads(decrypted_json)
                raw_json = json.dumps(fin_data, indent=2)
                
                amount = safe_float(fin_data.get("gross_amount") or fin_data.get("amount", 0.0))
                mapped_json = json.dumps({
                    "amount": amount,
                    "category": row.get("category", "Other business expenses"),
                    "timestamp": row["timestamp"],
                    "target_system": "XERO",
                    "sender_id": "unknown_whatsapp_user",
                    "extra_data": {"id": row["id"], **fin_data}
                }, indent=2)
            except Exception as e:
                raw_json = f"Error: {e}"
                
        html.append(f"<tr><td class='px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>{row['id']}</td>")
        html.append(f"<td class='px-6 py-4 whitespace-nowrap'>{status_badge(row['status'])}</td>")
        html.append(f"<td class='px-6 py-4 text-sm text-gray-500'><div class='bg-gray-50 rounded p-2 overflow-x-auto max-w-md'><pre><code class='text-xs'>{ht.escape(raw_json)}</code></pre></div></td>")
        html.append(f"<td class='px-6 py-4 text-sm text-gray-500'><div class='bg-gray-50 rounded p-2 overflow-x-auto max-w-md'><pre><code class='text-xs'>{ht.escape(mapped_json)}</code></pre></div></td></tr>")
        
    html.append("</tbody></table></div></section>")
    html.append("</div></body></html>")
    return "".join(html)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
from fastapi.responses import HTMLResponse
import os

@app.get("/privacy", response_class=HTMLResponse)
async def privacy_policy():
    with open(os.path.join("templates", "privacy.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/accessibility", response_class=HTMLResponse)
async def serve_accessibility():
    with open(os.path.join("templates", "accessibility.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/terms", response_class=HTMLResponse)
async def terms_and_conditions():
    with open(os.path.join("templates", "terms.html"), "r", encoding="utf-8") as f:
        return f.read()
