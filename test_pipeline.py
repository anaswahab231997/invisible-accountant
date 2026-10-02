import pytest
import json
from models.unified_record import UnifiedFinancialRecord, TargetSystem

def test_pipeline_extraction():
    # Mocked payload from webhook / AI extraction
    payload = {
        "vendor": "Costa Coffee",
        "net_amount": 10.0,
        "vat_amount": 2.0,
        "gross_amount": 12.0,
        "transaction_date": "2026-10-02T10:00:00Z",
        "line_items": [
            {"description": "Latte", "amount": 5.0, "quantity": 1},
            {"description": "Sandwich", "amount": 7.0, "quantity": 1}
        ]
    }
    
    # Assert transaction_date exists
    assert "transaction_date" in payload
    assert payload["transaction_date"] is not None
    
    # Assert line items mathematically equal the gross amount
    line_item_sum = sum(float(item.get("amount", 0.0) * item.get("quantity", 1)) for item in payload["line_items"])
    assert round(line_item_sum, 2) == round(payload["gross_amount"], 2)

    # Verify model creation
    record = UnifiedFinancialRecord(
        amount=payload["gross_amount"],
        category="Food and Drink",
        timestamp=payload["transaction_date"],
        target_system=TargetSystem.XERO,
        sender_id="whatsapp:+447000000000",
        extra_data={"id": 1, **payload}
    )
    assert record.amount == 12.0
    assert record.timestamp == "2026-10-02T10:00:00Z"
