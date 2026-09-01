import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace broadcast with send_personal_message in process_intake_task
content = re.sub(
    r'await manager\.broadcast\(\{\s*"type": "INTAKE_UPDATE",\s*"chat_id": chat_id,\s*"result": (.*?)\s*\}\)',
    r'await manager.send_personal_message({"type": "INTAKE_UPDATE", "chat_id": chat_id, "result": \1}, sender_id)',
    content,
    flags=re.DOTALL
)

# Update websocket endpoint
old_ws = '''@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)'''

new_ws = '''@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        manager.disconnect(client_id)'''

content = content.replace(old_ws, new_ws)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched main.py")
