import os
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
    "grant_type": "client_credentials"
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
    "Content-Type": "application/json"
}

payload = {
    "serviceNames": ["national-insurance", "self-assessment", "mtd-income-tax"]
}

print("Generating synthetic UK Taxpayer...")
response = requests.post(test_user_url, json=payload, headers=headers)

if response.status_code in [200, 201]:
    data = response.json()
    print("Successfully generated HMRC Test User!")
    print("--------------------------------------------------")
    print(f"User ID: {data.get('userId')}")
    print(f"Password: {data.get('password')}")
    print(f"NINO: {data.get('nino')}")
    print(f"UTR: {data.get('mtdItId')}") # or saUtr
    print("--------------------------------------------------")
    print("Save these credentials safely! You will use them to log into the HMRC mock portal.")
else:
    print("Failed to create test user:")
    print(response.text)

