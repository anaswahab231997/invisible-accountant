import os
from abc import ABC, abstractmethod
from models.unified_record import UnifiedFinancialRecord

class AuthenticationError(Exception):
    pass

class BaseAdapter:
    def _check_token(self, token_env_var: str):
        token = os.getenv(token_env_var)
        if not token:
            raise AuthenticationError(f"Missing OAuth 2.0 token in {token_env_var}. No fallback allowed.")
        return token

class SubmissionAdapter(ABC, BaseAdapter):
    @abstractmethod
    async def submit(self, record: UnifiedFinancialRecord, identity: dict) -> dict:
        pass

    async def get_accounts(self, identity: dict) -> list:
        return []

    async def get_tax_rates(self, identity: dict) -> list:
        return []
