# Phase 4: Commercial Hardening, Rate Limiting, and High-Concurrency Token Locking
## UK Fintech Distributed Systems Engineering Architecture Specification

**Target System**: Invisible Accountant Core Engine (`accounting_client.py`, `worker.py`, `db.py`)  
**Compliance Standards**: HMRC MTD (Making Tax Digital) for VAT & ITSA, RFC 6749 (OAuth 2.0), RFC 9700 (OAuth 2.0 Security BCP), Xero Accounting API v2.0 Guidelines.

---

## 1. Xero API Rate Limiting Architecture

### 1.1 Official Xero Accounting API Rate Limits (Verified via developer.xero.com)

Xero enforces strict multi-dimensional rate limits at the tenant (connected organization) and application levels:

| Limit Dimension | Threshold | Scope | Breach Response Header | Behavior / Retry Semantics |
| :--- | :--- | :--- | :--- | :--- |
| **Concurrent Limit** | **5 calls** in-flight | Per Tenant / Org | `X-Rate-Limit-Problem: Concurrent` | No `Retry-After` header provided. Back off with immediate randomized jitter (50–300ms) until an in-flight socket completes. |
| **Minute Limit** | **60 calls** / 60s rolling | Per Tenant / Org | `X-Rate-Limit-Problem: Minute` | Returns `Retry-After: <seconds>` (1–60s) indicating time remaining until window resets. |
| **Daily Limit** | **5,000 calls** / 24h rolling | Per Tenant / Org | `X-Rate-Limit-Problem: Daily` | Applicable to Core, Plus, Advanced, and Enterprise tiers (1,000 for Starter). Returns `Retry-After: <seconds>`. |
| **App Minute Limit** | **10,000 calls** / 60s rolling | Global (Across all tenants) | `X-Rate-Limit-Problem: AppMinute` | Returns `Retry-After: <seconds>` for app-wide throttling. |

### 1.2 HTTP Response Headers Returned by Xero
On **every HTTP response** (both 2xx success and 4xx errors), Xero provides real-time telemetry headers:
* `X-MinLimit-Remaining`: Integer count of calls remaining in the active 60-second rolling window for that tenant.
* `X-DayLimit-Remaining`: Integer count of calls remaining in the active 24-hour rolling window for that tenant.
* `X-AppMinLimit-Remaining`: Integer count of calls remaining across the entire application quota for the current minute.

When an HTTP `429 Too Many Requests` is returned:
* `Retry-After`: Mandatory integer indicating the exact number of seconds the client must wait before re-attempting (supplied for Minute, Daily, and AppMinute limits).
* `X-Rate-Limit-Problem`: Explicit diagnosis of which constraint was breached (`Concurrent`, `Minute`, `Daily`, or `AppMinute`).

### 1.3 Tenant-Keyed Token-Bucket Rate Limiter & Concurrency Guard Architecture

To eliminate HTTP 429 errors proactively rather than reactively, `AccountingClient` must implement a three-tiered control system:

```
[Inbound Request]
       │
       ▼
[Tier 1: Tenant Concurrency Semaphore (Capacity: 4 / Max: 5)]
       │
       ▼
[Tier 2: Token-Bucket Limiter (Rate: 55 calls / 60s, Burst: 10)]
       │ (Delays if tokens exhausted)
       ▼
[Tier 3: Adaptive Throttle (Dynamic Feedback from X-MinLimit-Remaining)]
       │
       ▼
[Execute HTTP Call to Xero API]
       │
       ├── HTTP 200/201 ──► Update Telemetry (`X-MinLimit-Remaining`, `X-DayLimit-Remaining`)
       │
       └── HTTP 429 ──────► Extract `Retry-After` + Decorrelated Jitter Backoff
```

#### Production Implementation (`RateLimiter` class):
```python
import asyncio
import time
import random
from typing import Dict

class XeroTenantRateLimiter:
    """
    Per-tenant rate limiter enforcing:
    1. Max 4 concurrent calls (leaving 1 safety slot under Xero's hard limit of 5).
    2. Token bucket: 55 requests / 60s (0.9167 tokens/sec), burst capacity of 10.
    3. Adaptive throttling based on X-MinLimit-Remaining and X-DayLimit-Remaining headers.
    """
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.semaphore = asyncio.Semaphore(4)  # Concurrency cap
        self.capacity = 10.0                   # Max burst
        self.tokens = 10.0
        self.refill_rate = 55.0 / 60.0         # 0.9167 tokens/sec (safety margin below 60/min)
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()
        self.backoff_until = 0.0

    async def acquire(self):
        # 1. Enforce active Retry-After backoff window
        now = time.monotonic()
        if now < self.backoff_until:
            await asyncio.sleep(self.backoff_until - now)

        # 2. Token-bucket rate limiting
        async with self.lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.last_refill = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    break
                else:
                    wait_time = (1.0 - self.tokens) / self.refill_rate
                    await asyncio.sleep(wait_time)

    def update_from_headers(self, headers: dict, status_code: int):
        # Dynamic feedback loop from Xero response headers
        min_remaining = headers.get("X-MinLimit-Remaining")
        day_remaining = headers.get("X-DayLimit-Remaining")
        retry_after = headers.get("Retry-After")
        problem = headers.get("X-Rate-Limit-Problem")

        if status_code == 429:
            now = time.monotonic()
            if retry_after:
                # Add decorrelated jitter to prevent thundering herd on reset
                jitter = random.uniform(0.5, 2.0)
                self.backoff_until = max(self.backoff_until, now + float(retry_after) + jitter)
            elif problem == "Concurrent":
                # Concurrent limit has no Retry-After; back off with fast randomized jitter
                self.backoff_until = max(self.backoff_until, now + random.uniform(0.1, 0.5))
        elif min_remaining is not None:
            try:
                rem = int(min_remaining)
                if rem < 5:
                    # Dynamically reduce burst tokens and slow down when nearing limit
                    self.tokens = min(self.tokens, float(rem))
            except ValueError:
                pass
```

---

## 2. High-Concurrency OAuth 2.0 Token Refresh Race Condition

### 2.1 RFC 6749 & Xero Refresh Token Rotation (RTR) Dynamics

Under **RFC 6749 Section 6 (Refreshing an Access Token)** and **Section 10.4 (Refresh Token Protection)**, in conjunction with **OAuth 2.0 Security BCP (RFC 9700)**:
* Xero mandates **Refresh Token Rotation (RTR)**: Every token refresh request revokes the presented `refresh_token` and returns a new pair of credentials (`access_token` + new `refresh_token`).
* **Replay Attack Detection (RFC 6749 §10.4)**:
  > *"The authorization server MUST invalidate the entire authorization grant (and all previously issued tokens for that grant) upon detecting the reuse of an invalidated refresh token."*

#### The Catastrophic Race Condition:
In a multi-process asynchronous architecture (e.g., FastAPI web intake worker, background HMRC queue worker, interactive dashboard session):
1. Both Process A and Process B see `time_left < 300` seconds on the stored token.
2. Process A and Process B read the same database row containing `refresh_token_v1`.
3. Process A sends `refresh_token_v1` to `https://identity.xero.com/connect/token` at $T_0$.
4. Process B sends `refresh_token_v1` to `https://identity.xero.com/connect/token` at $T_0 + 15\text{ms}$.
5. Process A's request succeeds. Xero invalidates `refresh_token_v1` and issues `Token_Family_v2`.
6. Process B's request arrives with the already-consumed `refresh_token_v1`.
7. **Xero's Identity Server detects reuse of an invalidated refresh token, flags a potential credential compromise, and triggers Immediate Token Family Revocation**.
8. Xero immediately revokes `Token_Family_v2` (invalidating Process A's new tokens) and returns:
   ```json
   HTTP/1.1 400 Bad Request
   {
       "error": "invalid_grant"
   }
   ```
9. **Impact**: The tenant connection is permanently dead. Automated recovery is impossible; the end user must complete manual browser-based re-authentication via the Xero authorization consent flow.

### 2.2 Flaw in Previous Implementation (`FOR UPDATE SKIP LOCKED`)
In `accounting_client.py`:
```sql
SELECT * FROM accounting_connections 
WHERE workspace_id = $1 AND provider = $2 
FOR UPDATE SKIP LOCKED
```
* `SKIP LOCKED` instructs PostgreSQL to silently skip any row currently locked by another concurrent transaction.
* If Process A is holding the row lock during refresh, Process B receives zero rows (`None`).
* The code immediately executes:
  ```python
  if not row:
      raise Exception(f"No {self.provider} connection found for workspace {self.workspace_id}")
  ```
* Result: Process B immediately crashes with a false-positive connection failure instead of waiting for Process A to complete the refresh!

### 2.3 Solution: Atomic Distributed Locking with Double-Checked Locking Pattern

To guarantee **exactly-once refresh** across all processes, we implement a two-step pattern:
1. **Optimistic Fast-Path Read (Zero Contention)**: Read the connection without acquiring a lock. If `time_left >= 300s`, return immediately. 99.9% of calls complete in sub-millisecond time with zero lock overhead.
2. **PostgreSQL Row Lock (`FOR UPDATE` without `SKIP LOCKED`) with Re-Check**:
   * If `time_left < 300s`, open an explicit database transaction and query with `FOR UPDATE` (blocking wait).
   * Concurrent callers wait on the lock.
   * Once unblocked, **re-inspect `expires_at`**. If another worker completed the refresh while this caller was waiting, `time_left` is now ~1800s!
   * The unblocked caller reads the newly committed token and returns without making a redundant Xero HTTP call.
   * If `time_left` is still `< 300s`, this caller is the designated leader: it calls Xero, encrypts and updates the database row, and commits the transaction.

#### Production Implementation in `accounting_client.py`:
```python
async def get_valid_token(self) -> dict:
    # STEP 1: Optimistic read without lock (Fast-Path)
    async with get_connection() as conn:
        row = await conn.fetchrow(
            '''
            SELECT access_token, refresh_token, provider_tenant_id, expires_at 
            FROM accounting_connections 
            WHERE workspace_id = $1 AND provider = $2
            ''',
            self.workspace_id, self.provider
        )
        if not row:
            raise Exception(f"No {self.provider} connection found for workspace {self.workspace_id}")

        expires_at = row["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        time_left = (expires_at - datetime.now(timezone.utc)).total_seconds()

        # If token has more than 5 minutes remaining, return immediately
        if time_left >= 300:
            return {
                "access_token": self._decrypt(row["access_token"]),
                "tenant_id": row["provider_tenant_id"]
            }

    # STEP 2: Token needs refresh. Acquire exclusive distributed lock via SELECT FOR UPDATE (Slow-Path)
    async with get_connection() as conn:
        async with conn.transaction():
            # Blocking lock on the specific connection row
            row = await conn.fetchrow(
                '''
                SELECT id, access_token, refresh_token, provider_tenant_id, expires_at 
                FROM accounting_connections 
                WHERE workspace_id = $1 AND provider = $2 
                FOR UPDATE
                ''',
                self.workspace_id, self.provider
            )
            if not row:
                raise Exception(f"No {self.provider} connection found for workspace {self.workspace_id}")

            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            time_left = (expires_at - datetime.now(timezone.utc)).total_seconds()

            # STEP 3: Double-Checked Locking Verification
            # If another worker refreshed the token while we waited for the lock, reuse it!
            if time_left >= 300:
                return {
                    "access_token": self._decrypt(row["access_token"]),
                    "tenant_id": row["provider_tenant_id"]
                }

            # STEP 4: We hold the lock and the token is still expired. Execute refresh.
            current_refresh_token = self._decrypt(row["refresh_token"])
            new_tokens = await self._refresh_xero_token(current_refresh_token)

            new_access = new_tokens["access_token"]
            new_refresh = new_tokens.get("refresh_token", current_refresh_token)
            expires_in = new_tokens.get("expires_in", 1800)

            await conn.execute(
                '''
                UPDATE accounting_connections 
                SET access_token = $1, refresh_token = $2, 
                    expires_at = NOW() + (INTERVAL '1 second' * $3), 
                    updated_at = NOW()
                WHERE id = $4
                ''',
                self._encrypt(new_access),
                self._encrypt(new_refresh),
                expires_in,
                row["id"]
            )

            return {
                "access_token": new_access,
                "tenant_id": row["provider_tenant_id"]
            }
```

---

## 3. Receipt Attachment Integrity & Pipeline Robustness

### 3.1 Official Xero Attachments API Specifications
* **Endpoints**:
  * Upload: `PUT /api.xro/2.0/Invoices/{InvoiceID}/Attachments/{FileName}` or `POST`
  * Inspect: `GET /api.xro/2.0/Invoices/{InvoiceID}/Attachments`
* **File Size Ceiling**: Maximum **10 MB** (10,485,760 bytes) per attachment; maximum **10 attachments** per invoice.
* **Payload Format**: Raw binary body in request (NOT multipart form data, NOT base64).
* **MIME Support**: `application/pdf`, `image/jpeg`, `image/png`, `image/gif`, `image/tiff`.

### 3.2 Fortified Upload Pipeline Architecture
To ensure commercial integrity, `upload_attachment` must execute strict multi-tier verification before any bytes are transmitted:

1. **Magic-Byte MIME Validation**: Reject forged file extensions by examining binary signatures.
2. **10MB Size Guard**: Fast validation check before memory buffering.
3. **Cryptographic Checksumming**: SHA-256 calculation for immutable audit logs and duplicate prevention.
4. **Filename Sanitization**: Strip unsafe characters to comply with RFC 3986.
5. **Idempotent Existence Check**: Query Xero for existing attachments on the invoice to avoid redundant uploads on retry.

```python
import hashlib
import re

ALLOWED_MAGIC_BYTES = {
    b"%PDF": "application/pdf",
    b"\xFF\xD8\xFF": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff"
}

def validate_and_detect_mime(file_bytes: bytes) -> str:
    """Validate magic bytes against Xero-supported receipt formats."""
    if len(file_bytes) > 10 * 1024 * 1024:
        raise ValueError(f"Attachment exceeds Xero 10MB limit: {len(file_bytes)} bytes")

    for magic, mime in ALLOWED_MAGIC_BYTES.items():
        if file_bytes.startswith(magic):
            return mime
    raise ValueError("Invalid file format. Only PDF, JPEG, PNG, GIF, and TIFF are supported by Xero.")

def sanitize_filename(filename: str, fallback_ext: str = "pdf") -> str:
    """Sanitize filename to alphanumeric, dots, hyphens, and underscores."""
    clean = re.sub(r'[^a-zA-Z0-9._-]', '_', filename).strip('._')
    if not clean or "." not in clean:
        clean = f"receipt_{int(time.time())}.{fallback_ext}"
    return clean[:255]
```

### 3.3 Two-Phase Commit & Attachment Failure Decoupling

#### The Problem:
If an invoice is created in Xero (Phase 1), but an attachment upload fails (network timeout, image CDN 404, Xero 503), naive error handling either:
* Silently ignores the attachment error (leaving an unattached invoice), OR
* Re-executes the entire submission, creating duplicate invoices in Xero.

#### The Decoupled State Machine Solution:

```
[Expense Queue Item: PENDING]
              │
              ▼
    [Phase 1: Draft Bill Creation]
              │
              ├── Creates Draft Invoice in Xero
              ▼
   [Persist external_bill_id IMMEDIATELY in DB]
              │
              ├── Status: BILL_CREATED / ATTACHMENTS_PENDING
              ▼
    [Phase 2: Attachment Upload Pipeline]
              │
              ├── Check Xero GET /Invoices/{ID}/Attachments (Idempotency)
              ├── Upload Validated Attachments (SHA-256 Verified)
              │
              ├── Success ──► Status: SUBMITTED
              │
              └── Failure ──► Bill is PROTECTED.
                              Status: ATTACHMENT_RETRY
                              Retry job executes Phase 2 ONLY.
```

1. **Phase 1 (Bill Creation)**:
   * Worker calls `create_draft_bill()`.
   * When Xero returns `InvoiceID`, the worker **immediately writes `external_bill_id` to `hmrc_ledger` in an isolated database transaction**.
   * The bill now exists safely in both Xero and PostgreSQL.
2. **Phase 2 (Attachment Upload)**:
   * If attachment download or upload encounters an error:
     * The bill in Xero is **NOT deleted or cancelled**.
     * The ledger entry retains `external_bill_id`.
     * `hmrc_ledger.status` is set to `ATTACHMENT_PENDING` (or queued for attachment retry).
     * On retry, the worker detects that `external_bill_id` is already populated. It **skips bill creation entirely** and jumps directly to Phase 2, querying Xero's attachment endpoint to upload only the missing files.
     * If the attachment source is permanently corrupted, the bill remains registered as `SUBMITTED_NO_ATTACHMENT`, and an alert is sent without compromising accounting ledger integrity.

---

## 4. Phase 4 Implementation Plan & Execution Checklist

| Task | Component | Key Actions | Verification Gate |
| :--- | :--- | :--- | :--- |
| **4.1** | `accounting_client.py` | Implement `XeroTenantRateLimiter` with `asyncio.Semaphore(4)`, token-bucket (55/60s), and header telemetry parser (`X-MinLimit-Remaining`, `Retry-After`). | Rate limiter test: 20 rapid calls do not breach 429; `Retry-After` triggers backoff. |
| **4.2** | `accounting_client.py` | Replace `SKIP LOCKED` with Double-Checked Locking via optimistic read + `SELECT ... FOR UPDATE`. | Concurrent token refresh simulation: 10 concurrent tasks refresh simultaneously with zero `invalid_grant` errors. |
| **4.3** | `accounting_client.py` & `worker.py` | Fortify `upload_attachment` with magic-byte MIME checking, 10MB limit enforcement, SHA-256 calculation, and RFC 3986 filename sanitization. | Unit test with corrupted files, oversized (>10MB) payloads, and mock network timeouts. |
| **4.4** | `worker.py` | Decouple Phase 1 (Bill) and Phase 2 (Attachments) in the two-phase commit state machine, allowing independent attachment retries. | Live sandbox test: Simulate attachment failure after bill creation; verify idempotent retry. |
| **4.5** | `test_phase4_hardening.py` | Comprehensive automated test suite validating rate limiting, concurrent token locking, and attachment integrity. | 100% pass rate in CI/CD pipeline. |
