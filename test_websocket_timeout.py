import asyncio
import websockets
import json
import time
import httpx

async def test_websocket_timeout():
    client_id = "test_timeout_client"
    uri = f"ws://localhost:8000/ws/{client_id}"
    print(f"Connecting to {uri}...")

    # Start the test
    start_time = time.time()
    ping_count = 0

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to websocket.")

            # Trigger the pipeline (BFF Simulator API)
            print("Triggering the pipeline...")
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        "http://localhost:8000/api/simulate_whatsapp",
                        json={
                            "sender_id": client_id,
                            "message": "Testing Cloudflare 100s timeout.",
                            "media_urls": [],
                            "turn_count": 1
                        },
                        timeout=5.0
                    )
                    print(f"Pipeline triggered, status: {resp.status_code}")
                except Exception as e:
                    print(f"Failed to trigger pipeline, maybe server isn't fully up? {e}")

            print("Simulating >105s delay waiting for AI response...")

            while time.time() - start_time < 110:
                try:
                    # Wait for message with a 20s timeout (since pings are every 15s)
                    message = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                    data = json.loads(message)

                    if data.get("type") == "PING":
                        ping_count += 1
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.1f}s] Received PING {ping_count} from server.")
                    else:
                        elapsed = time.time() - start_time
                        print(f"[{elapsed:.1f}s] Received AI payload: {data}")
                        
                        # Instead of breaking, we KEEP waiting to simulate the AI taking >105 seconds
                        # Or if the AI payload arrived too early (since local workers run fast),
                        # we still wait the full 110 seconds to ensure pings keep coming if we hadn't closed!
                        # BUT wait, the websocket endpoint in our fix continues to send pings as long as connection is open.
                except asyncio.TimeoutError:
                    print("No message received for 20 seconds! Connection might be dead or heartbeat failed.")
                    break

            print(f"Total pings received: {ping_count}")
            assert ping_count >= 6, f"Expected at least 6 pings to survive 100s Cloudflare limit, got {ping_count}."
            print("SUCCESS! Test passed! Connection was not dropped and pings were received.")

    except websockets.ConnectionClosed as e:
        print(f"Connection closed unexpectedly: {e}")
        assert False, "Connection dropped prematurely!"
        
if __name__ == "__main__":
    asyncio.run(test_websocket_timeout())
