import httpx
from .base_adapter import SubmissionAdapter
from models.unified_record import UnifiedFinancialRecord

class XeroAdapter(SubmissionAdapter):

    async def get_accounts(self, identity: dict) -> dict:
        token = identity.get("access_token")
        tenant_id = identity.get("xero_tenant_id")
        if not token or not tenant_id:
            raise ValueError("Missing access_token or xero_tenant_id in identity")
            
        headers = {
            "Authorization": f"Bearer {token}",
            "xero-tenant-id": tenant_id,
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.xero.com/api.xro/2.0/Accounts", headers=headers)
            resp.raise_for_status()
            return resp.json().get("Accounts", [])

    async def get_tax_rates(self, identity: dict) -> dict:
        token = identity.get("access_token")
        tenant_id = identity.get("xero_tenant_id")
        if not token or not tenant_id:
            raise ValueError("Missing access_token or xero_tenant_id in identity")
            
        headers = {
            "Authorization": f"Bearer {token}",
            "xero-tenant-id": tenant_id,
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.xero.com/api.xro/2.0/TaxRates", headers=headers)
            resp.raise_for_status()
            return resp.json().get("TaxRates", [])

    async def submit(self, record: UnifiedFinancialRecord, identity: dict) -> dict:
        token = identity.get("access_token")
        if not token:
            raise ValueError("Missing access_token in identity")
            
        tenant_id = identity.get("xero_tenant_id")
        if not tenant_id:
            raise ValueError("Missing xero_tenant_id in identity")
        
        # We assume extra_data has supplier_name, date, line_items
        payload = record.extra_data or {}
        
        line_items_data = payload.get("line_items", [])
        if not line_items_data:
            gross = float(payload.get("gross_amount") or payload.get("amount") or 0.0)
            net = float(payload.get("net_amount") or gross)
            line_items_data = [{
                "description": payload.get("category", "General Expense"),
                "quantity": 1,
                "unit_amount": net,
                "tax_amount": gross - net
            }]
        
        line_items = []
        for item in line_items_data:
            business_percentage = float(item.get("business_percentage", 100.0))
            multiplier = business_percentage / 100.0
            
            unit_amount = float(item.get("unit_amount") or item.get("net_amount") or item.get("amount") or 0.0)
            tax_amount = float(item.get("tax_amount") or item.get("vat_amount") or 0.0)
            
            # Line 1: Business Portion
            bus_item = {}
            if "description" in item: bus_item["Description"] = item["description"]
            if "quantity" in item: bus_item["Quantity"] = item["quantity"]
            bus_item["UnitAmount"] = unit_amount * multiplier
            tax_code = item.get("tax_code") or payload.get("tax_code")
            if tax_code: bus_item["TaxType"] = tax_code
            bus_item["TaxAmount"] = tax_amount * multiplier
            bus_item["AccountCode"] = item.get("account_code") or payload.get("account_code") or "8520"
            line_items.append(bus_item)

            # Line 2: Personal Portion
            if business_percentage < 100.0:
                personal_multiplier = (100.0 - business_percentage) / 100.0
                pers_item = {}
                if "description" in item: pers_item["Description"] = f"{item['description']} (Personal)"
                if "quantity" in item: pers_item["Quantity"] = item["quantity"]
                pers_item["UnitAmount"] = (unit_amount * personal_multiplier) + (tax_amount * personal_multiplier)
                pers_item["TaxType"] = "NONE"
                pers_item["AccountCode"] = "Owner's Drawings"
                line_items.append(pers_item)
                
        cis_amount = float(payload.get("cis_deduction_amount") or 0.0)
        if cis_amount > 0:
            line_items.append({
                "Description": "CIS Deduction",
                "UnitAmount": -cis_amount,
                "Quantity": 1,
                "AccountCode": "CIS Liability"
            })
        
        doc_type = payload.get("transaction_type") or payload.get("document_type") or payload.get("type", "EXPENSE")
        gross_amount = float(payload.get("gross_amount") or payload.get("amount") or 0.0)
        
        is_credit = gross_amount < 0
        invoice_type = "ACCPAYCREDIT" if is_credit else ("ACCREC" if doc_type.upper() == "INCOME" else "ACCPAY")
        
        # When creating a CreditNote, amounts are generally positive in the payload.
        # But we'll leave them as they were computed, Xero might expect them negative or positive.
        
        root_key = "CreditNotes" if is_credit else "Invoices"

        invoice_obj = {
            "Type": invoice_type,
            "Contact": {"Name": payload.get("supplier_name", payload.get("vendor", "Unknown"))},
            "Date": payload.get("date") or payload.get("transaction_date"),
            "DueDate": payload.get("due_date") or payload.get("date") or payload.get("transaction_date"),
            "LineAmountTypes": "Exclusive",
            "Status": "DRAFT",
            "LineItems": line_items
        }
        
        if payload.get("invoice_number"):
            invoice_obj["InvoiceNumber"] = payload.get("invoice_number")
        if payload.get("memo"):
            invoice_obj["Reference"] = payload.get("memo")
        if payload.get("currency"):
            invoice_obj["CurrencyCode"] = payload.get("currency")
            
        xero_payload = {
            root_key: [invoice_obj]
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "xero-tenant-id": tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            endpoint_url = f"https://api.xero.com/api.xro/2.0/{root_key}"
            response = await client.post(endpoint_url, json=xero_payload, headers=headers)
            response.raise_for_status()
            resp_data = response.json()
            
            id_field = "CreditNoteID" if is_credit else "InvoiceID"
            invoice_id = resp_data[root_key][0][id_field]
            
            media_urls_str = payload.get("media_urls")
            if media_urls_str:
                import json
                import os
                import asyncio
                import boto3
                import re
                from urllib.parse import urlparse
                try:
                    media_urls = json.loads(media_urls_str) if isinstance(media_urls_str, str) else media_urls_str
                except:
                    media_urls = []
                for media_url in media_urls:
                    file_name = f"{invoice_id}_receipt.jpg"
                    content_type = "image/jpeg"
                    file_content = None
                    if re.match(r"^s3://", media_url):
                        parsed = urlparse(media_url)
                        bucket = parsed.netloc
                        key = parsed.path.lstrip("/")
                        s3 = boto3.client("s3")
                        try:
                            obj = await asyncio.to_thread(s3.get_object, Bucket=bucket, Key=key)
                            file_content = await asyncio.to_thread(lambda: obj['Body'].read())
                            content_type = obj.get("ContentType", "image/jpeg")
                            ext = "pdf" if "pdf" in content_type else "jpg"
                            file_name = f"{invoice_id}_receipt.{ext}"
                        except Exception as e:
                            pass
                    elif media_url.startswith("http"):
                        try:
                            auth = None
                            if "twilio" in media_url.lower():
                                twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                                twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
                                if twilio_sid and twilio_token:
                                    auth = (twilio_sid, twilio_token)
                            
                            media_resp = await client.get(media_url, auth=auth)
                            if media_resp.status_code == 200:
                                file_content = media_resp.content
                                content_type = media_resp.headers.get("Content-Type", "image/jpeg")
                                ext = "pdf" if "pdf" in content_type else "jpg"
                                file_name = f"{invoice_id}_receipt.{ext}"
                        except Exception as e:
                            pass
                    
                    if file_content:
                        attach_headers = {
                            "Authorization": f"Bearer {token}",
                            "xero-tenant-id": tenant_id,
                            "Content-Type": content_type
                        }
                        attach_url = f"https://api.xero.com/api.xro/2.0/{root_key}/{invoice_id}/Attachments/{file_name}"
                        await client.post(attach_url, content=file_content, headers=attach_headers)
                        
            return resp_data
