import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from google.genai import types
import sys

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
client = genai.Client()

class ExpenseEvaluation(BaseModel):
    transaction_id: str = Field(description="A unique ID")
    raw_description: str = Field(description="The raw input")
    amount: float = Field(description="The extracted amount")
    sa103_category: str = Field(description="Official SA103 Category")
    hmrc_compliance_status: str = Field(description="ALLOWABLE, DISALLOWABLE, NEEDS_APPORTIONMENT, or NEEDS_CLARIFICATION")
    business_percentage: Optional[float] = Field(description="Percentage for business use (1-100), null if unknown")
    capital_or_revenue: str = Field(description="REVENUE or CAPITAL")
    emma_user_prompt: str = Field(description="The message Emma sends back")
    bim_reference: str = Field(description="HMRC manual code, e.g., BIM37000")

SYSTEM_PROMPT = """
You are Emma, a Senior UK Chartered Accountant AI for Sole Traders (MTD for ITSA). 
Categorize into SA103 categories based on the Business Income Manual (BIM).
1. Wholly and Exclusively (BIM37000): If vague, ask for clarification.
2. Duality of Purpose (BIM37007): If mixed-use, ask for percentage.
3. Entertainment (BIM45000): Client entertainment is strictly DISALLOWABLE. Reject firmly.
Output strictly conforming to the requested JSON schema.
"""

def evaluate_receipt(receipt_text: str):
    print(f"\n[WhatsApp Message]: {receipt_text}")
    
    response = client.models.generate_content(
        model='gemini-3.1-flash',
        contents=receipt_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ExpenseEvaluation,
            temperature=0.0,
        ),
    )
    
    result = json.loads(response.text)
    print("[Emma Internal]:")
    print(f"   Status: {result['hmrc_compliance_status']}")
    print(f"   Category: {result['sa103_category']} ({result['capital_or_revenue']})")
    print(f"   Ref: {result['bim_reference']}")
    
    if result['emma_user_prompt']:
        print(f"[Emma Reply]: {result['emma_user_prompt']}")
    else:
        print(f"[Emma Reply]: All looks perfect! Logged £{result['amount']} as {result['sa103_category']}.")
    print("-" * 60)

if __name__ == "__main__":
    evaluate_receipt("Just spent £100 on Amazon")
    evaluate_receipt("Paid my O2 mobile phone bill, £60.")
    evaluate_receipt("Took a prospective client out for dinner at Nando's. Cost £45.")
