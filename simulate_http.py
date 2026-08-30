import asyncio
import time
import httpx
import hmac
import hashlib
import json

async def simulate_http_traffic(num_requests=20):
    async with httpx.AsyncClient() as client:
        print(f"Sending {num_requests} concurrent HTTP requests to /webhook/whatsapp...")
        
        start_time = time.time()
        tasks = []
        
        for i in range(num_requests):
            payload = {
                "sender_id": f"user_{i}",
                "message": f"lunch {i} amount 10",
                "turn_count": 1
            }
            raw_body = json.dumps(payload).encode("utf-8")
            signature = hmac.new(
                "dummy_secret".encode("utf-8"),
                msg=raw_body,
                digestmod=hashlib.sha256
            ).hexdigest()
            
            headers = {
                "X-Hub-Signature-256": f"sha256={signature}",
                "Content-Type": "application/json"
            }
            
            tasks.append(client.post("http://localhost:8000/webhook/whatsapp", data=raw_body, headers=headers))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        status_codes = []
        for r in results:
            if isinstance(r, httpx.Response):
                status_codes.append(r.status_code)
            else:
                status_codes.append(str(r))
                
        print(f"HTTP requests completed in {time.time() - start_time:.2f} seconds.")
        print(f"Status codes: {status_codes}")

if __name__ == '__main__':
    asyncio.run(simulate_http_traffic(20))
