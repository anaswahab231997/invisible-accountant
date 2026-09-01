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
_master_key = os.getenv("DB_ENCRYPTION_KEY_B64")
if not _master_key:
    raise ValueError("DB_ENCRYPTION_KEY_B64 environment variable is missing.")
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
