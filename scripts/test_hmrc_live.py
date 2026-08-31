import asyncio
import os
import httpx
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hmrc_api import HMRCClient, generate_whatsapp_fraud_headers

load_dotenv()

async def test_hmrc_live():
    print("[DEV] Starting Live HMRC Sandbox Test...")
    
    client_id = os.getenv("HMRC_CLIENT_ID")
    client_secret = os.getenv("HMRC_CLIENT_SECRET")
    base_url = os.getenv("HMRC_BASE_URL")
    
    async with httpx.AsyncClient() as client:
        # 1. Get Application Token
        print("\n[1] Getting Application Token...")
        auth_resp = await client.post(
            f"{base_url}/oauth/token",
            data={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        )
        app_token = auth_resp.json().get("access_token")
        
        # 2. Test creating a test user (Server-to-Server)
        print("\n[2] Attempting to create an HMRC Test Individual...")
        resp = await client.post(
            f"{base_url}/create-test-user/individuals",
            json={"serviceNames": ["mtd-income-tax"]},
            headers={"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"}
        )
        if resp.status_code == 201:
            test_user = resp.json()
            print(f"Success! Created Test User:")
            print(f"    NINO: {test_user.get('nino')}")
            print(f"    MTD ID: {test_user.get('mtdItId')}")
        else:
            print(f"Failed to create test user: {resp.status_code} {resp.text}")
            return

    # 3. Test our HMRCClient TLS & Headers against the Sandbox
    print("\n[3] Testing TLS 1.2+ and Fraud Prevention Headers via HMRCClient...")
    fraud_headers = generate_whatsapp_fraud_headers("mock_device_id_123")
    hmrc_client = HMRCClient(access_token="INVALID_TOKEN_FOR_TESTING_HEADERS", fraud_headers=fraud_headers)
    
    try:
        # We expect a 401 Unauthorized, NOT a TLS handshake error or 403 Missing Headers
        await hmrc_client.submit_periodic_update(
            nino=test_user.get('nino'),
            income_source_id="XAIS12345678901",
            amount=14.50,
            period_start="2023-04-06",
            period_end="2024-04-05"
        )
    except Exception as e:
        status = getattr(e, 'status_code', None)
        if status == 401:
            print("Success! Reached HMRC Sandbox securely.")
            print("    Received 401 Unauthorized (Expected because we don't have a valid OAuth token yet).")
            print("    TLS 1.2 and Fraud Prevention headers are accepted by HMRC.")
        else:
            print(f"Unexpected Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hmrc_live())
