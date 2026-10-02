# State of the Codebase Report: Invisible Accountant
**Date:** September 26, 2026

This is a factual audit of the currently implemented source code in the `c:\Antigravity\UK MTD\invisible-accountant` directory. No planned or conceptual features are included; only what is physically written in the code.

## 1. Frameworks & Technology Stack
- **Backend Application:** Python 3 utilizing the **FastAPI** framework (`main.py`).
- **Database:** **SQLite** (`prototype_db.sqlite`), accessed asynchronously with connection pooling.
- **AI / LLM:** Google's **Gemini API** (`google-genai` SDK) is used for natural language processing.
- **Messaging Integration:** The **Twilio** Python SDK is used for WhatsApp webhook ingestion and outbound replies.
- **Security & Rate Limiting:** Uses `slowapi` for rate limiting and custom AES-GCM encryption (`aes_gcm_security.py`) for vaulting OAuth tokens.

## 2. WhatsApp Webhook Handling
The webhook flow is structured as an asynchronous producer-consumer pattern to avoid API timeouts:
- **Ingestion (`main.py`):** The `/webhook/twilio` endpoint receives the WhatsApp payload. It validates the Twilio HMAC signature via `RequestValidator`. 
- **PII Scrubbing:** The message body is passed through a `mask_pii` function.
- **Durable Queueing:** Instead of processing the LLM request inline (which would exceed Twilio's 15-second webhook timeout limit), the application logs the chat session to the DB and pushes the payload into a persistent SQLite queue (`push_intake_queue`). It immediately returns an empty `<Response></Response>` XML to Twilio.
- **Processing:** A background task (`intake_worker`) pulls messages from the database queue and passes them to `process_intake_task`, which executes the LLM pipeline.
- **Outbound:** Once the LLM formulates a response (or asks for clarification), the system uses `twilio.rest.Client.messages.create` to dispatch the reply back to the user's WhatsApp number.

## 3. Gemini / LLM Extraction Structure
The LLM extraction logic is entirely contained within `agents.py`.
- **Persona & Prompting:** The agent is prompted as "Emma," an accountant. It receives strict rules regarding HMRC allowable expenses (e.g., duality of purpose, client entertainment exclusions).
- **Structured Output:** The code utilizes `gemini-2.5-flash` with a Pydantic schema (`ExpenseCategorization`) passed into `response_schema` to guarantee structured JSON output containing `amount`, `vendor`, `category`, and an `is_ambiguous` boolean.
- **Anti-Hallucination Pipeline:** 
  - After the initial extraction, a secondary LLM call (`verify_expense_hallucination`) checks if the AI fabricated an amount or vendor not present in the user's raw text.
  - If a hallucination is detected, or if the primary extraction's self-assessed confidence score is `< 0.92`, the transaction is flagged as `is_ambiguous = True`.
  - When ambiguous, the AI is forced to generate an `auditor_question` (max 3 sentences) to ask the user for clarification.
- **Fallback Logic:** If flagged as ambiguous, it performs a "Deep Audit Escalation" by calling the model again (though currently, it just calls `gemini-2.5-flash` a second time as a fallback).

## 4. HMRC and Xero API Integration
### Xero
**There is zero Xero integration in the codebase.** No endpoints, authentication, or SDKs related to Xero exist.

### HMRC (`hmrc_api.py` & `worker.py`)
The HMRC MTD (Making Tax Digital) integration is partially built with active OAuth 2.0 flows, but contains heavy stubbing:
- **Authentication:** OAuth 2.0 flow is implemented in `main.py` (`/auth` and `/callback`). Tokens are AES-GCM encrypted and stored in a vault. `worker.py` contains an `OAuthManager` that handles token refreshes.
- **Fraud Prevention Headers:** `generate_whatsapp_fraud_headers` generates the strictly required HMRC telemetry headers, declaring the connection method as `OTHER_VIA_SERVER`.
- **API Mapping:** Internal categories are mapped to official HMRC ITSA deduction keys (e.g., `Car, van and travel expenses` -> `travelCosts`).
- **Hardcoded Stubs / Missing Pieces (Crucial):**
  - In `hmrc_api.py`, the methods `submit_periodic_update`, `get_itsa_penalties`, and `submit_annual_adjustments` all contain early-exit stubs. If `access_token` is missing or empty, the code skips the HTTP request entirely and returns a simulated success payload (e.g., `{"simulated": True, "message": "Simulated successful submission"}`).
  - The `get_public_ip()` function fails back to hardcoded `"127.0.0.1"` on network failure, which may cause HMRC API rejections in production.
  - Device ID (`Gov-Client-Device-ID`) is intentionally left out because the WhatsApp architecture does not expose the physical client device ID to the server.
