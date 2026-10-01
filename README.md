# Invisible Accountant

UK MTD compliance engine. Parses receipts (Images/PDFs only to preserve Digital Links) -> Extracts tax data via Gemini -> Pushes Draft Bills to Xero.

## Architecture
- **Ingestion:** Strict enforcement of multimodal processing (no plain text, preserves MTD unbroken link).
- **Engine:** Gemini 2.5 Flash for HMRC logic extraction and mathematical multi-line splits.
- **Security:** AES-256-GCM encryption for all financial payloads at rest.
- **Routing:** Universal Adapter pattern pushing exclusively to Xero Draft Bills (bypassing HMRC's API freeze).

## Quickstart
```bash
cp .env.example .env
python main.py
```
