import os
import json
import httpx
import asyncio
import time
import random
import hashlib
import io
import re
from datetime import datetime, timezone
import asyncpg
from db import get_connection
from aes_gcm_security import TokenEncryptionEngine

class XeroTenantRateLimiter:
    """
    In-process rate limiter per Xero Tenant ID.
    Enforces:
    - Max 4 concurrent in-flight requests (Xero API limit is 5).
    - Token bucket of 55 requests / 60 seconds (Xero API limit is 60).
    - Exponential backoff with decorrelated jitter on HTTP 429.
    """
    _instances: dict[str, "XeroTenantRateLimiter"] = {}
    _global_lock = asyncio.Lock()

    @classmethod
    async def get_limiter(cls, tenant_id: str) -> "XeroTenantRateLimiter":
        async with cls._global_lock:
            if tenant_id not in cls._instances:
                cls._instances[tenant_id] = XeroTenantRateLimiter(tenant_id)
            return cls._instances[tenant_id]

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.semaphore = asyncio.Semaphore(4)  # Ceiling of 4 concurrent calls (Xero enforces 5)
        self.capacity = 55.0  # Safe ceiling under Xero's 60 calls/minute limit
        self.tokens = 55.0
        self.fill_rate = 55.0 / 60.0  # tokens per second
        self.last_update = time.monotonic()
        self.bucket_lock = asyncio.Lock()

    async def acquire_token(self):
        """Acquires a token from the bucket, waiting if the bucket is exhausted."""
        while True:
            async with self.bucket_lock:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(self.capacity, self.tokens + (elapsed * self.fill_rate))
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait_time = (1.0 - self.tokens) / self.fill_rate
            await asyncio.sleep(min(max(wait_time, 0.05), 2.0))

    async def execute(self, request_coro_func):
        """
        Executes an HTTP request wrapped in concurrency semaphore and rate-limiting bucket.
        Handles HTTP 429 retry with adaptive jitter and Retry-After inspection.
        """
        max_retries = 3
        attempt = 0
        while attempt <= max_retries:
            await self.acquire_token()
            async with self.semaphore:
                try:
                    resp = await request_coro_func()
                    if resp.status_code == 429:
                        attempt += 1
                        if attempt > max_retries:
                            return resp
                        problem = resp.headers.get("X-Rate-Limit-Problem", "").lower()
                        retry_after_hdr = resp.headers.get("Retry-After")
                        if "concurrent" in problem:
                            # Concurrent limit exceeded: fast jitter backoff (150ms - 500ms)
                            sleep_duration = random.uniform(0.15, 0.50) * (2 ** (attempt - 1))
                        elif retry_after_hdr and retry_after_hdr.isdigit():
                            sleep_duration = float(retry_after_hdr) + random.uniform(0.5, 1.5)
                        elif "minute" in problem:
                            sleep_duration = 5.0 + random.uniform(1.0, 3.0)
                        else:
                            sleep_duration = (2 ** attempt) + random.uniform(0.1, 0.5)
                        await asyncio.sleep(sleep_duration)
                        continue
                    return resp
                except httpx.RequestError as net_err:
                    attempt += 1
                    if attempt > max_retries:
                        raise net_err
                    await asyncio.sleep((1.5 ** attempt) + random.uniform(0.1, 0.4))


def inspect_and_validate_attachment(file_bytes: bytes, filename: str) -> tuple[str, str, str, bytes]:
    """
    Validates file bytes for HMRC/Xero compliance:
    1. Size ceiling <= 10MB (10,485,760 bytes) and > 0 bytes.
    2. Magic-byte MIME detection (JPEG, PNG, PDF, GIF, TIFF).
    3. Computes cryptographic SHA-256 hash.
    4. Sanitizes filename with appropriate extension.
    Returns: (sanitized_filename, mime_type, sha256_hash, validated_bytes)
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Attachment validation failed: Empty (0-byte) payload.")
    
    max_bytes = 10 * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise ValueError(f"Attachment validation failed: File size ({len(file_bytes)} bytes) exceeds Xero 10MB ceiling.")

    # Magic byte identification
    detected_mime = None
    detected_ext = None

    if file_bytes.startswith(b"\xFF\xD8\xFF"):
        detected_mime = "image/jpeg"
        detected_ext = "jpg"
    elif file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
        detected_ext = "png"
    elif file_bytes.startswith(b"%PDF-"):
        detected_mime = "application/pdf"
        detected_ext = "pdf"
    elif file_bytes.startswith(b"GIF87a") or file_bytes.startswith(b"GIF89a"):
        detected_mime = "image/gif"
        detected_ext = "gif"
    elif file_bytes.startswith(b"II*\x00") or file_bytes.startswith(b"MM\x00*"):
        detected_mime = "image/tiff"
        detected_ext = "tiff"
    else:
        # Check if PIL can identify and transcode format to standard JPEG
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            if img.format in ("JPEG", "JPG"):
                detected_mime = "image/jpeg"
                detected_ext = "jpg"
            elif img.format == "PNG":
                detected_mime = "image/png"
                detected_ext = "png"
            else:
                rgb_img = img.convert("RGB")
                out_buf = io.BytesIO()
                rgb_img.save(out_buf, format="JPEG", quality=90)
                file_bytes = out_buf.getvalue()
                detected_mime = "image/jpeg"
                detected_ext = "jpg"
        except Exception:
            raise ValueError("Attachment validation failed: Unrecognized or corrupted file format. Only JPEG, PNG, and PDF are permitted.")

    sha256_hash = hashlib.sha256(file_bytes).hexdigest()

    # Sanitize filename
    clean_base = re.sub(r"[^a-zA-Z0-9_\-]", "_", os.path.splitext(filename)[0]).strip("_")
    if not clean_base:
        clean_base = f"receipt_{sha256_hash[:8]}"
    sanitized_filename = f"{clean_base[:50]}.{detected_ext}"

    return sanitized_filename, detected_mime, sha256_hash, file_bytes


class AccountingClient:
    def __init__(self, workspace_id: str, provider: str = "XERO"):
        self.workspace_id = workspace_id
        self.provider = provider
        self.master_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
        self.engine = TokenEncryptionEngine(self.master_key) if self.master_key else None

    def _decrypt(self, payload: str) -> str:
        if not self.engine or not payload.startswith("{"):
            return payload
        return self.engine.decrypt_tokens(json.loads(payload), associated_data=self.workspace_id)

    def _encrypt(self, payload: str) -> str:
        if not self.engine:
            return payload
        return json.dumps(self.engine.encrypt_tokens(payload, associated_data=self.workspace_id))

    async def get_valid_token(self) -> dict:
        """
        High-Concurrency Double-Checked Locking Token Engine (RFC 6749 §10.4 Compliant).
        1. Optimistic Fast-Path: Reads outside transaction without locks. If time_left >= 300s, returns immediately.
        2. Slow-Path: If expired/expiring, enters transaction with `FOR UPDATE` (no SKIP LOCKED).
        3. Double-Check: Re-checks expires_at under lock; if refreshed by a peer coroutine, reuses new token without calling Xero.
        4. Single Winner: Exactly one caller refreshes the token family with Xero and writes new credentials to DB.
        """
        # Step 1: Optimistic Fast-Path Read
        async with get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM accounting_connections 
                WHERE workspace_id = $1 AND provider = $2
                """,
                self.workspace_id, self.provider
            )
        
        if not row:
            raise Exception(f"No {self.provider} connection found for workspace {self.workspace_id}")

        expires_at = row["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        time_left = (expires_at - datetime.now(timezone.utc)).total_seconds()
        
        # If token has >= 5 minutes remaining, return immediately (fast path)
        if time_left >= 300:
            return {
                "access_token": self._decrypt(row["access_token"]),
                "tenant_id": row["provider_tenant_id"]
            }

        # Step 2: Slow-Path under Row-Level Exclusive Lock
        async with get_connection() as conn:
            async with conn.transaction():
                locked_row = await conn.fetchrow(
                    """
                    SELECT * FROM accounting_connections 
                    WHERE workspace_id = $1 AND provider = $2 
                    FOR UPDATE
                    """,
                    self.workspace_id, self.provider
                )
                if not locked_row:
                    raise Exception(f"No {self.provider} connection found for workspace {self.workspace_id}")

                # Step 3: Double-Check under lock
                locked_expires = locked_row["expires_at"]
                if locked_expires.tzinfo is None:
                    locked_expires = locked_expires.replace(tzinfo=timezone.utc)
                new_time_left = (locked_expires - datetime.now(timezone.utc)).total_seconds()

                if new_time_left >= 300:
                    # Token was already refreshed by a peer coroutine while we waited for lock
                    return {
                        "access_token": self._decrypt(locked_row["access_token"]),
                        "tenant_id": locked_row["provider_tenant_id"]
                    }

                # Step 4: We are the sole authorized worker to refresh with Xero
                refresh_token = self._decrypt(locked_row["refresh_token"])
                new_tokens = await self._refresh_xero_token(refresh_token)
                
                access_token = new_tokens["access_token"]
                new_refresh = new_tokens.get("refresh_token", refresh_token)
                expires_in = new_tokens.get("expires_in", 1800)
                
                await conn.execute(
                    """
                    UPDATE accounting_connections 
                    SET access_token = $1, refresh_token = $2, 
                        expires_at = NOW() + (INTERVAL '1 second' * $3), 
                        updated_at = NOW()
                    WHERE id = $4
                    """,
                    self._encrypt(access_token), 
                    self._encrypt(new_refresh),
                    expires_in,
                    locked_row["id"]
                )
                
                return {
                    "access_token": access_token,
                    "tenant_id": locked_row["provider_tenant_id"]
                }

    async def _refresh_xero_token(self, refresh_token: str) -> dict:
        client_id = os.getenv("XERO_CLIENT_ID")
        client_secret = os.getenv("XERO_CLIENT_SECRET")
        base_url = os.getenv("XERO_BASE_URL", "https://identity.xero.com")
        
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{base_url}/connect/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if resp.status_code != 200:
                raise Exception(f"Failed to refresh Xero token: {resp.text}")
            return resp.json()

    async def find_contact(self, name: str) -> dict | None:
        if not name or name.strip().lower() in ("unknown", "unknown supplier", "unknown vendor"):
            return None
        try:
            creds = await self.get_valid_token()
            clean_name = name.strip()
            tenant_id = creds["tenant_id"]
            limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)

            async def _make_request():
                async with httpx.AsyncClient(timeout=15.0) as client:
                    return await client.get(
                        "https://api.xero.com/api.xro/2.0/Contacts",
                        headers={
                            "Authorization": f"Bearer {creds['access_token']}",
                            "Xero-Tenant-Id": tenant_id,
                            "Accept": "application/json"
                        }
                    )

            resp = await limiter.execute(_make_request)
            if resp.status_code == 200:
                contacts = resp.json().get("Contacts", [])
                # Pass 1: exact match
                for c in contacts:
                    if c.get("Name", "").strip().lower() == clean_name.lower():
                        return {"Name": c["Name"], "ContactID": c["ContactID"]}
                # Pass 2: substring match
                for c in contacts:
                    c_name = c.get("Name", "").strip().lower()
                    if clean_name.lower() in c_name or c_name in clean_name.lower():
                        return {"Name": c["Name"], "ContactID": c["ContactID"]}
        except Exception:
            pass
        return None

    async def get_accounts(self) -> list:
        creds = await self.get_valid_token()
        tenant_id = creds["tenant_id"]
        limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)

        async def _make_request():
            async with httpx.AsyncClient(timeout=15.0) as client:
                return await client.get(
                    "https://api.xero.com/api.xro/2.0/Accounts",
                    headers={
                        "Authorization": f"Bearer {creds['access_token']}",
                        "Xero-Tenant-Id": tenant_id,
                        "Accept": "application/json"
                    }
                )

        resp = await limiter.execute(_make_request)
        if resp.status_code == 200:
            return resp.json().get("Accounts", [])
        return []

    async def get_tax_rates(self) -> list:
        creds = await self.get_valid_token()
        tenant_id = creds["tenant_id"]
        limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)

        async def _make_request():
            async with httpx.AsyncClient(timeout=15.0) as client:
                return await client.get(
                    "https://api.xero.com/api.xro/2.0/TaxRates",
                    headers={
                        "Authorization": f"Bearer {creds['access_token']}",
                        "Xero-Tenant-Id": tenant_id,
                        "Accept": "application/json"
                    }
                )

        resp = await limiter.execute(_make_request)
        if resp.status_code == 200:
            return resp.json().get("TaxRates", [])
        return []

    async def create_draft_bill(self, payload: dict) -> dict:
        creds = await self.get_valid_token()
        tenant_id = creds["tenant_id"]
        limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)
        headers = {
            "Authorization": f"Bearer {creds['access_token']}",
            "Xero-Tenant-Id": tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        async def _make_post_request(data):
            async with httpx.AsyncClient(timeout=25.0) as client:
                return await client.post(
                    "https://api.xero.com/api.xro/2.0/Invoices",
                    json=data,
                    headers=headers
                )

        resp = await limiter.execute(lambda: _make_post_request(payload))
        
        # Automatic fallback if TaxType INPUT2 / INPUT differs in tenant
        if resp.status_code == 400 and "TaxType code" in resp.text:
            modified = False
            fallback_payload = json.loads(json.dumps(payload))
            for line in fallback_payload.get("LineItems", []):
                if line.get("TaxType") == "INPUT2":
                    line["TaxType"] = "INPUT"
                    modified = True
                elif line.get("TaxType") == "INPUT":
                    line["TaxType"] = "INPUT2"
                    modified = True
            if modified:
                retry_resp = await limiter.execute(lambda: _make_post_request(fallback_payload))
                if retry_resp.status_code in (200, 201):
                    return retry_resp.json()
        
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to create draft bill (HTTP {resp.status_code}): {resp.text}")
        return resp.json()

    async def upload_attachment(self, invoice_id: str, filename: str, file_bytes: bytes, mime_type: str | None = None) -> dict:
        """
        Pre-flight validated, magic-byte authenticated receipt attachment uploader.
        Computes SHA-256 integrity hash, enforces 10MB ceiling, and isolates upload errors.
        """
        sanitized_name, detected_mime, sha256_hash, validated_bytes = inspect_and_validate_attachment(file_bytes, filename)
        creds = await self.get_valid_token()
        tenant_id = creds["tenant_id"]
        limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)

        async def _make_upload_request():
            async with httpx.AsyncClient(timeout=30.0) as client:
                return await client.put(
                    f"https://api.xero.com/api.xro/2.0/Invoices/{invoice_id}/Attachments/{sanitized_name}",
                    content=validated_bytes,
                    headers={
                        "Authorization": f"Bearer {creds['access_token']}",
                        "Xero-Tenant-Id": tenant_id,
                        "Content-Type": detected_mime,
                        "Accept": "application/json"
                    }
                )

        resp = await limiter.execute(_make_upload_request)
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to upload attachment (HTTP {resp.status_code}): {resp.text}")

        resp_json = {}
        attachment_id = None
        try:
            resp_json = resp.json()
            attachments = resp_json.get("Attachments", [])
            if attachments and isinstance(attachments, list):
                attachment_id = attachments[0].get("AttachmentID")
        except Exception:
            pass

        return {
            "status": "success",
            "attachment_id": attachment_id or sanitized_name,
            "sha256": sha256_hash,
            "filename": sanitized_name,
            "mime_type": detected_mime,
            "size_bytes": len(validated_bytes),
            "raw_response": resp_json
        }

    async def get_invoice(self, invoice_id: str) -> dict:
        creds = await self.get_valid_token()
        tenant_id = creds["tenant_id"]
        limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)
        headers = {
            "Authorization": f"Bearer {creds['access_token']}",
            "Xero-Tenant-Id": tenant_id,
            "Accept": "application/json"
        }

        async def _make_request():
            async with httpx.AsyncClient(timeout=15.0) as client:
                return await client.get(
                    f"https://api.xero.com/api.xro/2.0/Invoices/{invoice_id}",
                    headers=headers
                )

        resp = await limiter.execute(_make_request)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch invoice {invoice_id} (HTTP {resp.status_code}): {resp.text}")
        return resp.json()

    async def get_invoices(self, where: str | None = None) -> list:
        creds = await self.get_valid_token()
        tenant_id = creds["tenant_id"]
        limiter = await XeroTenantRateLimiter.get_limiter(tenant_id)
        headers = {
            "Authorization": f"Bearer {creds['access_token']}",
            "Xero-Tenant-Id": tenant_id,
            "Accept": "application/json"
        }
        params = {}
        if where:
            params["where"] = where

        async def _make_request():
            async with httpx.AsyncClient(timeout=15.0) as client:
                return await client.get(
                    "https://api.xero.com/api.xro/2.0/Invoices",
                    headers=headers,
                    params=params
                )

        resp = await limiter.execute(_make_request)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch invoices (HTTP {resp.status_code}): {resp.text}")
        return resp.json().get("Invoices", [])
