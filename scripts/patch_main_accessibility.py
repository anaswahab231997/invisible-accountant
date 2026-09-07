with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

accessibility_route = '''
@app.get("/accessibility", response_class=HTMLResponse)
async def serve_accessibility():
    with open(os.path.join("templates", "accessibility.html"), "r", encoding="utf-8") as f:
        return f.read()

'''
if '@app.get("/accessibility"' not in content:
    content = content.replace(
        '@app.get("/terms", response_class=HTMLResponse)',
        accessibility_route + '@app.get("/terms", response_class=HTMLResponse)'
    )
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(content)
        print("Successfully injected /accessibility route into main.py")
