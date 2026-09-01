def patch():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    old_auth = """@app.get("/auth")
async def auth(whatsapp_id: str):
    client_id = os.environ.get("HMRC_CLIENT_ID", "mock_client_id")
    redirect_uri = os.environ.get("HMRC_REDIRECT_URI", "http://localhost:8000/callback")
    
    state_uuid = await create_oauth_state(whatsapp_id)
    url = f"https://test-api.service.hmrc.gov.uk/oauth/authorize?response_type=code&client_id={client_id}&scope=read:self-assessment write:self-assessment&state={state_uuid}&redirect_uri={redirect_uri}"
    return RedirectResponse(url)"""

    new_auth = """import hashlib
@app.get("/auth")
async def auth(whatsapp_id: str, response: Response):
    client_id = os.environ.get("HMRC_CLIENT_ID", "mock_client_id")
    redirect_uri = os.environ.get("HMRC_REDIRECT_URI", "http://localhost:8000/callback")
    
    nonce = secrets.token_urlsafe(32)
    nonce_hash = hashlib.sha256(nonce.encode()).hexdigest()
    
    state_uuid = await create_oauth_state(whatsapp_id, nonce_hash)
    url = f"https://test-api.service.hmrc.gov.uk/oauth/authorize?response_type=code&client_id={client_id}&scope=read:self-assessment write:self-assessment&state={state_uuid}&redirect_uri={redirect_uri}"
    
    res = RedirectResponse(url)
    res.set_cookie(key="oauth_nonce", value=nonce, httponly=True, secure=True, samesite="lax")
    return res"""
    content = content.replace(old_auth, new_auth)

    old_callback = """@app.get("/callback")
async def callback(code: str, state: str):
    whatsapp_id = await consume_oauth_state(state)
    if not whatsapp_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")"""
        
    new_callback = """@app.get("/callback")
async def callback(request: Request, code: str, state: str):
    state_data = await consume_oauth_state(state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
    nonce = request.cookies.get("oauth_nonce")
    if not nonce:
        raise HTTPException(status_code=400, detail="Missing OAuth nonce cookie")
        
    expected_hash = state_data.get("nonce_hash")
    actual_hash = hashlib.sha256(nonce.encode()).hexdigest()
    
    if not expected_hash or not secrets.compare_digest(expected_hash, actual_hash):
        raise HTTPException(status_code=403, detail="CSRF token mismatch. Session fixation attempt prevented.")
        
    whatsapp_id = state_data["whatsapp_id"]"""
    content = content.replace(old_callback, new_callback)

    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    patch()
