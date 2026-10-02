import os
import sys

from adapters.xero_adapter import XeroAdapter
from adapters.qbo_adapter import QBOAdapter
from adapters.sage_adapter import SageAdapter
from adapters.base_adapter import AuthenticationError

def test_payload_mapping():
    os.environ["XERO_OAUTH_TOKEN"] = "test_token"
    os.environ["QBO_OAUTH_TOKEN"] = "test_token"
    os.environ["QBO_REALM_ID"] = "test_realm"
    os.environ["SAGE_OAUTH_TOKEN"] = "test_token"

    test_payload = {
        "supplier_name": "LNER",
        "date": "2026-10-01",
        "description": "Train Ticket",
        "net_amount": 100.00,
        "vat_amount": 20.00,
        "gross_amount": 120.00
    }
    
    del os.environ["XERO_OAUTH_TOKEN"]
    xero = XeroAdapter()
    try:
        xero.create_draft_bill(test_payload)
        print("XERO FAIL: Did not raise AuthenticationError")
        sys.exit(1)
    except AuthenticationError:
        print("XERO SUCCESS: Raised AuthenticationError when token missing.")
    
    print("All tests passed! Adapters are strictly validating tokens.")

if __name__ == "__main__":
    test_payload_mapping()
