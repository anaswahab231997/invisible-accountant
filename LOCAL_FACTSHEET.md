# LOCAL FACTSHEET — Invisible Accountant
*Extracted exclusively from local source files. All citations reference verified file contents only.*

---

## 1. The Raise
- **Amount:** £350k–£500k Pre-Seed
- **Structure:** Pre-Seed round
- **SEIS/EIS Status:** SEIS/EIS Eligible (explicitly stated)
- **Target ARR:** £9.6M ARR in 5 years
- **Exit Path:** 10x–20x returns via acquisition; named acquirers: Xero, Monzo, Revolut

*Source: PITCH_DECK.md — "THE 10x ROI" section*

---

## 2. The Market
- **Sole Trader Count:** 3.2 million micro-businesses / UK sole traders
- **MTD Mandate Date:** April 2026 (HMRC's Making Tax Digital deadline)
- **Mandate Details:** HMRC's Making Tax Digital (MTD) mandate forces micro-businesses and sole traders into digital compliance. The mandate requires software that produces digitally-linked HMRC JSON payloads — described as "MTD's most complex technical hurdle."

*Source: PITCH_DECK.md — "THE PANIC (MTD 2026)" section; BUSINESS_PLAN.md — Executive Summary*

---

## 3. The Product
**How it actually works (WhatsApp flow ? AI ? HMRC submission):**

1. **Input Methods:** User snaps a receipt, records a voice note, or forwards a PDF — entirely within WhatsApp. No new app download required.
2. **AI Processing (Live Inference Engine):** A proprietary "Live Inference Engine" (called a "UK Tax AI Engine") ingests unstructured text/audio and:
   - Extracts data from receipts/audio
   - Categorises expenses according to HMRC rules (handles dual-use items, non-allowable deductions, precise entity extraction)
   - Applies HMRC logic constraints from training on HMRC case law, tax tribunals, and accounting rules
3. **User Confirmation Flow (from main.py):** When user replies "proceed", the system calls `confirm_and_queue_to_ledger()` — staging the expense and queuing it to the HMRC submission ledger
4. **Quarterly Submissions:** AI prepares quarterly updates automatically; engine outputs structured, digitally-linked HMRC JSON payloads
5. **Platform Fallback:** Primary delivery is WhatsApp (Meta); fallback to SMS via Twilio and a lightweight Progressive Web App (PWA) if Meta alters terms

*Source: PITCH_DECK.md — "INVISIBLE MAGIC"; BUSINESS_PLAN.md — Section 1 & 2; main.py lines 94–97*

---

## 4. The Technical Proof Points

### Security
- **AES-256-GCM Encryption (aes_gcm_security.py):** `TokenEncryptionEngine` class implements AES-256-GCM with authenticated encryption. Master key must be exactly 32 bytes. Includes `authenticate_additional_data()` (AEAD). Raises `InvalidTag` exception on cryptographic integrity failure with tamper detection messaging.
- **SHA-256 Hashing:** WhatsApp numbers (PII) are secured using SHA-256 hashing prior to any interaction with HMRC networks (from hmrc_api.py — `hashlib.sha256` applied to `real_device_id`)
- **Data Architecture:** PII and financial data are instantly decoupled from the chat interface and stored in an encrypted PostgreSQL staging environment ("Bank-level security vault")
- **DB Encryption Key:** Loaded from environment variable `DB_ENCRYPTION_KEY_B64` (from worker.py)
- **HSTS Enforced:** `Strict-Transport-Security: max-age=31536000; includeSubDomains` set as HTTP middleware (from main.py lines 51–55)
- **Rate Limiting:** slowapi Limiter applied using `get_remote_address` (from main.py)
- **API Docs Hidden:** FastAPI app disables docs_url, redoc_url, openapi_url (from main.py line 47)

### HMRC Compliance
- **HMRC Production Ticket:** Reference **2026-OUP153** — formal application for Production API Credentials submitted to HMRC Developer Hub for MTD IT & VAT
- **Fraud Prevention Headers:** Implemented `OTHER_VIA_SERVER` specification (`Gov-Client-Connection-Method: OTHER_VIA_SERVER`). Full header set in hmrc_api.py: `Gov-Vendor-Version`, `Gov-Vendor-Public-IP`, `Gov-Client-Public-IP`, `Gov-Vendor-Forwarded`, `Gov-Vendor-Product-Name`, `Gov-Vendor-License-IDs`
- **Static Egress IP:** Backend server must be hosted with Static Egress IP (e.g., AWS Elastic IP) for HMRC Developer Hub IP Allow List compliance (from HMRC_PRODUCTION.md)
- **Required Production APIs (from HMRC_PRODUCTION.md):**
  - Business Details API
  - Obligations API
  - Self Employment Business API
  - Individuals Calculations API
  - Property Business API
- **OAuth Token Management (worker.py):** `OAuthManager` class handles token retrieval from encrypted vault, automatic refresh via `HMRC_BASE_URL/oauth/token`, re-encryption and re-storage of refreshed tokens. 60-second buffer for network latency on expiry checks.
- **Circuit Breaker:** `CircuitBreaker` and `CircuitBreakerOpenException` imported in worker.py for resilience against HMRC API failures

### Penetration Testing
- **Pen Test:** Infrastructure passed an automated, CREST-accredited Infrastructure Penetration Test via **Intruder.io**
- **WAF:** Cloudflare Web Application Firewall (WAF) with HSTS enforced
- **ISO 27001 Ready:** Described as such in BUSINESS_PLAN.md
- **Prometheus Metrics Endpoint:** Explicitly disabled (comment: "Disabled to fix Exposed Metrics Endpoint finding") — from main.py line 57, indicating a pen test finding was remediated

### HMRC Sandbox vs Production
- **Current Default URL:** `https://test-api.service.hmrc.gov.uk` (sandbox) — from hmrc_api.py line 12 and worker.py line 36
- **Sandbox APIs excluded from production (HMRC_PRODUCTION.md):** Test Support 1.0, Create Test User 1.0, Test Fraud Prevention 1.0

*Source: aes_gcm_security.py; hmrc_api.py; worker.py; main.py; BUSINESS_PLAN.md; HMRC_PRODUCTION.md*

---

## 5. The Business Model
- **Primary Model:** B2B2C — White-label Enterprise Licensing for high-street accountancy firms
- **GTM:** Sell Enterprise licenses to traditional accountancy firms; firms white-label the WhatsApp bot and onboard their entire client base overnight
- **CAC Advantage:** "One B2B sale brings 1,000+ sole trader clients instantly" — drastically lowered CAC via enterprise sales cycles
- **Gross Margins:** 85%+ on the underlying software layer
- **Revenue Metric:** Highly scalable Annual Contract Value (ACV)
- **Direct B2C:** Not primary — cited as having "prohibitively high Customer Acquisition Costs (CAC)"
- **Operating Leverage:** Near-zero marginal cost to onboard additional 10,000 users

*Source: PITCH_DECK.md — "UNFAIR ECONOMICS"; BUSINESS_PLAN.md — Section 2*

---

## 6. The Roadmap

### Year 1
- Hire 2 UK-based Senior AI/Backend Engineers
- Hire 1 Head of Accountancy Partnerships

### Year 2
- Expand GTM team
- Hire UK-based B2B sales representatives to onboard regional accountancy networks

### Year 3
- Establish a localized compliance and legal team
- Oversee international expansion into EU and US markets from UK headquarters
- Export and fine-tune AI engine for global gig-economies:
  - **US 1099 Workers:** Translating HMRC rules to IRS guidelines
  - **Australia / Canada:** Adapting to local GST and sole trader tax codes
  - **EU VAT regimes:** With minimal architectural friction (mentioned as Year 3 / 2028 target)
- WhatsApp interface remains the same; AI engine scales globally

### 5-Year Target
- £9.6M ARR

*Source: PITCH_DECK.md — "GLOBAL SCALABILITY"; BUSINESS_PLAN.md — Section 3*

---

## 7. The Competitors Named
*(Only those explicitly mentioned in the local files)*

1. **Xero** — named as a legacy incumbent (deterministic database, requires manual data entry) AND as a potential acquirer
2. **QuickBooks** — named as a legacy incumbent (deterministic database, requires manual data entry)
3. **Monzo** — named as a potential acquirer
4. **Revolut** — named as a potential acquirer

*Source: BUSINESS_PLAN.md — Section 1 ("Defensibility against Incumbents"); PITCH_DECK.md — "THE 10x ROI"*

---

## File Coverage Notes
| File | Status |
|---|---|
| PITCH_DECK.md | Read in full (38 lines) |
| BUSINESS_PLAN.md | Read in full (43 lines) |
| README.md | Read — empty file (0 bytes) |
| HMRC_PRODUCTION.md | Read in full (19 lines) |
| main.py | Read first 100 lines of 515 |
| hmrc_api.py | Read first 80 lines of 197 |
| aes_gcm_security.py | Read in full (56 lines) |
| worker.py | Read first 80 lines of 288 |

---

*Generated: 2026-09-06 | Source: Local files only — no extrapolation*
