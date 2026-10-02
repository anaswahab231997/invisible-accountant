from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

class TargetSystem(str, Enum):
    HMRC = "HMRC"
    XERO = "XERO"

class UnifiedFinancialRecord(BaseModel):
    amount: float
    category: Optional[str] = None
    timestamp: str
    target_system: TargetSystem
    sender_id: str
    extra_data: Optional[Dict[str, Any]] = None
