from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Depends, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
import asyncio
import uuid
import hmac
import hashlib

from db import init_db, log_intake, queue_expense, get_pending_hmrc_queue, get_all_hmrc_queue
from agents import process_expense_message
from worker import process_hmrc_queue, process_ttl_sweeper

app = FastAPI(title="Invisible Accountant Webhook Prototype (V2 Enterprise)")

# Serve the frontend simulator
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")

class WhatsAppPayload(BaseModel):
    sender_id: str
    message: str = Field(..., max_length=1000)
    media_urls: Optional[List[HttpUrl]] = None
    turn_count: int = Field(default=1, description="Number of conversational turns so far")

@app.on_event("startup")
async def startup_event():
    await init_db()
    # Start the async workers in the background
    asyncio.create_task(process_hmrc_queue())
    asyncio.create_task(process_ttl_sweeper())

@app.get("/generate_presigned_url")
async def get_presigned_url():
    """
    Simulates generating an S3 presigned URL to offload media uploads
    from the main webhook server to prevent memory pressure.
    """
    mock_upload_id = str(uuid.uuid4())
    return {
        "upload_url": f"https://mock-s3-bucket.amazonaws.com/uploads/{mock_upload_id}?AWSAccessKeyId=MOCK&Signature=MOCK",
        "expires_in": 3600
    }

async def process_intake_task(sender_id: str, message: str, media_urls: List[HttpUrl], turn_count: int):
    # This runs asynchronously after responding to WhatsApp
    # Convert HttpUrl to str for DB and downstream tasks
    media_urls_str = [str(url) for url in media_urls] if media_urls else []
    intake_id = await log_intake(sender_id, message, media_urls_str, turn_count)
    result = process_expense_message(message, turn_count)
    
    if result:
        await queue_expense(
            intake_id=intake_id,
            vendor=result.get("vendor", "Unknown"),
            amount=result.get("amount", 0.0),
            category=result.get("category", "Other expenses"),
            is_ambiguous=result.get("is_ambiguous", False),
            auditor_question=result.get("auditor_question", "")
        )

WEBHOOK_SECRET = "dummy_secret"

@app.post("/webhook/whatsapp")
async def receive_whatsapp(
    payload: WhatsAppPayload, 
    background_tasks: BackgroundTasks,
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature")
        
    raw_body = await request.body()
    expected_sig = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(x_hub_signature_256, expected_sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Offload the heavy LLM parsing and queueing to a background task instantly
    background_tasks.add_task(
        process_intake_task, 
        payload.sender_id, 
        payload.message, 
        payload.media_urls or [],
        payload.turn_count
    )
    
    # Return 200 OK immediately to satisfy WhatsApp's latency requirements
    return {
        "status": "success",
        "message": "Payload received. Processing in background."
    }

API_KEY = "super-secret-key"

def verify_api_key(api_key: str = Query(None)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.get("/queue", dependencies=[Depends(verify_api_key)])
async def view_hmrc_queue():
    return {"queue": await get_all_hmrc_queue()}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

