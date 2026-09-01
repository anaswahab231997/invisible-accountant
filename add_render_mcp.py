import json
import os

config_path = r'C:\Users\ANAS\.gemini\antigravity\mcp_config.json'

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

config['mcpServers']['render'] = {
    "command": r"C:\Users\ANAS\.gemini\antigravity\mcp\render\render-mcp-server_v0.3.0.exe",
    "args": [],
    "env": {
        "RENDER_API_KEY": ""  # Needs to be filled in by the user
    }
}

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4)
