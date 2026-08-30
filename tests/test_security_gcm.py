import base64
import os

import pytest
from fastapi import HTTPException

from aes_gcm_security import TokenEncryptionEngine


def test_aes_gcm_encryption_decryption():
    master_key = base64.b64encode(os.urandom(32)).decode("utf-8")
    engine = TokenEncryptionEngine(master_key_b64=master_key)

    plaintext = "super_secret_oauth_token_123"
    associated_data = "user_id_456"

    encrypted = engine.encrypt_tokens(plaintext, associated_data)

    assert "nonce" in encrypted
    assert "ciphertext" in encrypted
    assert "tag" in encrypted

    decrypted = engine.decrypt_tokens(encrypted, associated_data)
    assert decrypted == plaintext


def test_aes_gcm_tampered_ciphertext():
    master_key = base64.b64encode(os.urandom(32)).decode("utf-8")
    engine = TokenEncryptionEngine(master_key_b64=master_key)

    encrypted = engine.encrypt_tokens("token", "ad")

    # Tamper with ciphertext
    raw_cipher = base64.b64decode(encrypted["ciphertext"])
    tampered_cipher = raw_cipher[:-1] + bytes([(raw_cipher[-1] + 1) % 256])
    encrypted["ciphertext"] = base64.b64encode(tampered_cipher).decode("utf-8")

    with pytest.raises(HTTPException) as exc_info:
        engine.decrypt_tokens(encrypted, "ad")

    assert exc_info.value.status_code == 500
    assert "Cryptographic integrity failure" in str(exc_info.value.detail)


def test_aes_gcm_wrong_master_key():
    master_key1 = base64.b64encode(os.urandom(32)).decode("utf-8")
    master_key2 = base64.b64encode(os.urandom(32)).decode("utf-8")

    engine1 = TokenEncryptionEngine(master_key_b64=master_key1)
    engine2 = TokenEncryptionEngine(master_key_b64=master_key2)

    encrypted = engine1.encrypt_tokens("token", "ad")

    with pytest.raises(HTTPException):
        engine2.decrypt_tokens(encrypted, "ad")
import pytest
pytestmark = pytest.mark.unit
