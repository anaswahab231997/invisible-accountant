import re

with open('hmrc_api.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the spoofing logic
content = re.sub(r"client_ip = server_egress_ip\n\s+", "", content)

# Update the headers dictionary
old_headers = '''    headers = {
        "Gov-Client-Connection-Method": "OTHER_VIA_SERVER",
        "Gov-Client-Timezone": "UTC+00:00",
        "Gov-Client-Local-IPs": client_ip,
        "Gov-Client-Local-IPs-Timestamp": now,
        "Gov-Client-Public-IP": client_ip, # Must match 'for'
        "Gov-Client-Public-IP-Timestamp": now,
        "Gov-Client-User-Agent": "os-family=Unknown&os-version=Unknown&device-manufacturer=Unknown&device-model=Unknown",
        "Gov-Vendor-Version": "InvisibleAccountantClient=1.0.0&InvisibleAccountantServer=1.0.0",
        "Gov-Vendor-Public-IP": server_egress_ip, # Must match 'by'
        "Gov-Vendor-Forwarded": f"by={server_egress_ip}&for={client_ip}",
        "Gov-Vendor-Product-Name": "InvisibleAccountant",
        "Gov-Vendor-License-IDs": "InvisibleAccountant=e82dde43c926e486f1a7766a20691ed7f351b798e77bd903cb0b744bb92e240a"
    }'''

new_headers = '''    # Following HMRC strict guidelines: Omit headers that cannot be collected for WhatsApp/Twilio architectures 
    # instead of spoofing them with the server egress IP.
    headers = {
        "Gov-Client-Connection-Method": "OTHER_VIA_SERVER",
        "Gov-Client-Timezone": "UTC+00:00",
        "Gov-Vendor-Version": "InvisibleAccountantClient=1.0.0&InvisibleAccountantServer=1.0.0",
        "Gov-Vendor-Public-IP": server_egress_ip,
        "Gov-Vendor-Forwarded": f"by={server_egress_ip}", # 'for' omitted because client IP is obscured by WhatsApp
        "Gov-Vendor-Product-Name": "InvisibleAccountant",
        "Gov-Vendor-License-IDs": "InvisibleAccountant=e82dde43c926e486f1a7766a20691ed7f351b798e77bd903cb0b744bb92e240a"
    }'''

content = content.replace(old_headers, new_headers)

with open('hmrc_api.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("HMRC headers patched")
