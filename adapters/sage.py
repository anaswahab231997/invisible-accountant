import os
import requests
from typing import Dict, Any
from .base import AccountingAdapter

class SageAdapter(AccountingAdapter):
    def __init__(self):
        self.client_id = os.environ.get("SAGE_CLIENT_ID")
        self.client_secret = os.environ.get("SAGE_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("SAGE_REDIRECT_URI")
        self.base_url = "https://api.accounting.sage.com/v3.1"
        self.auth_url = "https://www.sageone.com/oauth2/auth/central"
        self.token_url = "https://oauth.accounting.sage.com/token"
        
    def get_authorization_url(self) -> str:
        return f"{self.auth_url}?client_id={self.client_id}&response_type=code&redirect_uri={self.redirect_uri}&scope=full_access"

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        response = requests.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()

    def create_draft_bill(self, access_token: str, company_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/purchase_invoices"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Map our internal payload to Sage format
        sage_payload = {
            "purchase_invoice": {
                "contact_id": payload.get("vendor_id", "default"),
                "date": payload.get("date", "2023-01-01"),
                "due_date": payload.get("due_date", "2023-01-31"),
                "invoice_lines": [
                    {
                        "description": "Expense from Invisible Accountant",
                        "ledger_account_id": payload.get("account_id", "default"),
                        "quantity": 1,
                        "unit_price": payload.get("net_amount", 0.0),
                        "tax_amount": payload.get("vat_amount", 0.0)
                    }
                ]
            }
        }
        
        response = requests.post(url, headers=headers, json=sage_payload)
        response.raise_for_status()
        return response.json()
