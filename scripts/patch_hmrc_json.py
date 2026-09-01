with open('hmrc_api.py', 'r', encoding='utf-8') as f:
    content = f.read()
if 'import json' not in content:
    content = content.replace('import httpx', 'import httpx\nimport json')
    with open('hmrc_api.py', 'w', encoding='utf-8') as f:
        f.write(content)
print("Added import json")
