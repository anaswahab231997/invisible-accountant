import os
import httpx
import asyncio
from dotenv import load_dotenv
from hmrc_api import generate_whatsapp_fraud_headers

load_dotenv()

async def main():
    print("--------------------------------------------------")
    print("HMRC Fraud Prevention Headers Validator (WhatsApp)")
    print("--------------------------------------------------")
    
    client_id = os.getenv("HMRC_CLIENT_ID")
    client_secret = os.getenv("HMRC_CLIENT_SECRET")
    base_url = os.getenv("HMRC_BASE_URL")
    
    # Get Application Restricted Token
    print("Fetching Application Token...")
    async with httpx.AsyncClient() as client:
        auth_resp = await client.post(
            f"{base_url}/oauth/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials"
            }
        )
        token = auth_resp.json().get("access_token")
    
    # 1. Simulate a WhatsApp User
    dummy_whatsapp_number = "+447700900077"
    encryption_key = os.getenv("AES_GCM_KEY", "dummy_fallback_key_for_testing_only")
    
    # 2. Generate the OTHER_VIA_SERVER headers
    print(f"\nGenerating headers for user: {dummy_whatsapp_number}")
    fraud_headers = generate_whatsapp_fraud_headers(dummy_whatsapp_number, encryption_key)
    
    # Also we need an Accept and Auth header
    fraud_headers["Accept"] = "application/vnd.hmrc.1.0+json"
    fraud_headers["Authorization"] = f"Bearer {token}"
    
    print("\n[Headers to be sent]")
    for k, v in fraud_headers.items():
        if k != "Authorization":
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: Bearer [HIDDEN]")
            
    # 3. Fire them at the HMRC Sandbox Validator
    url = f"{base_url}/test/fraud-prevention-headers/validate"
    print(f"\nSending GET request to {url}...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=fraud_headers)
        
    print("\n[HMRC Response]")
    print(f"Status Code: {response.status_code}")
    
    try:
        print(response.json())
    except:
        print(response.text)

    if response.status_code == 200:
        print("\nSUCCESS: HMRC accepted the OTHER_VIA_SERVER headers!")
        print("Your WhatsApp architecture is fully compliant with Fraud Prevention guidelines.")
    else:
        print("\nFAILURE: HMRC rejected the headers.")

if __name__ == "__main__":
    asyncio.run(main())
