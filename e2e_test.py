import asyncio
from agents import process_expense_message

async def run_test():
    message = "Just spent 150 on some new tools for the site from Screwfix."
    
    # Simulate dynamic payload pulled from Xero GET Accounts and GET TaxRates
    dynamic_enums = {
        "accounts": [
            {"Code": "310", "Name": "Cost of Goods Sold"},
            {"Code": "400", "Name": "Advertising"},
            {"Code": "429", "Name": "General Expenses"},
            {"Code": "720", "Name": "Light, Power, Heating"}
        ],
        "tax_rates": [
            {"TaxType": "20% (VAT on Expenses)", "Name": "20% VAT"},
            {"TaxType": "Zero Rated Expenses", "Name": "0%"},
            {"TaxType": "Exempt", "Name": "Exempt"}
        ]
    }
    
    result = await process_expense_message(message, turn_count=1, media_urls=[], dynamic_enums=dynamic_enums)
    import json
    print(json.dumps(result, indent=2))

asyncio.run(run_test())
