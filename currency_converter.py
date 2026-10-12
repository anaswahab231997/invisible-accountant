"""
Currency Converter & Normalizer for UK Accounting (HMRC VATA 1994 Sch 6 Para 11 & VAT Notice 700 §7.6)
Safeguards non-multicurrency Xero tenants by converting foreign amounts to base GBP
and applying statutory zero UK input VAT (TaxType: 'NONE') on overseas transactions.
"""
import re
from datetime import datetime
from typing import Dict, Any, Tuple

# Indicative HMRC / market selling exchange rates (Base: GBP)
# In production, this can query HMRC monthly exchange rates or European Central Bank API
DEFAULT_FX_RATES_TO_GBP = {
    "USD": 0.78,    # 1 USD = 0.78 GBP (~ 1.28 USD/GBP)
    "EUR": 0.85,    # 1 EUR = 0.85 GBP (~ 1.18 EUR/GBP)
    "CAD": 0.57,    # 1 CAD = 0.57 GBP
    "AUD": 0.51,    # 1 AUD = 0.51 GBP
    "CHF": 0.88,    # 1 CHF = 0.88 GBP
    "JPY": 0.0052,  # 1 JPY = 0.0052 GBP
    "GBP": 1.0
}

def detect_currency(text: str | None, default: str = "GBP") -> str:
    """Detects currency symbol or ISO code from vendor, memo, or message text."""
    if not text:
        return default
    
    text_upper = text.upper()
    if "$" in text or "USD" in text_upper:
        return "USD"
    if "€" in text or "EUR" in text_upper:
        return "EUR"
    if "CAD" in text_upper:
        return "CAD"
    if "AUD" in text_upper:
        return "AUD"
    if "¥" in text or "JPY" in text_upper:
        return "JPY"
    if "CHF" in text_upper:
        return "CHF"
    if "£" in text or "GBP" in text_upper:
        return "GBP"
        
    return default

def normalize_to_base_currency(
    amount: float,
    currency: str,
    vat_amount: float = 0.0,
    custom_rate: float | None = None
) -> Tuple[float, float, float, Dict[str, Any]]:
    """
    Normalizes an expense to base GBP.
    Under UK VAT law (VATA 1994 s88, VAT Notice 700 §7.6):
    - Foreign transactions cannot claim UK input VAT (TaxType must be 'NONE', VAT amount = 0.0).
    - Returns: (base_gross, base_vat, base_net, fx_metadata)
    """
    curr = currency.upper().strip()
    if curr == "GBP":
        net = round(amount - vat_amount, 2)
        return (round(amount, 2), round(vat_amount, 2), net, {"currency": "GBP", "rate": 1.0})
    
    # Foreign currency detected
    rate = custom_rate if custom_rate is not None else DEFAULT_FX_RATES_TO_GBP.get(curr, 0.78)
    base_gross = round(amount * rate, 2)
    
    # Statutory rule: No UK input VAT reclaimable on overseas foreign transactions
    base_vat = 0.0
    base_net = base_gross
    
    fx_metadata = {
        "original_currency": curr,
        "original_amount": round(amount, 2),
        "original_vat": round(vat_amount, 2),
        "exchange_rate": rate,
        "converted_currency": "GBP",
        "tax_type_override": "NONE",
        "annotation": f"[{amount:.2f} {curr} converted @ {rate:.4f} GBP/{curr}]"
    }
    
    return (base_gross, base_vat, base_net, fx_metadata)
