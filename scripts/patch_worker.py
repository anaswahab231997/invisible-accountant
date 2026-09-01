import re

def patch():
    with open('worker.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Fix decryption TypeError and AAD
    old_decrypt = """        decrypted_json = token_engine.decrypt_tokens(
            encrypted_blob, 
            associated_data=f"hmrc_identity_{whatsapp_id}"
        )"""
    new_decrypt = """        encrypted_payload = json.loads(encrypted_blob.decode("utf-8"))
        decrypted_json = token_engine.decrypt_tokens(
            encrypted_payload, 
            associated_data=f"hmrc_identity_{whatsapp_id}"
        )"""
    content = content.replace(old_decrypt, new_decrypt)

    # 2. Fix nested PII logging
    pii_fix_old = """        safe_payload = {k: v for k, v in e.payload.items() if k.lower() not in ['nino', 'utr', 'password', 'name', 'address']}
        logger.error("HMRC API Error", queue_id=item["id"], status=e.status_code, payload=safe_payload)"""
    
    pii_fix_new = """        def sanitize_pii(data):
            if isinstance(data, dict):
                return {k: sanitize_pii(v) for k, v in data.items() if k.lower() not in ['nino', 'utr', 'password', 'name', 'address', 'vrn']}
            elif isinstance(data, list):
                return [sanitize_pii(v) for v in data]
            return data
            
        safe_payload = sanitize_pii(e.payload)
        logger.error("HMRC API Error", queue_id=item["id"], status=e.status_code, payload=safe_payload)"""
    content = content.replace(pii_fix_old, pii_fix_new)

    # 3. Fix Rate Limiter lazy lock
    lock_old = """    async def consume(self, tokens: int = 1):
        if self.lock is None:
            self.lock = asyncio.Lock()
            
        async with self.lock:"""
    lock_new = """    async def consume(self, tokens: int = 1):
        if getattr(self, "lock", None) is None:
            # Although technically a race here if 2 tasks hit it, doing it in __init__ is better.
            # We'll just do a lightweight fallback if __init__ isn't async
            pass
            
        # We will fix the class __init__ instead
        pass"""
        
    class_old = """class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_fill = time.monotonic()
        self.lock = None

    async def consume(self, tokens: int = 1):
        if self.lock is None:
            self.lock = asyncio.Lock()
            
        async with self.lock:"""
    class_new = """class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_fill = time.monotonic()
        # Initialize Lock synchronously 
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1):
        async with self.lock:"""
    content = content.replace(class_old, class_new)

    with open('worker.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
if __name__ == "__main__":
    patch()
