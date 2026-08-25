from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
import uuid

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
    media_urls: Optional[List[str]] = None
    turn_count: int = Field(default=1, description="Number of conversational turns so far")

@app.on_event("startup")
async def startup_event():
    init_db()
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

def process_intake_task(sender_id: str, message: str, media_urls: List[str], turn_count: int):
    # This runs asynchronously after responding to WhatsApp
    intake_id = log_intake(sender_id, message, media_urls, turn_count)
    result = process_expense_message(message, turn_count)
    
    if result:
        queue_expense(
            intake_id=intake_id,
            vendor=result.get("vendor", "Unknown"),
            amount=result.get("amount", 0.0),
            category=result.get("category", "Other expenses"),
            is_ambiguous=result.get("is_ambiguous", False),
            auditor_question=result.get("auditor_question", "")
        )

@app.post("/webhook/whatsapp")
async def receive_whatsapp(payload: WhatsAppPayload, background_tasks: BackgroundTasks):
    # Offload the heavy LLM parsing and queueing to a background task instantly
    background_tasks.add_task(
        process_intake_task, 
        payload.sender_id, 
        payload.message, 
        payload.media_urls,
        payload.turn_count
    )
    
    # Return 200 OK immediately to satisfy WhatsApp's latency requirements
    return {
        "status": "success",
        "message": "Payload received. Processing in background."
    }

@app.get("/queue")
async def view_hmrc_queue():
    return {"queue": get_all_hmrc_queue()}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

