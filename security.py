import hashlib
import hmac
import os
import re

from fastapi import HTTPException

from cryptography.hazmat.primitives import padding
from dotenv import load_dotenv
load_dotenv()

from aes_gcm_security import TokenEncryptionEngine


# --- 1. WhatsApp Webhook Security (HMAC Signature) ---
def verify_whatsapp_signature(
    request_body: bytes, signature_header: str, app_secret: str
):
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=403, detail="Invalid signature header")

    signature = signature_header.split("sha256=")[1]
    expected_hmac = hmac.new(
        key=app_secret.encode("utf-8"), msg=request_body, digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hmac, signature):
        raise HTTPException(status_code=403, detail="Signature mismatch")


# --- 2. AI Data Privacy (PII Masking / DLP) ---
def mask_pii(text: str) -> str:
    # Mask Emails (Fixed TLD limit)
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "<EMAIL>", text
    )
    # Mask UK Postcodes
    text = re.sub(
        r"\b[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}\b", "<POSTCODE>", text, flags=re.IGNORECASE
    )
    # Mask UK Phone Numbers with optional spaces and dashes
    text = re.sub(r"(?:(?:\+44\s?|0)\d{4}\s?\d{6})", "<PHONE_NUMBER>", text)
    # Mask UK National Insurance Numbers (NINO)
    text = re.sub(
        r"\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s*\d{2}\s*\d{2}\s*\d{2}\s*[A-D]\b",
        "<NINO>",
        text,
        flags=re.IGNORECASE,
    )
    # Mask Credit Card PANs (13-19 digits)
    text = re.sub(r"\b(?:\d[ -]*?){13,19}\b", "<CREDIT_CARD>", text)
    # Mask UK UTR (Unique Taxpayer Reference) - 10 digits
    text = re.sub(r"\b\d{10}\b", "<UTR>", text)
    return text


# --- 3. Database Security (AES-256 Authenticated Encryption) ---
# NCSC compliant AES-256-GCM encryption
_master_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
if not _master_key:
    raise ValueError("ENCRYPTION_MASTER_KEY_B64 environment variable is missing.")
crypto_engine = TokenEncryptionEngine(master_key_b64=_master_key)


def encrypt_token(token: str, associated_data: str) -> dict:
    return crypto_engine.encrypt_tokens(token, associated_data)


def decrypt_token(encrypted_payload: dict, associated_data: str) -> str:
    return crypto_engine.decrypt_tokens(encrypted_payload, associated_data)


# --- 4. HMRC Transmission Security (Fraud Prevention Headers) ---
def generate_hmrc_fraud_headers(
    client_ip: str,
    device_id: str,
    user_agent: str,
    timezone: str = "UTC+00:00",
    port: str = "443",
) -> dict:
    return {
        "Gov-Client-Connection-Method": "WEB_APP_VIA_SERVER",
        "Gov-Client-Public-IP": client_ip,
        "Gov-Client-Public-Port": port,
        "Gov-Client-Device-ID": device_id,
        "Gov-Client-User-Agent": user_agent,
        "Gov-Vendor-Version": "InvisibleAccountant=1.0.0",
        "Gov-Vendor-License-IDs": "InvisibleAccountant=12345",
        "Gov-Client-Timezone": timezone,
    }

from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, Request, Response
from fastapi.responses import RedirectResponse
import secrets

API_KEY = os.environ.get("API_KEY")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_dashboard_api_key() -> str | None:
    return os.environ.get("API_KEY") or API_KEY

def is_valid_api_key(candidate: str | None) -> bool:
    expected = get_dashboard_api_key()
    if not candidate or not expected:
        return False
    try:
        return secrets.compare_digest(str(candidate).strip(), str(expected).strip())
    except Exception:
        return False

def is_authenticated_request(request: Request) -> bool:
    """Helper to check if a request has valid authentication without raising exceptions."""
    if is_valid_api_key(request.cookies.get("accountant_session")):
        return True
    if is_valid_api_key(request.headers.get("X-API-Key")):
        return True
    if is_valid_api_key(request.query_params.get("key")):
        return True
    return False

def set_accountant_session_cookie(
    response: Response,
    token: str | None = None,
    secure: bool = True,
    max_age: int = 604800,
) -> Response:
    expected = token or get_dashboard_api_key()
    if expected:
        response.set_cookie(
            key="accountant_session",
            value=expected,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=max_age,
        )
    return response

def clear_accountant_session_cookie(
    response: Response,
    secure: bool = True,
) -> Response:
    response.delete_cookie(
        key="accountant_session",
        httponly=True,
        secure=secure,
        samesite="lax",
    )
    return response

async def verify_api_key(api_key_header_val: str = Security(api_key_header)):
    expected = get_dashboard_api_key()
    if not expected or not api_key_header_val or not secrets.compare_digest(str(api_key_header_val).strip(), str(expected).strip()):
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    return api_key_header_val

async def verify_accountant_session(request: Request) -> str:
    """
    Hardened dual-auth dependency for Accountant Review Gateway.
    Checks:
      a) HTTP cookie: request.cookies.get("accountant_session")
      b) HTTP header: request.headers.get("X-API-Key")
      c) Query parameter: request.query_params.get("key") (magic link)
    Validation is performed against API_KEY using secrets.compare_digest.
    If authenticated via query parameter ?key=..., flags request.state.should_set_cookie = True.
    If unauthenticated:
      - Browser HTML navigation requests (Accept contains text/html, not HTMX) redirect to /dashboard/login?next=... (303).
      - API / HTMX requests receive HTTP 401 Unauthorized.
    """
    expected_key = get_dashboard_api_key()

    # a) HTTP cookie
    cookie_token = request.cookies.get("accountant_session")
    if is_valid_api_key(cookie_token):
        return cookie_token

    # b) HTTP header
    header_token = request.headers.get("X-API-Key")
    if is_valid_api_key(header_token):
        return header_token

    # c) Query parameter (magic link)
    query_token = request.query_params.get("key")
    if is_valid_api_key(query_token):
        request.state.should_set_cookie = True
        request.state.accountant_session = expected_key
        return query_token

    # If unauthenticated:
    accept_header = request.headers.get("accept", "")
    is_htmx = (request.headers.get("HX-Request", "").lower() == "true")
    is_browser_nav = ("text/html" in accept_header) and (not is_htmx)

    if is_browser_nav:
        login_url = f"/dashboard/login?next={request.url.path}"
        raise HTTPException(
            status_code=303,
            headers={"Location": login_url},
            detail="Authentication required",
        )
    else:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )


# --- 5. Receipt Fingerprinting & Deduplication ---
def normalize_sender_id(sender_id: str | None) -> str:
    s = str(sender_id or "").strip().lower()
    if s.startswith("whatsapp:"):
        s = s[len("whatsapp:"):]
    return s.strip()

def normalize_vendor(vendor: str | None) -> str:
    v = str(vendor or "unknown").strip().lower()
    v = re.sub(r'[\r\n\t]+', ' ', v)
    v = re.sub(r'[^\w\s]', '', v)
    v = re.sub(r'\s+', ' ', v)
    return v.strip()

def normalize_amount(amount: float | str | None) -> str:
    if amount is None:
        return "0.00"
    cleaned = re.sub(r'[^\d\.-]', '', str(amount))
    try:
        val = float(cleaned)
        return f"{val:.2f}"
    except (ValueError, TypeError):
        return "0.00"

def normalize_date(date_val: str | None) -> str:
    if not date_val:
        return ""
    clean_val = str(date_val).strip()
    if len(clean_val) >= 10 and clean_val[4] == '-' and clean_val[7] == '-':
        return clean_val[:10]
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%Y-%m-%dT%H:%M:%S"):
        try:
            from datetime import datetime
            return datetime.strptime(clean_val[:19], fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return clean_val[:10]

def compute_receipt_fingerprint(
    sender_id: str | None,
    vendor: str | None,
    gross_amount: float | str | None,
    transaction_date: str | None = None
) -> str:
    """
    Computes a deterministic SHA256 fingerprint for deduplication.
    Normalized over: (sender_id, vendor, gross_amount, transaction_date).
    """
    norm_sender = normalize_sender_id(sender_id)
    norm_vendor = normalize_vendor(vendor)
    norm_gross = normalize_amount(gross_amount)
    norm_date = normalize_date(transaction_date)
    raw = f"{norm_sender}:{norm_vendor}:{norm_gross}:{norm_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

