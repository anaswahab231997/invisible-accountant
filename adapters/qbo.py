import os
import requests
import base64
from typing import Dict, Any
from .base import AccountingAdapter

class QBOAdapter(AccountingAdapter):
    def __init__(self):
        self.client_id = os.environ.get("QBO_CLIENT_ID")
        self.client_secret = os.environ.get("QBO_CLIENT_SECRET")
        self.redirect_uri = os.environ.get("QBO_REDIRECT_URI")
        self.environment = os.environ.get("QBO_ENVIRONMENT", "sandbox")
        
        if self.environment == "production":
            self.base_url = "https://quickbooks.api.intuit.com/v3/company"
        else:
            self.base_url = "https://sandbox-quickbooks.api.intuit.com/v3/company"
            
        self.auth_url = "https://appcenter.intuit.com/connect/oauth2"
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
    def get_authorization_url(self) -> str:
        return f"{self.auth_url}?client_id={self.client_id}&response_type=code&scope=com.intuit.quickbooks.accounting&redirect_uri={self.redirect_uri}&state=security_token"

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        response = requests.post(self.token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

    def create_draft_bill(self, access_token: str, realm_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{realm_id}/bill"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Map our internal payload to QuickBooks Online format
        qbo_payload = {
            "VendorRef": {
                "value": payload.get("vendor_id", "1") # Needs QBO Vendor ID
            },
            "Line": [
                {
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "Amount": payload.get("net_amount", 0.0),
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {
                            "value": payload.get("account_id", "1")
                        }
                    }
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=qbo_payload)
        response.raise_for_status()
        return response.json()
