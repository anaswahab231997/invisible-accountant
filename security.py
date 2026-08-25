import hmac
import hashlib
import os
import re
from cryptography.fernet import Fernet
from fastapi import Request, HTTPException

# --- 1. WhatsApp Webhook Security (HMAC Signature) ---
def verify_whatsapp_signature(request_body: bytes, signature_header: str, app_secret: str):
    if not signature_header or not signature_header.startswith('sha256='):
        raise HTTPException(status_code=403, detail="Invalid signature header")
    
    signature = signature_header.split('sha256=')[1]
    expected_hmac = hmac.new(
        key=app_secret.encode('utf-8'),
        msg=request_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected_hmac, signature):
        raise HTTPException(status_code=403, detail="Signature mismatch")

# --- 2. AI Data Privacy (PII Masking / DLP) ---
def mask_pii(text: str) -> str:
    # Mask UK Phone Numbers
    text = re.sub(r'(\+44\s?7\d{3}|\b07\d{3})\s?\d{6}\b', '<PHONE_NUMBER>', text)
    # Mask UK National Insurance Numbers (NINO)
    text = re.sub(r'\b[A-CEGHJ-PR-TW-Z]{1}[A-CEGHJ-NPR-TW-Z]{1}[0-9]{6}[A-D]{1}\b', '<NINO>', text, flags=re.IGNORECASE)
    # Mask Credit Card PANs (16 digits)
    text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '<CREDIT_CARD>', text)
    return text

# --- 3. Database Security (AES-256 Authenticated Encryption) ---
# In production, this key must come from a KMS. We use Fernet for AES-128-CBC with HMAC authentication (highly secure standard).
# For strict AES-256-GCM, the cryptography.hazmat primitives would be used.
encryption_key = os.getenv("DB_ENCRYPTION_KEY") or Fernet.generate_key().decode()
cipher_suite = Fernet(encryption_key.encode())

def encrypt_token(token: str) -> bytes:
    return cipher_suite.encrypt(token.encode('utf-8'))

def decrypt_token(encrypted_token: bytes) -> str:
    return cipher_suite.decrypt(encrypted_token).decode('utf-8')

# --- 4. HMRC Transmission Security (Fraud Prevention Headers) ---
def generate_hmrc_fraud_headers(client_ip: str, device_id: str) -> dict:
    return {
        "Gov-Client-Connection-Method": "WEB_APP_VIA_SERVER",
        "Gov-Client-Public-IP": client_ip,
        "Gov-Client-Public-Port": "443",
        "Gov-Client-Device-ID": device_id,
        "Gov-Vendor-Version": "InvisibleAccountant=1.0.0",
        "Gov-Vendor-License-IDs": "InvisibleAccountant=12345",
        "Gov-Client-Timezone": "UTC+00:00"
    }
