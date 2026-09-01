import json
import os

config_path = r'C:\Users\ANAS\.gemini\antigravity\mcp_config.json'

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

config['mcpServers']['render']['env']['RENDER_API_KEY'] = 'rnd_F6MiTusfxOT7MSDoZMgXI0mMhpEK'

with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=4)
