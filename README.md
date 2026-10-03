# The Invisible Accountant 🇬🇧

An autonomous, **Zero-Hallucination** AI bookkeeping pipeline designed specifically for UK Sole Traders and Accountants. Built to comply with HMRC MTD (Making Tax Digital) ITSA regulations.

## 🚀 The Core Philosophy
Most AI bookkeeping tools attempt to guess tax codes, often hallucinating categories that don't exist in the client's Chart of Accounts. 
**The Invisible Accountant** solves this by physically constraining the AI's generation process using **dynamic Pydantic Enums**.

Every time a receipt or message is processed, the system builds a dynamic schema restricted exactly to the accountant's Xero / HMRC tax codes. The AI is forced at the token-generation level to select a valid category, resulting in 100% zero-hallucination compliance.

## ✨ Features
- **Zero-Hallucination Pipeline**: Uses Gemini 2.5 Flash and Pro wrapped in strict JSON-schema enforcement to extract amounts, vendors, and precise tax codes.
- **Deep Audit Escalation**: Automatically flags expenses with "Duality of Purpose" (e.g. personal vs. business laptops) and escalates them to a deep reasoning model.
- **Human-in-the-Loop Accountant Queue**: An HTMX + FastAPI dashboard where accountants can review, edit, and bulk-approve AI categorizations before they hit Xero.
- **Crash-Proof Concurrency**: Implements a strict `asyncio.Semaphore` throttling queue, completely bypassing 429 Rate Limits during massive WhatsApp traffic spikes.
- **Anti-Hallucination Auditor**: A secondary AI pass that strictly verifies the model didn't invent vendors or amounts not present in the user's text.

## 🛠 Tech Stack
- **Backend**: Python, FastAPI, SQLite (async)
- **Frontend**: HTMX, Tailwind CSS, Jinja2 Templates
- **AI Infrastructure**: Google Gemini API (`google-genai` SDK)

## 📦 Installation & Setup

1. **Clone & Install**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=sqlite+aiosqlite:///prototype_db.sqlite
   ```

3. **Initialize the Database**
   ```bash
   python init_db.py
   ```

4. **Run the Server**
   ```bash
   python -m uvicorn main:app --port 8000
   ```

## 📊 Dashboards
Once the server is running, you can access the two core dashboards:
- **[Accountant Review Queue](http://localhost:8000/dashboard)**: Where accountants review the AI's work and approve it.
- **[DevOps & System Architecture](http://localhost:8000/dev-dashboard)**: Monitor DB load, AI latency, and queue depth in real-time.

## 🧪 Testing the Prototype
To simulate heavy concurrent WhatsApp traffic and test the Semaphore Queue's resilience:
```bash
python simulate_dashboard_levels.py
```
This will inject 5 highly complex, ambiguous edge-case expenses into the queue instantly. You can watch the Dev Dashboard handle the load perfectly.

---
*Built for UK Accountants with ❤️.*
