import asyncio
import json
from agents import process_expense_message

category_map = {
    "Turnover / Sales Income": "turnover",
    "Cost of goods sold": "costOfGoods",
    "Construction industry subcontractors": "constructionIndustryScheme",
    "Wages, salaries and other staff costs": "staffCosts",
    "Car, van and travel expenses": "travelCosts",
    "Rent, rates, power and insurance costs": "premisesRunningCosts",
    "Repairs and maintenance of property and equipment": "maintenanceCosts",
    "Phone, fax, stationery and other office costs": "adminCosts",
    "Advertising and business entertainment costs": "advertisingCosts",
    "Interest on bank and other loans": "interest",
    "Bank, credit card and other financial charges": "financialCharges",
    "Irrecoverable debts written off": "badDebt",
    "Accountancy, legal and other professional fees": "professionalFees",
    "Depreciation and loss/profit on sale of assets": "depreciation",
    "Other business expenses": "other"
}

async def run_review():
    test_cases = [
        "Just paid £300 to a subcontractor for help on the plumbing job.",
        "Bought £50 worth of Facebook Ads for my business.",
        "Paid £1200 for a new MacBook Pro to use for accounting and quotes."
    ]
    
    print("=== DRAFT BILL PIPELINE TEST FOR ACCOUNTANT REVIEW ===")
    for msg in test_cases:
        print(f"\n[Raw Receipt Text]: {msg}")
        result = await process_expense_message(msg, media_urls=[])
        internal_category = result.get("category", "Other business expenses")
        mapped_key = category_map.get(internal_category, "other")
        
        draft_bill = {
            "Vendor": result.get("vendor", "Unknown"),
            "Amount": result.get("amount", 0.0),
            "Internal_AI_Category": internal_category,
            "Mapped_API_Ledger_Code": mapped_key,
            "Requires_Accountant_Audit": result.get("is_ambiguous", False)
        }
        
        print("[Generated Draft Bill]:")
        print(json.dumps(draft_bill, indent=2))
        print("-" * 50)
        await asyncio.sleep(5)

if __name__ == '__main__':
    asyncio.run(run_review())
