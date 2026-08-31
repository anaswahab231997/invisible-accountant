import httpx
import os
import json

RENDER_API_KEY = "rnd_8RYuyEWDh6FXY7PbJYuYfUMcDZvf"
SERVICE_ID = "srv-daa95qks728c73foktv0"
PUBLIC_URL = "https://invisible-accountant.onrender.com"
HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

env_vars = []
with open('.env', 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'): continue
        parts = line.split('=', 1)
        if len(parts) == 2:
            key, val = parts[0], parts[1]
            if key == "HMRC_REDIRECT_URI":
                val = f"{PUBLIC_URL}/callback"
            env_vars.append({"key": key, "value": val})

print("Updating Env Vars on Render...")
resp = httpx.put(f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars", headers=HEADERS, json=env_vars)
if resp.status_code == 200:
    print("SUCCESS: Environment variables securely injected!")
else:
    print("ERROR:", resp.text)
