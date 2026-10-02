import httpx
from .base_adapter import SubmissionAdapter
from models.unified_record import UnifiedFinancialRecord

class SageAdapter(SubmissionAdapter):
    async def submit(self, record: UnifiedFinancialRecord, identity: dict) -> dict:
        token = self._check_token("SAGE_OAUTH_TOKEN")
        
        payload = record.extra_data or {}
        
        sage_payload = {
            "purchase_invoice": {
                "contact_id": "generic_contact_id",
                "date": payload.get("date"),
                "due_date": payload.get("date"),
                "invoice_lines": [
                    {
                        "description": payload.get("description", "Expense"),
                        "ledger_account_id": "generic_ledger_id",
                        "quantity": 1,
                        "unit_price": payload.get("net_amount", record.amount),
                        "net_amount": payload.get("net_amount", record.amount),
                        "tax_amount": payload.get("vat_amount", 0.0)
                    }
                ]
            }
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.accounting.sage.com/v3.1/purchase_invoices", json=sage_payload, headers=headers)
            response.raise_for_status()
            return response.json()
