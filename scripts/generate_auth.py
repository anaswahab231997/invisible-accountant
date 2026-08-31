import asyncio
import os
import secrets
import hashlib
import base64
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

async def main():
    client_id = os.getenv("HMRC_CLIENT_ID")
    client_secret = os.getenv("HMRC_CLIENT_SECRET")
    base_url = os.getenv("HMRC_BASE_URL")
    redirect_uri = os.getenv("HMRC_REDIRECT_URI", "http://localhost:8000/callback")
    
    async with httpx.AsyncClient() as client:
        # 1. Get Application Token
        auth_resp = await client.post(
            f"{base_url}/oauth/token",
            data={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"}
        )
        app_token = auth_resp.json().get("access_token")
        
        # 2. Create Test User
        resp = await client.post(
            f"{base_url}/create-test-user/individuals",
            json={"serviceNames": ["mtd-income-tax"]},
            headers={"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"}
        )
        if resp.status_code != 201:
            print(f"FAILED: {resp.text}")
            return
        
        test_user = resp.json()
        
        # Save Test User
        with open(".env.test.local", "w") as f:
            json.dump(test_user, f)
            
        # 3. Generate OAuth Auth URL
        # Note: Scopes for MTD Income Tax usually include read:self-assessment write:self-assessment
        scopes = "read:self-assessment write:self-assessment"
        state = secrets.token_urlsafe(32)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge_hash).decode('ascii').rstrip('=')
        
        # Save PKCE data for step 2
        with open(".pkce.json", "w") as f:
            json.dump({"state": state, "code_verifier": code_verifier}, f)
            
        auth_url = (
            f"{base_url}/oauth/authorize?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"scope={scopes}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256"
        )
        
        print("SUCCESS")
        print(f"USER_ID:{test_user.get('userId')}")
        print(f"PASSWORD:{test_user.get('password')}")
        print(f"AUTH_URL:{auth_url}")

if __name__ == "__main__":
    asyncio.run(main())
