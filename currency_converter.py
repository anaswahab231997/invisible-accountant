"""
Currency Converter & Normalizer for UK Accounting (HMRC VATA 1994 s8, Sch 6 Para 11 & VAT Notice 700 §7.6)
Safeguards non-multicurrency Xero tenants by converting foreign amounts to base GBP,
differentiating B2B electronic services subject to the UK Reverse Charge (VATA 1994 s8) from
general foreign expenditures (No UK VAT / NONE).
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

# Major international digital service / cloud / SaaS providers subject to UK Reverse Charge
OVERSEAS_REVERSE_CHARGE_PROVIDERS = [
    "aws", "amazon web services", "google", "openai", "chatgpt", "adobe",
    "microsoft", "zoom", "slack", "github", "gitlab", "atlassian", "jira",
    "digitalocean", "cloudflare", "stripe", "hubspot", "mailchimp", "heroku",
    "notion", "figma", "dropbox", "godaddy", "namecheap", "meta", "facebook ads",
    "linkedin", "canva", "twilio", "mongodb", "datadog", "vercel", "sentry",
    "envato", "shutterstock", "jetbrains", "anthropic"
]

# Service categories / keywords subject to Reverse Charge under VATA 1994 s8
REVERSE_CHARGE_SERVICE_KEYWORDS = [
    "software", "saas", "cloud", "hosting", "subscription", "api", "license",
    "advertising", "ad spend", "marketing", "consulting", "web hosting",
    "domain", "server", "telecom"
]

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

def is_overseas_reverse_charge_candidate(
    vendor: str | None = None, 
    description: str | None = None, 
    category: str | None = None
) -> bool:
    """
    Identifies B2B electronic, cloud, telecommunication, SaaS, or professional services
    supplied by an overseas provider subject to UK Reverse Charge under VATA 1994 s8.
    """
    corpus = f"{vendor or ''} {description or ''} {category or ''}".lower()
    if any(provider in corpus for provider in OVERSEAS_REVERSE_CHARGE_PROVIDERS):
        return True
    if any(kw in corpus for kw in REVERSE_CHARGE_SERVICE_KEYWORDS):
        return True
    return False

def normalize_to_base_currency(
    amount: float,
    currency: str,
    vat_amount: float = 0.0,
    custom_rate: float | None = None,
    vendor: str | None = None,
    description: str | None = None,
    category: str | None = None
) -> Tuple[float, float, float, Dict[str, Any]]:
    """
    Normalizes an expense to base GBP.
    Under UK VAT law (VATA 1994 s8, Sch 6 Para 11 & VAT Notice 700 §7.6):
    - Identifies B2B electronic services subject to Reverse Charge (TaxType: 'REVERSECHARGES').
    - Distinguishes general overseas expenditures (TaxType: 'NONE').
    - Returns: (base_gross, base_vat, base_net, fx_metadata)
    """
    curr = currency.upper().strip()
    if curr == "GBP":
        net = round(amount - vat_amount, 2)
        return (round(amount, 2), round(vat_amount, 2), net, {"currency": "GBP", "rate": 1.0, "is_reverse_charge": False})
    
    rate = custom_rate if custom_rate is not None else DEFAULT_FX_RATES_TO_GBP.get(curr, 0.78)
    base_gross = round(amount * rate, 2)
    base_vat = 0.0
    base_net = base_gross
    
    is_rc = is_overseas_reverse_charge_candidate(vendor, description, category)
    tax_type_override = "REVERSECHARGES" if is_rc else "NONE"
    
    fx_metadata = {
        "original_currency": curr,
        "original_amount": round(amount, 2),
        "original_vat": round(vat_amount, 2),
        "exchange_rate": rate,
        "converted_currency": "GBP",
        "is_reverse_charge": is_rc,
        "tax_type_override": tax_type_override,
        "annotation": (
            f"[{amount:.2f} {curr} converted @ {rate:.4f} GBP/{curr} - "
            f"{'UK Reverse Charge (VATA 1994 s8)' if is_rc else 'Overseas Expenditure (No UK VAT)'}]"
        )
    }
    
    return (base_gross, base_vat, base_net, fx_metadata)
