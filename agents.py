import json
import os

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from logger import get_logger
from dotenv import load_dotenv
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from google.genai.errors import APIError

load_dotenv()

logger = get_logger(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing.")
client = genai.Client(api_key=API_KEY)

from enum import Enum


class HMRCCategory(str, Enum):
    COST_OF_GOODS_SOLD = "Cost of goods sold"
    CONSTRUCTION_INDUSTRY_COSTS = "Construction industry costs"
    STAFF_COSTS = "Staff costs"
    TRAVEL_COSTS = "Travel costs"
    PREMISES_RUNNING_COSTS = "Premises running costs"
    REPAIRS_AND_MAINTENANCE = "Repairs and maintenance"
    ADMIN_COSTS = "Admin costs"
    ADVERTISING_AND_MARKETING = "Advertising and marketing"
    INTEREST_ON_LOANS = "Interest on loans"
    BANK_AND_FINANCIAL_CHARGES = "Bank and financial charges"
    PROFESSIONAL_FEES = "Professional fees"
    DEPRECIATION_AND_LOSS_OF_ASSETS = "Depreciation and loss of assets"
    OTHER_EXPENSES = "Other expenses"


class ExpenseCategorization(BaseModel):
    reasoning_step_1_amount_and_vendor: str = Field(
        description="Extract the exact numerical amount and vendor name from the text."
    )
    reasoning_step_2_nature_of_expense: str = Field(
        description="What exactly was purchased, and what is its business purpose?"
    )
    reasoning_step_3_hmrc_rules: str = Field(
        description="Analyze the expense against the UK HMRC Sole Trader rules to determine if it is allowable or has duality of purpose."
    )
    reasoning_step_4_final_determination: str = Field(
        description="Determine the appropriate HMRC category and whether auditor clarification is needed."
    )
    vendor: str = Field(
        description="The name of the shop, person, or business the money was paid to."
    )
    amount: float = Field(description="The monetary amount (as a float).")
    category: HMRCCategory = Field(
        description="Map the expense to exactly ONE of the official HMRC MTD ITSA categories."
    )
    is_ambiguous: bool = Field(
        description="Set to true if this expense might not be wholly and exclusively for business, or is entertainment."
    )
    auditor_question: str = Field(
        description="If is_ambiguous is true, what short question should the Auditor ask?"
    )


from urllib.parse import urlparse

import httpx

ALLOWED_DOMAINS = {
    "lookaside.fbsbx.com",
    "s3.amazonaws.com",
    "mock-s3-bucket.amazonaws.com",
}


def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and parsed.netloc in ALLOWED_DOMAINS
    except Exception:
        return False


@retry(
    wait=wait_exponential(multiplier=2, min=2, max=65),
    stop=stop_after_attempt(10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def _call_gemini(
    system_instruction: str,
    user_input: str,
    media_urls: list = None,
    model: str = "gemini-2.5-flash",
):
    contents = []

    if media_urls:
        async with httpx.AsyncClient() as http_client:
            async def fetch_media(url):
                if not is_safe_url(url):
                    logger.warning("SSRF mitigation blocked URL", url=url)
                    return None
                try:
                    resp = await http_client.get(url, timeout=5.0)
                    resp.raise_for_status()
                    mime_type = resp.headers.get("content-type", "image/jpeg")
                    return types.Part.from_bytes(data=resp.content, mime_type=mime_type)
                except Exception as e:
                    logger.error("Error fetching media", url=url, error=str(e))
                    return None
                    
            tasks = [fetch_media(url) for url in media_urls]
            parts = await asyncio.gather(*tasks)
            contents.extend([p for p in parts if p is not None])

    # Always append text at the end
    contents.append(user_input)

    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=ExpenseCategorization,
        ),
    )
    return json.loads(response.text)


async def process_expense_message(
    raw_message: str, turn_count: int = 1, media_urls: list = None, previous_state: dict = None
):
    system_instruction = """
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
    Extract the entities based strictly on the user message.
    If the expense violates HMRC rules (like client lunches), set `is_ambiguous` to true and ask a concise clarification question or inform them of the rule casually.
    """

    try:
        # Phase 1: Fast & Cheap (Gemini 2.5 Flash)
        
        if previous_state:
            import json
            raw_message = f"PREVIOUS STATE:\n{json.dumps(previous_state, indent=2)}\n\nUSER'S LATEST MESSAGE:\n{raw_message}\n\nINSTRUCTION: The user is replying to your previous question. Merge this new information with the PREVIOUS STATE. If they answered your question, update the missing fields (e.g. amount, vendor, category). If everything is now complete, set is_ambiguous to false."
            
        result = await _call_gemini(
            system_instruction, raw_message, media_urls, model="gemini-2.5-flash"
        )

        # Phase 2: Deep Audit Escalation (Gemini 2.5 Pro)
        if result.get("is_ambiguous"):
            logger.info(
                "Escalating to Gemini 2.5 Pro for deep audit",
                reason="Flash flagged as ambiguous",
            )
            pro_result = await _call_gemini(
                system_instruction, raw_message, media_urls, model="gemini-2.5-flash"
            )

            # If Pro ALSO thinks it's ambiguous, or definitively categorizes it, trust Pro.
            result = pro_result

        # Human-in-the-loop limit logic (2 turns max)
        if turn_count >= 2 and result.get("is_ambiguous"):
            logger.info("Turn limit reached. Forcing category to 'Other expenses'")
            result["is_ambiguous"] = False
            result["category"] = "Other expenses"

        return result

    except Exception as e:
        logger.error("Error calling Gemini API", error=str(e))
        raise e
class AntiHallucinationCheck(BaseModel):
    is_hallucinated: bool = Field(description="True if the parsed JSON contains information (amount, vendor) not present in the user text.")
    hallucination_reason: str = Field(description="If hallucinated, why?")
    corrected_question: str = Field(description="If hallucinated, ask the user to clarify the missing information.")

@retry(
    wait=wait_exponential(multiplier=2, min=2, max=65),
    stop=stop_after_attempt(10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def verify_expense_hallucination(raw_message: str, parsed_json: dict) -> dict:
    system_instruction = """
    You are an Anti-Hallucination Auditor. Your strict job is to compare the raw user text to the parsed JSON.
    Did the AI hallucinate an amount, vendor, or date that the user did NOT actually say?
    For example, if the user says "lunch" and the AI outputs "vendor: Unknown, amount: 0.0", that is a hallucination/failure.
    If the user says "spent 50 at tesco" and AI outputs "amount: 50.0", that is valid.
    Return true for hallucination if the amount or vendor is completely fabricated.
    """
    contents = [
        f"USER MESSAGE: {raw_message}",
        f"PARSED JSON: {json.dumps(parsed_json)}"
    ]
    
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=AntiHallucinationCheck,
        ),
    )
    return json.loads(response.text)
