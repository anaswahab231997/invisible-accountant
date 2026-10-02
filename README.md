# Invisible Accountant

The Invisible Accountant is a robust, high-performance automated accounting service designed specifically for UK Making Tax Digital (MTD) compliance. It seamlessly bridges communication between clients via WhatsApp and the Xero accounting platform, utilizing advanced Large Language Models (LLMs) with strict constraints to ensure absolute data integrity.

## Architecture

The system is built for concurrency, speed, and reliability, leveraging modern asynchronous Python frameworks:

- **FastAPI**: Serves as the high-performance web framework, handling incoming webhook events and API requests with minimal latency.
- **AsyncPG**: Provides asynchronous PostgreSQL database access, ensuring non-blocking, high-throughput data operations crucial for handling concurrent messaging and transaction logging.
- **WhatsApp Webhooks**: Acts as the primary interface for client interactions, receiving receipts, invoices, and accounting queries in real-time.

## The Zero Hallucination Engine

In financial and tax compliance contexts, LLM hallucinations are unacceptable. The Invisible Accountant employs a "Zero Hallucination Engine" to guarantee that data pushed to Xero is strictly valid.

Rather than relying on prompt engineering to enforce output constraints, we dynamically enforce them at the schema level:

1. **Per-Request Schema Generation**: For every transaction processing request, we dynamically fetch the specific, active Tax Rates and Account Codes available in the client's Xero organization.
2. **Dynamic Pydantic Models**: We use Pydantic's `create_model` in conjunction with Python's `enum.Enum` to generate strict validation schemas on the fly. The valid Xero codes are embedded as Enum values within this schema.
3. **Structured Generation**: The LLM is forced to output data conforming exactly to this dynamically generated Pydantic model. By physically constraining the output space to the `Enum` values, it is impossible for the LLM to hallucinate invalid or non-existent Xero Tax or Account codes.

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Google Gemini API Key

### Installation

1. Navigate to the project directory:
   ```bash
   cd invisible-accountant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment variables. Create a `.env` file in the project root and provide the necessary credentials:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
   ```

## Testing

The project includes scripts to ensure reliability and performance.

### Running End-to-End Tests

To execute the end-to-end test suite:

```bash
python e2e_test.py
```

### Simulating Load

To test the system's performance and concurrency limits under heavy traffic:

```bash
python simulate_load.py
```
