import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import HTTPException


class TokenEncryptionEngine:
    def __init__(self, master_key_b64: str):
        self.master_key = base64.b64decode(master_key_b64)
        if len(self.master_key) != 32:
            raise ValueError("Master key must be exactly 32 bytes for AES-256")

    def encrypt_tokens(self, plaintext: str, associated_data: str) -> dict[str, str]:
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(nonce))
        encryptor = cipher.encryptor()

        encryptor.authenticate_additional_data(associated_data.encode("utf-8"))

        ciphertext = encryptor.update(plaintext.encode("utf-8")) + encryptor.finalize()

        return {
            "nonce": base64.b64encode(nonce).decode("utf-8"),
            "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
            "tag": base64.b64encode(encryptor.tag).decode("utf-8"),
        }

    def decrypt_tokens(
        self, encrypted_payload: dict[str, str], associated_data: str
    ) -> str:
        try:
            nonce = base64.b64decode(encrypted_payload["nonce"])
            ciphertext = base64.b64decode(encrypted_payload["ciphertext"])
            tag = base64.b64decode(encrypted_payload["tag"])

            cipher = Cipher(algorithms.AES(self.master_key), modes.GCM(nonce, tag))
            decryptor = cipher.decryptor()

            decryptor.authenticate_additional_data(associated_data.encode("utf-8"))

            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode("utf-8")

        except InvalidTag:
            raise HTTPException(
                status_code=500,
                detail="Cryptographic integrity failure. Data may have been tampered with.",
            )
        except Exception:
            # Catch other potential decoding errors without leaking data
            raise HTTPException(
                status_code=500, detail="Cryptographic decryption failure."
            )
