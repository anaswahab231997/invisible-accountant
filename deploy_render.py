import httpx
import os
import json

RENDER_API_KEY = "rnd_8RYuyEWDh6FXY7PbJYuYfUMcDZvf"
OWNER_ID = "tea-daa9168n74is73a74dp0"
HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# 1. Parse .env
env_vars = []
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'): continue
        parts = line.split('=', 1)
        if len(parts) == 2:
            key, val = parts[0], parts[1]
            if key == "HMRC_REDIRECT_URI":
                val = "PLACEHOLDER" # Will update later
            env_vars.append({"key": key, "value": val, "generateValue": False})

# 2. Create Service
payload = {
    "ownerId": OWNER_ID,
    "type": "web_service",
    "name": "invisible-accountant",
    "repo": "https://github.com/anaswahab231997/invisible-accountant",
    "autoDeploy": "yes",
    "branch": "main",
    "serviceDetails": {
        "env": "docker",
        "region": "frankfurt",
        "plan": "free",
        "envVars": env_vars
    }
}

print("Creating Render Service...")
resp = httpx.post("https://api.render.com/v1/services", headers=HEADERS, json=payload)
if resp.status_code != 201:
    print("Error creating service:", resp.text)
    exit(1)

service = resp.json()
print("RAW RENDER RESPONSE:", json.dumps(service, indent=2))
service_id = service.get("id")
if not service_id:
    print("Failed to extract service ID.")
    exit(1)
public_url = service["serviceDetails"]["url"]
print(f"Service created! ID: {service_id}")
print(f"Public URL: {public_url}")

# 3. Update HMRC_REDIRECT_URI with the new URL
new_redirect_uri = f"{public_url}/callback"

print(f"Updating HMRC_REDIRECT_URI to {new_redirect_uri} ...")
env_vars_update = []
for var in env_vars:
    if var["key"] == "HMRC_REDIRECT_URI":
        env_vars_update.append({"key": "HMRC_REDIRECT_URI", "value": new_redirect_uri})
    else:
        env_vars_update.append(var)

update_resp = httpx.put(f"https://api.render.com/v1/services/{service_id}/env-vars", headers=HEADERS, json=env_vars_update)
if update_resp.status_code == 200:
    print("Environment variables updated successfully!")
else:
    print("Error updating env vars:", update_resp.text)

print(f"DEPLOYMENT INITIATED! View it live at: {public_url}")
