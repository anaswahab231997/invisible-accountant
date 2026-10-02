from adapters.base_adapter import SubmissionAdapter
from adapters.xero_adapter import XeroAdapter
from models.unified_record import UnifiedFinancialRecord, TargetSystem
from typing import Dict

class UniversalAdapter:
    def __init__(self):
        self._adapters: Dict[TargetSystem, SubmissionAdapter] = {
            TargetSystem.XERO: XeroAdapter()
        }
        
    async def dispatch(self, record: UnifiedFinancialRecord, identity: dict) -> dict:
        adapter = self._adapters.get(record.target_system)
        if not adapter:
            raise ValueError(f"No adapter configured for target system: {record.target_system}")
        return await adapter.submit(record, identity)

    async def get_accounts(self, target_system: TargetSystem, identity: dict) -> list:
        adapter = self._adapters.get(target_system)
        if adapter:
            return await adapter.get_accounts(identity)
        return []

    async def get_tax_rates(self, target_system: TargetSystem, identity: dict) -> list:
        adapter = self._adapters.get(target_system)
        if adapter:
            return await adapter.get_tax_rates(identity)
        return []
