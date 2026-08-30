import os
import secrets
import hashlib
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("HMRC_CLIENT_ID")
client_secret = os.getenv("HMRC_CLIENT_SECRET")
base_url = os.getenv("HMRC_BASE_URL")

print("Authenticating with HMRC Sandbox...")

# 1. Get Application-Restricted Token
auth_url = f"{base_url}/oauth/token"
auth_data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "grant_type": "client_credentials",
}

response = requests.post(auth_url, data=auth_data)
if response.status_code != 200:
    print("Authentication failed!")
    print(response.json())
    exit(1)

token = response.json().get("access_token")
print("Successfully generated HMRC OAuth Bearer Token!")

# 2. Create a Test User (Sole Trader)
test_user_url = f"{base_url}/create-test-user/individuals"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.hmrc.1.0+json",
    "Content-Type": "application/json",
}

payload = {"serviceNames": ["national-insurance", "self-assessment", "mtd-income-tax"]}

print("Generating synthetic UK Taxpayer...")
response = requests.post(test_user_url, json=payload, headers=headers)

if response.status_code in [200, 201]:
    data = response.json()
    print("Successfully generated HMRC Test User!")
    
    # Securely save credentials to a local gitignored file instead of printing
    env_test_local_path = ".env.test.local"
    with open(env_test_local_path, "w") as f:
        f.write(f"TEST_USER_ID={data.get('userId')}\n")
        f.write(f"TEST_PASSWORD={data.get('password')}\n")
        f.write(f"TEST_NINO={data.get('nino')}\n")
        f.write(f"TEST_UTR={data.get('mtdItId')}\n")
        
    print(f"Test credentials securely saved to {env_test_local_path}. DO NOT COMMIT THIS FILE.")
else:
    print("Failed to create test user:")
    print(response.text)
    exit(1)

# 3. User-restricted OAuth 2.0 Flow (MTD Requirement)
print("\n--- MTD USER-RESTRICTED OAUTH FLOW ---")
redirect_uri = os.getenv("HMRC_REDIRECT_URI", "http://localhost:8000/callback")
scopes = "read:self-assessment write:self-assessment"

# Generate state and PKCE parameters for CSRF and injection protection
state = secrets.token_urlsafe(32)
code_verifier = secrets.token_urlsafe(64)
code_challenge_hash = hashlib.sha256(code_verifier.encode('ascii')).digest()
code_challenge = base64.urlsafe_b64encode(code_challenge_hash).decode('ascii').rstrip('=')

# Generate Auth URL with state and PKCE
auth_code_url = (
    f"{base_url}/oauth/authorize?"
    f"response_type=code&"
    f"client_id={client_id}&"
    f"scope={scopes}&"
    f"redirect_uri={redirect_uri}&"
    f"state={state}&"
    f"code_challenge={code_challenge}&"
    f"code_challenge_method=S256"
)

print(f"\n1. Go to this URL in your browser:\n{auth_code_url}")
print(f"2. Log in using the Test User credentials from {env_test_local_path}.")
print("3. Grant authority to the application.")
print(f"4. You will be redirected to {redirect_uri}?code=AUTHORIZATION_CODE&state=...")

auth_code = input("\nEnter the AUTHORIZATION_CODE from the URL: ").strip()
returned_state = input("Enter the STATE from the URL (to verify CSRF): ").strip()

if returned_state != state:
    print("SECURITY ALERT: State mismatch! Potential CSRF attack detected. Aborting.")
    exit(1)

if auth_code:
    print("Exchanging Authorization Code for User-Restricted Token...")
    token_exchange_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code": auth_code,
        "code_verifier": code_verifier,  # Include PKCE verifier
    }

    token_response = requests.post(auth_url, data=token_exchange_data)
    if token_response.status_code == 200:
        print("Success! Received User-Restricted Access Token.")
        # Only print keys, don't dump the full token to console
        print("Token payload keys:", list(token_response.json().keys()))
    else:
        print("Failed to exchange token:")
        print(token_response.json())
