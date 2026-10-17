# Investor Demo Plan: "The Invisible Accountant"

## The Goal
To prove to UK Accountants and Seed Investors that our AI is **Safe**, **Compliant**, and **Crash-Proof**, turning hours of manual bookkeeping into an instant, zero-hallucination workflow.

## The 3-Step Demo Flow

### Step 1: Secure Data Ingestion & OCR Accuracy (The "Wow" Factor)
**Action:** Using the WhatsApp integration (or the `simulate_load.py` script), push a batch of complex UK receipts into the system. Include a mix of simple expenses and complex edge cases (e.g., a blurry coffee receipt and a £1500 laptop with 50% personal use).
**Talking Point:** "Most AI bookkeeping tools guess when they get confused. Watch how our Zero-Hallucination engine physically constrains the AI to your exact Chart of Accounts using dynamic Pydantic schemas. It cannot hallucinate an account code."

### Step 2: MTD-Compliant Tax Categorization (The "Trust" Factor)
**Action:** Open the **Accountant Review Queue Dashboard** (`/dashboard`). Show the live-updating rows as the AI perfectly categorizes the transactions according to HMRC tax rules.
**Talking Point:** "Look at how the AI handles the laptop. It didn't just extract the price—it applied the HMRC 'Duality of Purpose' rule, apportioned 50% for personal use, and drafted a concise WhatsApp message asking the client to confirm. It acts exactly like a Junior Accountant."

### Step 3: Seamless System Resilience (The "Scale" Factor)
**Action:** Open the **System Architecture & DevOps Dashboard** (`/dev-dashboard`). Run the heavy load simulation script.
**Talking Point:** "We built this for massive concurrency. Behind the scenes, a strict background queuing mechanism (Semaphore throttling) ensures that even if 500 clients text their receipts at 9:00 AM on a Monday, the API will perfectly throttle and process them without a single 429 crash or dropped message. It's production-ready for your practice today."
