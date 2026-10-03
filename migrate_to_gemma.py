import os
import re

path = r'C:\Antigravity\UK MTD\invisible-accountant\agents.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace imports and client initialization
import_replacement = '''
from huggingface_hub import AsyncInferenceClient
from huggingface_hub.errors import HfHubHTTPError

API_KEY = os.getenv("API_KEY") # Keep existing API keys
HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = AsyncInferenceClient(model="google/gemma-4-31B-it", token=HF_TOKEN)
'''
content = re.sub(r'from google import genai\nfrom google\.genai import types\n.*?client = genai\.Client\(api_key=API_KEY\)', import_replacement.strip(), content, flags=re.DOTALL)


# 2. Rewrite _do_call_gemini to _do_call_gemma
gemma_call_logic = '''
async def _do_call_gemini(
    system_instruction: str,
    user_input: str,
    media_urls: list = None,
    model: str = "google/gemma-4-31B-it",
    schema: any = None
):
    messages = [{"role": "system", "content": system_instruction}]

    content_parts = []
    if user_input:
        content_parts.append({"type": "text", "text": user_input})
    else:
        content_parts.append({"type": "text", "text": "Analyze this receipt for UK tax categorization."})

    if media_urls:
        for url in media_urls:
            if is_safe_url(url):
                content_parts.append({"type": "image_url", "image_url": {"url": url}})

    messages.append({"role": "user", "content": content_parts})
    
    # Enforce Pydantic schema if provided
    response_format = None
    if schema:
        # In pydantic v2 we can use model_json_schema()
        response_format = {
            "type": "json_object",
            "value": schema.model_json_schema()
        }

    response = await hf_client.chat_completion(
        messages=messages,
        model=model,
        response_format=response_format,
        max_tokens=1500
    )
    
    return json.loads(response.choices[0].message.content)
'''
content = re.sub(r'async def _do_call_gemini\(.*?return json\.loads\(response\.text\)', gemma_call_logic.strip(), content, flags=re.DOTALL)

# 3. Rewrite _do_verify_expense_hallucination
gemma_verify_logic = '''
async def _do_verify_expense_hallucination(raw_message: str, parsed_json: dict) -> dict:
    system_instruction = """
    You are an Anti-Hallucination Auditor. Your strict job is to compare the raw user text to the parsed JSON.
    Did the AI hallucinate an amount, vendor, or date that the user did NOT actually say?
    For example, if the user says "lunch" and the AI outputs "vendor: Unknown, amount: 0.0", that is a hallucination/failure.
    If the user says "spent 50 at tesco" and AI outputs "amount: 50.0", that is valid.
    Return true for hallucination if the amount or vendor is completely fabricated.
    """
    
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": f"USER MESSAGE: {raw_message}\\nPARSED JSON: {json.dumps(parsed_json)}"}
    ]
    
    response = await hf_client.chat_completion(
        messages=messages,
        model="google/gemma-4-31B-it",
        response_format={"type": "json_object", "value": AntiHallucinationCheck.model_json_schema()},
        max_tokens=500
    )
    
    return json.loads(response.choices[0].message.content)
'''
content = re.sub(r'async def _do_verify_expense_hallucination\(raw_message: str, parsed_json: dict\) -> dict:.*?return json\.loads\(response\.text\)', gemma_verify_logic.strip(), content, flags=re.DOTALL)

# 4. Replace 429 references to generic HF references and replace "gemini-2.5-flash" with "google/gemma-4-31B-it"
content = content.replace('model="gemini-2.5-flash"', 'model="google/gemma-4-31B-it"')
content = content.replace('from google.genai.errors import APIError\n            if isinstance(e, APIError) and e.code == 429:', 'if isinstance(e, HfHubHTTPError) and e.response.status_code == 429:')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Migrated agents.py to Gemma 4 via Hugging Face!")
