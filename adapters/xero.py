import os
import requests
from typing import Dict, Any
from .base import AccountingAdapter
from requests.auth import HTTPBasicAuth

class XeroAdapter(AccountingAdapter):
    def __init__(self):
        self.client_id = os.environ.get("XERO_CLIENT_ID")
        self.client_secret = os.environ.get("XERO_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("XERO_REDIRECT_URI")
        self.base_url = "https://api.xero.com/api.xro/2.0"
        self.auth_url = "https://login.xero.com/identity/connect/authorize"
        self.token_url = "https://identity.xero.com/connect/token"
        
    def get_authorization_url(self) -> str:
        return f"{self.auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=offline_access accounting.transactions"

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        response = requests.post(
            self.token_url,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        response = requests.post(
            self.token_url,
            data=data,
            auth=HTTPBasicAuth(self.client_id, self.client_secret)
        )
        response.raise_for_status()
        return response.json()

    def create_draft_bill(self, access_token: str, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/Invoices"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "xero-tenant-id": tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Map our internal payload to Xero's format
        xero_payload = {
            "Type": "ACCPAY",
            "Contact": {
                "Name": payload.get("vendor", "Unknown Vendor")
            },
            "LineItems": [
                {
                    "Description": "Expense from Invisible Accountant",
                    "Quantity": 1,
                    "UnitAmount": payload.get("net_amount", 0.0),
                    "TaxAmount": payload.get("vat_amount", 0.0),
                    "AccountCode": payload.get("account_code", "429")
                }
            ],
            "Status": "DRAFT"
        }
        
        response = requests.post(url, headers=headers, json={"Invoices": [xero_payload]})
        response.raise_for_status()
        return response.json()
