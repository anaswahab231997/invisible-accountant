import os

with open('test_agents.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'result = process_expense_message(case["message"])' in line:
        new_lines.append(line.replace('result = process_expense_message(case["message"])', 'result = asyncio.run(process_expense_message(case["message"]))'))
    else:
        new_lines.append(line)

new_lines.insert(0, 'import asyncio\n')

with open('test_agents.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
