import httpx
from .base_adapter import SubmissionAdapter
from models.unified_record import UnifiedFinancialRecord

class QBOAdapter(SubmissionAdapter):
    async def submit(self, record: UnifiedFinancialRecord, identity: dict) -> dict:
        token = self._check_token("QBO_OAUTH_TOKEN")
        realm_id = self._check_token("QBO_REALM_ID")
        
        payload = record.extra_data or {}
        
        qbo_payload = {
            "Line": [
                {
                    "DetailType": "AccountBasedExpenseLineDetail",
                    "Amount": payload.get("net_amount", record.amount),
                    "AccountBasedExpenseLineDetail": {
                        "AccountRef": {"value": "1"}
                    }
                }
            ],
            "TxnTaxDetail": {
                "TotalTax": payload.get("vat_amount", 0.0)
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/bill", json=qbo_payload, headers=headers)
            response.raise_for_status()
            return response.json()
