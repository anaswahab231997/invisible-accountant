import os
import json
import httpx
from datetime import datetime, timezone
import asyncpg
from db import get_connection
from aes_gcm_security import TokenEncryptionEngine

class AccountingClient:
    def __init__(self, workspace_id: str, provider: str = "XERO"):
        self.workspace_id = workspace_id
        self.provider = provider
        self.master_key = os.getenv("ENCRYPTION_MASTER_KEY_B64")
        self.engine = TokenEncryptionEngine(self.master_key) if self.master_key else None

    def _decrypt(self, payload: str) -> str:
        if not self.engine or not payload.startswith("{"):
            return payload
        return self.engine.decrypt_tokens(json.loads(payload), associated_data=self.workspace_id)

    def _encrypt(self, payload: str) -> str:
        if not self.engine:
            return payload
        return json.dumps(self.engine.encrypt_tokens(payload, associated_data=self.workspace_id))

    async def get_valid_token(self) -> dict:
        async with get_connection() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    '''
                    SELECT * FROM accounting_connections 
                    WHERE workspace_id = $1 AND provider = $2 
                    FOR UPDATE SKIP LOCKED
                    ''',
                    self.workspace_id, self.provider
                )
                if not row:
                    raise Exception(f"No {self.provider} connection found for workspace {self.workspace_id}")

                expires_at = row["expires_at"]
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                # Check if it expires in less than 5 minutes
                time_left = (expires_at - datetime.now(timezone.utc)).total_seconds()
                
                access_token = self._decrypt(row["access_token"])
                refresh_token = self._decrypt(row["refresh_token"])
                tenant_id = row["provider_tenant_id"]

                if time_left < 300:
                    # Token is expired or about to expire, refresh it
                    new_tokens = await self._refresh_xero_token(refresh_token)
                    
                    access_token = new_tokens["access_token"]
                    new_refresh = new_tokens.get("refresh_token", refresh_token)
                    expires_in = new_tokens.get("expires_in", 1800)
                    
                    await conn.execute(
                        '''
                        UPDATE accounting_connections 
                        SET access_token = $1, refresh_token = $2, expires_at = NOW() + (INTERVAL '1 second' * $3), updated_at = NOW()
                        WHERE id = $4
                        ''',
                        self._encrypt(access_token), 
                        self._encrypt(new_refresh),
                        expires_in,
                        row["id"]
                    )
                
                return {
                    "access_token": access_token,
                    "tenant_id": tenant_id
                }

    async def _refresh_xero_token(self, refresh_token: str) -> dict:
        client_id = os.getenv("XERO_CLIENT_ID")
        client_secret = os.getenv("XERO_CLIENT_SECRET")
        base_url = os.getenv("XERO_BASE_URL", "https://identity.xero.com")
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{base_url}/connect/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if resp.status_code != 200:
                raise Exception(f"Failed to refresh Xero token: {resp.text}")
            return resp.json()

    async def create_draft_bill(self, payload: dict):
        creds = await self.get_valid_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.xero.com/api.xro/2.0/Invoices",
                json=payload,
                headers={
                    "Authorization": f"Bearer {creds['access_token']}",
                    "Xero-Tenant-Id": creds["tenant_id"],
                    "Accept": "application/json"
                }
            )
            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to create draft bill: {resp.text}")
            return resp.json()

    async def upload_attachment(self, invoice_id: str, filename: str, file_bytes: bytes, mime_type: str = "image/jpeg"):
        creds = await self.get_valid_token()
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"https://api.xero.com/api.xro/2.0/Invoices/{invoice_id}/Attachments/{filename}",
                content=file_bytes,
                headers={
                    "Authorization": f"Bearer {creds['access_token']}",
                    "Xero-Tenant-Id": creds["tenant_id"],
                    "Content-Type": mime_type
                }
            )
            if resp.status_code not in (200, 201):
                raise Exception(f"Failed to upload attachment: {resp.text}")
            return resp.json()
