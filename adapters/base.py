import abc
from typing import Dict, Any

class AccountingAdapter(abc.ABC):
    @abc.abstractmethod
    def get_authorization_url(self) -> str:
        pass

    @abc.abstractmethod
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        pass

    @abc.abstractmethod
    def create_draft_bill(self, access_token: str, tenant_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        pass
