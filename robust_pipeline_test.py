import asyncio
import json
import os
from agents import process_expense_message, HMRCCategory

messages = [
    "Bought a 1500 GBP laptop and a 5 GBP coffee from Pret. Wait, the laptop is 50% for personal use.",
    "Taxi to London for 40 GBP, no VAT receipt. Plus 10 GBP tip.",
    "Paid my accountant 200 GBP for software subscription."
]

async def main():
    print("Starting Pipeline Tests...\n")
    for i, msg in enumerate(messages, 1):
        print(f"--- Test Case {i} ---")
        print(f"Input: {msg}")
        try:
            result = await process_expense_message(msg)
            print(f"Output: {json.dumps(result.model_dump() if hasattr(result, 'model_dump') else result, indent=2)}")
        except Exception as e:
            print(f"Status: FAILED with error: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
