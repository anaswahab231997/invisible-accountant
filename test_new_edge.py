import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.abspath('.'))
from agents import process_expense_message, verify_expense_hallucination

edge_cases = [
    {
        "name": "Digital Subscription Trap",
        "msg": "Just paid £25 for Spotify, need it for 'content research' as I do a weekly podcast."
    },
    {
        "name": "Capital Asset & Duality",
        "msg": "Bought a used van for £900 to carry tools, but I drop the kids off at school in it too."
    },
    {
        "name": "Home Office Apportionment",
        "msg": "Paid my monthly rent £1200, I use my spare bedroom which is 25% of the house exclusively for my business."
    },
    {
        "name": "Mixed Income and Expense",
        "msg": "I received a £600 payment for website design, but I also paid £55 for hosting on the same day to AWS."
    }
]

async def run_tests():
    print("DEPLOYING NEW EXTREME EDGE CASE ENVIRONMENT...\n")
    for case in edge_cases:
        print("="*60)
        print(f"TEST: {case['name'].upper()}")
        print(f"USER MSG: '{case['msg']}'")
        try:
            parsed = await process_expense_message(case['msg'])
            audit = await verify_expense_hallucination(case['msg'], parsed)
            
            print(f"\nEMMA'S BRAIN (Parsed):")
            print(f"   Amount: £{parsed.get('amount')} | Vendor: {parsed.get('vendor')}")
            print(f"   Category: {parsed.get('category')}")
            print(f"   Is Ambiguous: {parsed.get('is_ambiguous')}")
            print(f"   Type: {parsed.get('transaction_type')}")
            
            if parsed.get('is_ambiguous'):
                print(f"   Escalation/Question: {parsed.get('auditor_question')}")
            
            print(f"\nAUDITOR CHECK:")
            if audit.get('is_hallucinated'):
                print(f"   CAUGHT HALLUCINATION: {audit.get('hallucination_reason')}")
            else:
                print("   Passed (Zero Hallucination Detected)")
                
        except Exception as e:
            print(f"CRITICAL FAILURE: {str(e)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
