import asyncio
import os
import json
import httpx
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hmrc_api import HMRCClient, generate_whatsapp_fraud_headers

load_dotenv()

async def main():
    client_id = os.getenv("HMRC_CLIENT_ID")
    client_secret = os.getenv("HMRC_CLIENT_SECRET")
    base_url = os.getenv("HMRC_BASE_URL")
    redirect_uri = os.getenv("HMRC_REDIRECT_URI", "http://localhost:8000/callback")
    
    auth_code = "c959128b93d04379b055422b7be2fc5a"
    state = "TsMriFiV4nx1xY06bqtWajl8VSNCvEjHIu2VVu9x900"
    
    with open(".pkce.json", "r") as f:
        pkce_data = json.load(f)
    
    with open(".env.test.local", "r") as f:
        test_user = json.load(f)
        
    if pkce_data["state"] != state:
        print("SECURITY ERROR: State mismatch! CSRF protection triggered.")
        return
        
    async with httpx.AsyncClient() as client:
        print("[1] Exchanging Authorization Code for Access Token...")
        token_resp = await client.post(
            f"{base_url}/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": auth_code,
                "code_verifier": pkce_data["code_verifier"]
            }
        )
        
        if token_resp.status_code != 200:
            print(f"FAILED TO EXCHANGE TOKEN: {token_resp.text}")
            return
            
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        print("SUCCESS: Access Token acquired!")
        
        fraud_headers = generate_whatsapp_fraud_headers("mock_test_device_001")
        hmrc_client = HMRCClient(access_token=access_token, fraud_headers=fraud_headers)
        nino = test_user.get("nino")
        
        print(f"\n[2] Fetching Business Details for NINO {nino} to find Income Source ID...")
        try:
            biz_details = await hmrc_client.get_business_details(nino)
            
            income_source_id = None
            if "taxPayerDisplayResponse" in biz_details:
                # Based on HMRC MTD docs, it's usually inside taxPayerDisplayResponse -> businessData -> incomeSourceId
                bus_data = biz_details["taxPayerDisplayResponse"].get("businessData", [])
                if bus_data:
                    income_source_id = bus_data[0].get("incomeSourceId")
            elif "businessData" in biz_details:
                income_source_id = biz_details["businessData"][0].get("incomeSourceId")
                
            if not income_source_id:
                print("FAILED: Could not parse Income Source ID. Biz Details: ", biz_details)
                income_source_id = "XAIS12345678901"
            else:
                print(f"SUCCESS: Found Income Source ID: {income_source_id}")
        except Exception as e:
            print(f"FAILED to fetch business details: {e}")
            if hasattr(e, 'payload'): print(e.payload)
            print("Assuming test ID 'XAIS12345678901' to continue test...")
            income_source_id = "XAIS12345678901"
            
        print(f"\n[3] Submitting 45.50 'Printer Ink' Expense to MTD Sandbox...")
        try:
            result = await hmrc_client.submit_periodic_update(
                nino=nino,
                income_source_id=income_source_id,
                amount=45.50,
                period_start="2023-04-06",
                period_end="2024-04-05"
            )
            print("SUCCESS: Submitted dummy expense to HMRC Sandbox!")
            print(f"Response: {result}")
        except Exception as e:
            print(f"FAILED to submit expense: {e}")
            if hasattr(e, 'payload'): print(f"HMRC Payload: {e.payload}")

if __name__ == "__main__":
    asyncio.run(main())
