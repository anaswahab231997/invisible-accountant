# coding: utf-8
import asyncio
import json
from agents import process_expense_message

scenarios = [
    "Tesco receipt: £10 standard items (20%), £5 zero-rated food, and a £3 personal magazine.",
    "Dinner for £100: £50 for me (staff) and £50 for my client.",
    "£150 Christmas party, but it was just me and the other company director, no other staff.",
    "Claiming 100 miles at 45p. Attached £15 fuel receipt with 20% VAT."
]

async def main():
    results = {}
    for i, scenario in enumerate(scenarios, 1):
        try:
            print(f"Testing {i}")
            res = await process_expense_message(scenario)
            results[f"Scenario {i}"] = {"input": scenario, "output": res}
        except Exception as e:
            results[f"Scenario {i}"] = {"input": scenario, "error": str(e)}
            
    with open("sandbox_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Done")

if __name__ == "__main__":
    asyncio.run(main())