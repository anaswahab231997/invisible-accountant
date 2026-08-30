import base64
import os
import unittest

from fastapi import HTTPException

from aes_gcm_security import TokenEncryptionEngine


class TestTokenEncryptionEngine(unittest.TestCase):
    def setUp(self):
        master_key = base64.b64encode(os.urandom(32)).decode("utf-8")
        self.engine = TokenEncryptionEngine(master_key)
        self.plaintext = '{"access_token": "hmrc_123", "refresh_token": "refresh_456"}'
        self.user_uuid = "user-1234-5678-uuid"

    def test_round_trip_verification(self):
        payload = self.engine.encrypt_tokens(self.plaintext, self.user_uuid)

        self.assertIn("nonce", payload)
        self.assertIn("ciphertext", payload)
        self.assertIn("tag", payload)

        decrypted = self.engine.decrypt_tokens(payload, self.user_uuid)
        self.assertEqual(decrypted, self.plaintext)

    def test_tamper_resistance_check_ciphertext(self):
        payload = self.engine.encrypt_tokens(self.plaintext, self.user_uuid)

        ciphertext_bytes = bytearray(base64.b64decode(payload["ciphertext"]))
        ciphertext_bytes[0] ^= 1
        payload["ciphertext"] = base64.b64encode(ciphertext_bytes).decode("utf-8")

        with self.assertRaises(HTTPException) as context:
            self.engine.decrypt_tokens(payload, self.user_uuid)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("integrity failure", context.exception.detail)

    def test_tamper_resistance_check_tag(self):
        payload = self.engine.encrypt_tokens(self.plaintext, self.user_uuid)

        tag_bytes = bytearray(base64.b64decode(payload["tag"]))
        tag_bytes[0] ^= 1
        payload["tag"] = base64.b64encode(tag_bytes).decode("utf-8")

        with self.assertRaises(HTTPException) as context:
            self.engine.decrypt_tokens(payload, self.user_uuid)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("integrity failure", context.exception.detail)

    def test_context_substitution_check(self):
        user_uuid_1 = "user-alice"
        user_uuid_2 = "user-bob"

        payload = self.engine.encrypt_tokens(self.plaintext, user_uuid_1)

        with self.assertRaises(HTTPException) as context:
            self.engine.decrypt_tokens(payload, user_uuid_2)

        self.assertEqual(context.exception.status_code, 500)
        self.assertIn("integrity failure", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
import pytest
pytestmark = pytest.mark.unit
