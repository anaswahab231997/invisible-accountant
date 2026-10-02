import os
import glob

files = glob.glob('*.md') + glob.glob('*.html')

for filepath in files:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    original = content
    
    replacements = {
        "In April 2026, the UK government is forcing 3.2 million micro-businesses": "Five months ago, the HMRC MTD tax mandate went live for top earners. The final wave hits 3.2 million micro-businesses in April 2027",
        "The mandate is law. I’m ready to build this in London.": "The mandate is live. The market is bleeding. I’m ready to scale this in London.",
        "In April 2026, HMRC's Making Tax Digital (MTD) mandate comes into full force": "HMRC's MTD Phase 1 mandate went live 5 months ago. Phase 2 hits in April 2027",
        "In April 2026, HMRC's Making Tax Digital (MTD) mandate comes into full statutory effect": "HMRC's MTD Phase 1 mandate went live 5 months ago. Phase 2 hits in April 2027",
        "In April 2026, HMRC forces 3.2 million UK sole traders": "HMRC's MTD mandate is now live. Phase 2 hits 3.2 million UK sole traders in April 2027",
        "With HMRC making tax digital (MTD) mandatory for 3.2 million sole traders in 2026,": "With HMRC's digital tax mandate (MTD) now live, and the final Phase 2 wave hitting 3.2 million sole traders in April 2027,",
        "ahead of the April 2026 MTD deadline": "ahead of the massive April 2027 Phase 2 deadline",
        "Making Tax Digital (MTD) becomes mandatory for UK Sole Traders in April 2026.": "HMRC MTD Phase 1 is LIVE. The final Phase 2 mandate hits in April 2027.",
        "Making Tax Digital (MTD) becomes mandatory for UK Sole Traders earning over £50k in April 2026.": "HMRC MTD Phase 1 is LIVE. The final Phase 2 mandate hits in April 2027.",
        "countdown to HMRC Making Tax Digital in April 2026": "countdown to the final HMRC Making Tax Digital Phase 2 in April 2027"
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
