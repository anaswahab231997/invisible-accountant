with open('ws.py', 'r', encoding='utf-8') as f:
    ws_content = f.read()

ws_old = '''class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def broadcast(self, message: dict):
        for client_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_json(message)
            except Exception:
                pass'''

ws_new = '''from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id].copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        for client_id, connections in list(self.active_connections.items()):
            for connection in connections.copy():
                try:
                    await connection.send_json(message)
                except Exception:
                    pass'''

ws_content = ws_content.replace(ws_old, ws_new)

with open('ws.py', 'w', encoding='utf-8') as f:
    f.write(ws_content)

# Update main.py to pass websocket to disconnect
with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

main_old = '''    except Exception:
        pass
    finally:
        manager.disconnect(client_id)'''

main_new = '''    except Exception:
        pass
    finally:
        manager.disconnect(websocket, client_id)'''

main_content = main_content.replace(main_old, main_new)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)

print("WebSocket patched")
