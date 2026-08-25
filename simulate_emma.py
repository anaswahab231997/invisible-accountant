import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

# 1. Define the Strict JSON Schema for Gemini
class ExpenseEvaluation(BaseModel):
    transaction_id: str = Field(description="A unique ID for this transaction")
    raw_description: str = Field(description="The raw input from the user")
    amount: float = Field(description="The extracted monetary amount")
    sa103_category: str = Field(description="Official SA103 Category (e.g., OFFICE_COSTS, TRAVEL_COSTS, DISALLOWABLE, CAPITAL_ASSET)")
    hmrc_compliance_status: str = Field(description="ALLOWABLE, DISALLOWABLE, NEEDS_APPORTIONMENT, or NEEDS_CLARIFICATION")
    business_percentage: Optional[float] = Field(description="Percentage for business use (1-100), null if unknown or 100%")
    capital_or_revenue: str = Field(description="REVENUE or CAPITAL")
    emma_user_prompt: str = Field(description="If NEEDS_CLARIFICATION, NEEDS_APPORTIONMENT, or DISALLOWABLE, the friendly but strict message Emma sends back to the user.")
    bim_reference: str = Field(description="The relevant HMRC manual code, e.g., BIM37000, BIM45000")

# 2. The System Prompt from the Tax Analyst
SYSTEM_PROMPT = """
You are Emma, a Senior UK Chartered Accountant and HMRC Policy Analyst AI designed for Sole Traders (MTD for ITSA). 
Your primary function is to rigorously categorize transactions into official HMRC SA103 categories and assess their allowability based on the UK Business Income Manual (BIM).

RULES:
1. Wholly and Exclusively (BIM37000): If vague, ask for clarification.
2. Duality of Purpose (BIM37007): If mixed-use (phone, fuel), ask for business percentage.
3. Entertainment (BIM45000): Client entertainment is strictly DISALLOWABLE. Tell the user firmly.
4. Subsistence (BIM47705): Everyday lunches near work are DISALLOWABLE.

Output strictly conforming to the requested JSON schema.
"""

def evaluate_receipt(receipt_text: str):
    print(f"\n[WhatsApp Message from User]: {receipt_text}")
    
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=receipt_text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=ExpenseEvaluation,
            temperature=0.0,
        ),
    )
    
    result = json.loads(response.text)
    print("[Emma's Internal Logic]:")
    print(f"   Status: {result['hmrc_compliance_status']}")
    print(f"   Category: {result['sa103_category']} ({result['capital_or_revenue']})")
    print(f"   HMRC Manual Ref: {result['bim_reference']}")
    
    if result['emma_user_prompt']:
        print(f"[Emma's WhatsApp Reply]: {result['emma_user_prompt']}")
    else:
        print(f"[Emma's WhatsApp Reply]: All looks perfect! I've logged £{result['amount']} as {result['sa103_category']}.")
    print("-" * 60)

# 3. Simulate tricky real-world scenarios
if __name__ == "__main__":
    evaluate_receipt("Just spent £100 on Amazon")
    evaluate_receipt("Paid my O2 mobile phone bill, £60.")
    evaluate_receipt("Took a prospective client out for dinner at Nando's to discuss a contract. Cost £45.")
