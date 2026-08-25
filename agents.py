import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")
client = genai.Client(api_key=API_KEY)

breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

HMRC_CATEGORIES = [
    "Cost of goods sold",
    "Construction industry costs",
    "Staff costs",
    "Travel costs",
    "Premises running costs",
    "Repairs and maintenance",
    "Admin costs",
    "Advertising and marketing",
    "Interest on loans",
    "Bank and financial charges",
    "Professional fees",
    "Depreciation and loss of assets",
    "Other expenses"
]

class ExpenseCategorization(BaseModel):
    reasoning_step_1_amount_and_vendor: str = Field(description="Extract the exact numerical amount and vendor name from the text.")
    reasoning_step_2_nature_of_expense: str = Field(description="What exactly was purchased, and what is its business purpose?")
    reasoning_step_3_hmrc_rules: str = Field(description="Analyze the expense against the UK HMRC Sole Trader rules to determine if it is allowable or has duality of purpose.")
    reasoning_step_4_final_determination: str = Field(description="Determine the appropriate HMRC category and whether auditor clarification is needed.")
    vendor: str = Field(description="The name of the shop, person, or business the money was paid to.")
    amount: float = Field(description="The monetary amount (as a float).")
    category: str = Field(description="Map the expense to exactly ONE of the official HMRC MTD ITSA categories.")
    is_ambiguous: bool = Field(description="Set to true if this expense might not be wholly and exclusively for business, or is entertainment.")
    auditor_question: str = Field(description="If is_ambiguous is true, what short question should the Auditor ask?")

def _call_gemini(prompt: str):
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ExpenseCategorization,
        )
    )
    return json.loads(response.text)

def process_expense_message(raw_message: str, turn_count: int = 1):
    prompt = f"""
    You are Emma, an Invisible Accountant AI for UK Sole Traders.
    Your tone is "casual formal" (like a real WhatsApp text from a professional human). 
    - Use contractions (I'll, doesn't).
    - NEVER start with "Hi" or "Hello" or end with a signature ("Cheers, Emma")—this is an ongoing chat.
    - Be direct, empathetic, and natural. Do not sound robotic.
    
    CRITICAL CONSTRAINT: Your `auditor_question` must NEVER exceed 3 sentences. Keep it brief.

    --- YOUR ACCOUNTING BRAIN (HMRC SOLE TRADER RULES) ---
    1. The Golden Rule: Expenses must be "wholly and exclusively" for the purposes of the trade.
    2. Duality of Purpose: If an expense has both personal and business use (like a mobile phone, broadband, or vehicle), it must be apportioned. Identify personal vs business split.
    3. Client Entertainment: Taking clients out for lunch/dinner or buying event tickets is STRICTLY NOT ALLOWABLE for tax relief for UK sole traders, even if business was discussed. It must be flagged.
    4. Commuting: Regular travel from home to a permanent workplace is not allowable.
    5. Use of home as office: Claiming a portion of home bills is allowable but requires identifying hours worked or the exact proportion of space used.
    6. Clothing: Everyday wear (even suits) is not allowable. Only protective clothing, uniforms with logos, or costumes for actors are allowable.
    -------------------------------------------------------
    
    --- FEW-SHOT EXAMPLES ---
    Example 1:
    User: "Bought a new suit for client meetings, £200 at Marks & Spencer."
    Analysis: Clothing is everyday wear. Not allowable.
    is_ambiguous: true
    auditor_question: "I've noted the £200 at Marks & Spencer. Unfortunately, HMRC doesn't allow claims for everyday clothing like suits, even if bought specifically for work, as they have a 'duality of purpose'. I'll keep this recorded but we can't offset it against tax."

    Example 2:
    User: "Paid £50 for O2 mobile bill."
    Analysis: Duality of purpose. Mobile phones are often used personally too.
    is_ambiguous: true
    auditor_question: "Got the £50 O2 bill. Do you use this phone for personal calls too? If so, roughly what percentage is for business?"
    
    Example 3:
    User: "£100 for timber from B&Q."
    Analysis: Wholly for trade. Construction industry costs / Cost of goods sold.
    is_ambiguous: false
    auditor_question: ""
    -------------------------------------------------------
    
    A sole trader has just sent you a message about an expense.
    
    <expense_message>
    {raw_message}
    </expense_message>
    
    Extract the entities based strictly on the text inside the <expense_message> tags.
    If the expense violates HMRC rules (like client lunches), set `is_ambiguous` to true and ask a concise clarification question or inform them of the rule casually.
    """

    try:
        # Wrap the API call in our Circuit Breaker
        result = breaker.call(_call_gemini, prompt)
        
        # Human-in-the-loop limit logic (2 turns max)
        if turn_count >= 2 and result.get("is_ambiguous"):
            print("INFO: Turn limit reached. Forcing category to 'Other expenses'.")
            result["is_ambiguous"] = False
            result["category"] = "Other expenses"
            
        return result
        
    except CircuitBreakerOpenException:
        print("Circuit is OPEN. Executing Fallback model.")
        # Fallback simulated response
        return {
            "vendor": "Pending",
            "amount": 0.0,
            "category": "Other expenses",
            "is_ambiguous": True,
            "auditor_question": "Our AI is currently overloaded. We have queued your receipt for processing shortly."
        }
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise e
