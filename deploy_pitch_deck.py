import httpx
import json

# Using existing credentials pattern from deploy_render.py
RENDER_API_KEY = "rnd_8RYuyEWDh6FXY7PbJYuYfUMcDZvf"
OWNER_ID = "tea-daa9168n74is73a74dp0"
HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# The Render API payload for a Static Site
payload = {
    "ownerId": OWNER_ID,
    "type": "static_site",
    "name": "invisible-accountant-pitch-deck",
    "repo": "https://github.com/anaswahab231997/invisible-accountant",
    "autoDeploy": "yes",
    "branch": "main",
    "serviceDetails": {
        "publishPath": "./",
        "pullRequestPreviewsEnabled": "no",
        "buildCommand": "echo 'No build command needed for static HTML'"
    }
}

print("Creating Render Static Site for Pitch Deck...")
resp = httpx.post("https://api.render.com/v1/services", headers=HEADERS, json=payload)

if resp.status_code == 201:
    service = resp.json()
    service_id = service.get("id")
    public_url = service.get("serviceDetails", {}).get("url")
    print(f"Service created! ID: {service_id}")
    print(f"Deployment initiated for the pitch deck.")
    print(f"Once complete, it will be available at: {public_url}/pitch_perfect_investor_deck.html")
elif resp.status_code == 401:
    print("Error: Unauthorized. The Render API Key might be expired or invalid.")
    print("Please update the RENDER_API_KEY in the script.")
else:
    print(f"Error creating service ({resp.status_code}):", resp.text)
