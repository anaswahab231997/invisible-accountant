import asyncio
import time
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from db import (
    get_connection,
    
    get_pending_hmrc_queue,
    mark_hmrc_submitted,
    get_identity_from_vault,
    store_identity_in_vault
)
from logger import get_logger
from hmrc_api import HMRCClient, HMRCApiError, generate_whatsapp_fraud_headers
from aes_gcm_security import TokenEncryptionEngine

logger = get_logger(__name__)

# Initialize Token Encryption Engine
encryption_key = os.getenv("DB_ENCRYPTION_KEY_B64")
if not encryption_key:
    raise ValueError("DB_ENCRYPTION_KEY_B64 environment variable is missing in worker.py.")
    
token_engine = TokenEncryptionEngine(encryption_key)

class OAuthManager:
    def __init__(self):
        self.client_id = os.getenv("HMRC_CLIENT_ID")
        self.client_secret = os.getenv("HMRC_CLIENT_SECRET")
        self.base_url = os.getenv("HMRC_BASE_URL", "https://test-api.service.hmrc.gov.uk")

    async def get_user_identity(self, whatsapp_id: str):
        encrypted_blob = await get_identity_from_vault(whatsapp_id)
        if not encrypted_blob:
            raise Exception("No identity found in secure vault for this user.")
            
        encrypted_payload = json.loads(encrypted_blob.decode("utf-8"))
        decrypted_json = token_engine.decrypt_tokens(
            encrypted_payload, 
            associated_data=f"hmrc_identity_{whatsapp_id}"
        )
        identity = json.loads(decrypted_json)
        
        # Check expiry with a 60-second buffer for network latency
        if time.time() + 60 > identity.get("expires_at", 0):
            logger.info("Access token expired. Refreshing token via HMRC...", whatsapp_id=whatsapp_id)
            identity = await self.refresh_user_token(whatsapp_id, identity)
            
        return identity

    async def refresh_user_token(self, whatsapp_id: str, identity: dict):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": identity.get("refresh_token")
                }
            )
            
            if resp.status_code != 200:
                logger.error("Token refresh failed. User must re-authenticate via Gov Gateway.", status=resp.status_code)
                raise Exception("OAuth 18-month grant expired or refresh token invalid.")
                
            token_data = resp.json()
            identity["access_token"] = token_data["access_token"]
            identity["refresh_token"] = token_data.get("refresh_token", identity["refresh_token"])
            identity["expires_at"] = time.time() + token_data.get("expires_in", 14400)
            
            # Re-encrypt and store
            encrypted_blob = token_engine.encrypt_tokens(
                plaintext=json.dumps(identity),
                associated_data=f"hmrc_identity_{whatsapp_id}"
            )
            await store_identity_in_vault(whatsapp_id, encrypted_blob)
            
            return identity

# Token Bucket Rate Limiter for 2.5 requests per second
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = None

    async def consume(self):
        if self.lock is None:
            self.lock = asyncio.Lock()
            
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_refill = time.time()
            else:
                self.tokens -= 1


hmrc_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=15)
oauth_manager = OAuthManager()
rate_limiter = TokenBucket(rate=2.5, capacity=5)


async def submit_to_hmrc(item, identity):
    sender_id = item.get("sender_id", "unknown_whatsapp_user")
    # We pass None for device ID since we don't capture the physical device on WhatsApp.
    fraud_headers = generate_whatsapp_fraud_headers(real_device_id=None)
    
    # Initialize HMRCClient with the user's specific access token
    client = HMRCClient(access_token=identity["access_token"], fraud_headers=fraud_headers)
    
    # Safely pull the user's NINO from their decrypted vault identity
    nino = identity.get("nino")
    
    if not nino:
        logger.error("NINO missing from decrypted identity vault", queue_id=item["id"])
        raise Exception("Missing NINO for submission")
        
    year = item["timestamp"][:4]
    from_date = f"{year}-04-06"
    to_date = f"{int(year)+1}-04-05"
    
    try:
        # 1. Fetch Business Details to get incomeSourceId
        logger.info("Fetching Business Details", queue_id=item["id"])
        business_details = await client.get_business_details(nino)
        
        businesses = business_details.get("businessData", [])
        if not businesses:
            raise Exception("No self-employment business found for user.")
            
        income_source_id = businesses[0].get("incomeSourceId")
        
        # 2. Fetch Obligations to get exact periodDates
        logger.info("Fetching Obligations", queue_id=item["id"])
        obligations_resp = await client.get_obligations(nino, from_date, to_date)
        
        obligations = obligations_resp.get("obligations", [])
        if not obligations:
            raise Exception("No obligations found for the specified period.")
            
        details = obligations[0].get("obligationDetails", [])
        open_obs = [ob for ob in details if ob.get("status") == "O"]
        
        if not open_obs:
            raise Exception("No OPEN obligations found to submit against.")
            
        period_start = open_obs[0].get("inboundCorrespondenceFromDate")
        period_end = open_obs[0].get("inboundCorrespondenceToDate")
        
        # 3. Submit periodic update using the dynamic metadata
        logger.info("Submitting Periodic Update", income_source_id=income_source_id, period_start=period_start, period_end=period_end)
        await client.submit_periodic_update(
            nino=nino,
            income_source_id=income_source_id,
            amount=item["amount"],
            period_start=period_start,
            period_end=period_end
        )
        await mark_hmrc_submitted(item["id"])
    except HMRCApiError as e:
        # Sanitize PII from the payload before logging
        def sanitize_pii(data):
            if isinstance(data, dict):
                return {k: sanitize_pii(v) for k, v in data.items() if k.lower() not in ['nino', 'utr', 'password', 'name', 'address', 'vrn']}
            elif isinstance(data, list):
                return [sanitize_pii(v) for v in data]
            return data
            
        safe_payload = sanitize_pii(e.payload)
        logger.error("HMRC API Error", queue_id=item["id"], status=e.status_code, payload=safe_payload)
        raise e
    except Exception as e:
        logger.error("Unknown HMRC Error", queue_id=item["id"], error=str(e))
        raise e


async def process_hmrc_queue():
    while True:
        try:
            pending_items = await get_pending_hmrc_queue()

            for item in pending_items:
                try:
                    await rate_limiter.consume()
                    
                    # Fetch identity from the secure vault, refreshing the token if necessary
                    identity = await oauth_manager.get_user_identity(item["sender_id"])
                    
                    logger.info("Submitting Queue ID to HMRC API", queue_id=item["id"])
                    await hmrc_breaker.async_call(submit_to_hmrc, item, identity)
                    logger.info("Queue ID successfully submitted", queue_id=item["id"])
                except CircuitBreakerOpenException:
                    logger.warning(
                        "Circuit is OPEN. Pausing queue processing",
                        recovery_timeout=hmrc_breaker.recovery_timeout,
                    )
                    await asyncio.sleep(hmrc_breaker.recovery_timeout)
                    break  # Break out of the batch loop to retry later
                except Exception as e:
                    logger.error("Queue item failed", queue_id=item["id"], error=str(e))
                    from db import mark_hmrc_failed
                    await mark_hmrc_failed(item["id"])

            await asyncio.sleep(1)  # idle wait if queue is empty
        except Exception as e:
            logger.critical("Worker critical error", error=str(e), retry_in="5s")
            await asyncio.sleep(5)


async def process_ttl_sweeper():
    while True:
        try:
            from db import get_expiring_staged_sessions
            expiring = await get_expiring_staged_sessions()
            if expiring:
                async with get_connection() as conn:
                    for item in expiring:
                        logger.warning(
                            "ALERT: Chat Session ID is nearing the 24h WhatsApp policy limit!",
                            chat_id=item["id"],
                        )
                        logger.info(
                            "Triggering batch template message for missing data",
                            sender_id=item["sender_id"],
                        )
                        await conn.execute(
                            "UPDATE chat_sessions SET ttl_timestamp = '9999-12-31' WHERE id = $1",
                            item["id"]
                        )

            await asyncio.sleep(5)
        except Exception as e:
            logger.error("Sweeper error", error=str(e), retry_in="5s")
            await asyncio.sleep(5)


async def start_workers():
    logger.info("Starting background async workers...")
    await asyncio.gather(process_hmrc_queue(), process_ttl_sweeper())


if __name__ == "__main__":
    asyncio.run(start_workers())
