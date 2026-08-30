import os
import sys

# Ensure we're running from the right directory
sys.path.append(os.path.dirname(__file__))

from agents import process_expense_message


def run_tests():
    print("Testing Emma AI (agents.py -> process_expense_message)\n")

    test_cases = [
        {
            "name": "1. Clear allowable expense",
            "message": "Bought a train ticket to London for £40 for a client meeting",
            "expected_ambiguous": False,
        },
        {
            "name": "2. Client entertainment (Not allowable)",
            "message": "Took John out to dinner to discuss the new contract, cost £150",
            "expected_ambiguous": True,
        },
        {
            "name": "3. Ambiguous expense (Duality of purpose)",
            "message": "Paid my £50 O2 phone bill",
            "expected_ambiguous": True,
        },
        {
            "name": "4. Unallowable clothing expense",
            "message": "Bought a new suit for £200 for a conference at M&S",
            "expected_ambiguous": True,
        },
    ]

    for case in test_cases:
        print(f"--- Running Test: {case['name']} ---")
        print(f"Input: {case['message']}")
        try:
            result = process_expense_message(case["message"])
            print(f"Vendor: {result.get('vendor')}")
            print(f"Amount: {result.get('amount')}")
            print(f"Category: {result.get('category')}")
            print(
                f"Is Ambiguous: {result.get('is_ambiguous')} (Expected: {case['expected_ambiguous']})"
            )
            if result.get("is_ambiguous"):
                print(f"Auditor Question: {result.get('auditor_question')}")
            print(f"Reasoning 2: {result.get('reasoning_step_2_nature_of_expense')}")
            print(f"Reasoning 3: {result.get('reasoning_step_3_hmrc_rules')}")
        except Exception as e:
            print(f"Error during test: {e}")
        print("\n")


if __name__ == "__main__":
    run_tests()
