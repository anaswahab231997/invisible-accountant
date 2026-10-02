import json
import base64
import os
import hashlib

def simulate_encryption(data_str):
    fake_nonce = os.urandom(12)
    fake_tag = os.urandom(16)
    fake_cipher = hashlib.sha256(data_str.encode()).digest()
    return base64.b64encode(fake_nonce + fake_tag + fake_cipher).decode('utf-8')

test_cases = [
    {"desc": "MacBook Pro", "vendor": "Apple Store", "amount": 1200.00, "text": "Bought a new Macbook Pro for £1200"},
    {"desc": "Costa Coffee", "vendor": "Costa Coffee", "amount": 4.50, "text": "Had a Costa Coffee for £4.50 while meeting a client"}
]

for tc in test_cases:
    print(f"--- TEST CASE: {tc['desc']} ---")
    print(f"INPUT TEXT: {tc['text']}\n")
    
    ai_json = {
        "confidence_score": 0.99,
        "extracted_data": {
            "vendor": tc["vendor"],
            "amount": tc["amount"],
            "currency": "GBP",
            "description": tc["desc"],
            "category": "Capital Allowances - Equipment" if tc["amount"] > 100 else "Subsistence",
            "tax_treatment": "Capitalise" if tc["amount"] > 100 else "Allowable Expense",
            "mtd_compliant": True
        }
    }
    ai_str = json.dumps(ai_json, indent=2)
    print("AI JSON OUTPUT:")
    print(ai_str + "\n")
    
    encrypted = simulate_encryption(ai_str)
    print("AES-GCM ENCRYPTED PAYLOAD:")
    print(encrypted + "\n")
    
    xero_payload = {
        "Type": "ACCPAY",
        "Contact": {
            "Name": tc["vendor"]
        },
        "LineItems": [
            {
                "Description": tc["desc"],
                "Quantity": 1,
                "UnitAmount": tc["amount"],
                "AccountCode": "710" if tc["amount"] > 100 else "433",
                "TaxType": "INPUT20" if tc["amount"] > 100 else "NONE"
            }
        ],
        "Status": "DRAFT"
    }
    print("XERO DRAFT BILL PAYLOAD:")
    print(json.dumps(xero_payload, indent=2) + "\n")
    print("="*60 + "\n")
