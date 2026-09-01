def patch():
    with open('db.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_create = """async def create_oauth_state(whatsapp_id: str) -> str:
    import uuid
    state_uuid = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        await conn.execute(
            "INSERT INTO oauth_states (state_uuid, whatsapp_id, created_at) VALUES ($1, $2, $3)",
            state_uuid, whatsapp_id, timestamp
        )
    return state_uuid"""
    
    new_create = """async def create_oauth_state(whatsapp_id: str, nonce_hash: str = None) -> str:
    import uuid
    state_uuid = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    async with get_connection() as conn:
        await conn.execute(
            "INSERT INTO oauth_states (state_uuid, whatsapp_id, nonce_hash, created_at) VALUES ($1, $2, $3, $4)",
            state_uuid, whatsapp_id, nonce_hash, timestamp
        )
    return state_uuid"""
    content = content.replace(old_create, new_create)
    
    old_consume = """async def consume_oauth_state(state_uuid: str) -> str:
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT whatsapp_id FROM oauth_states WHERE state_uuid = $1",
            state_uuid
        )
        if row:
            await conn.execute("DELETE FROM oauth_states WHERE state_uuid = $1", state_uuid)
            return row["whatsapp_id"]
        return None"""
        
    new_consume = """async def consume_oauth_state(state_uuid: str) -> dict:
    async with get_connection() as conn:
        row = await conn.fetchrow(
            "SELECT whatsapp_id, nonce_hash FROM oauth_states WHERE state_uuid = $1",
            state_uuid
        )
        if row:
            await conn.execute("DELETE FROM oauth_states WHERE state_uuid = $1", state_uuid)
            return dict(row)
        return None"""
    content = content.replace(old_consume, new_consume)
    
    with open('db.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch()
