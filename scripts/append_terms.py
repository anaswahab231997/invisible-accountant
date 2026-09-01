import json
import os

out_path = r"C:\Users\ANAS\.gemini\antigravity\brain\78ff27f1-8259-43b9-b7a1-bc6c2f498cda\hmrc_compliance_docs.md"

with open("knowledge_base/hmrc_terms_of_use.json", "r", encoding="utf-8") as f:
    terms = json.load(f)

content = "\n\n## Terms Of Use (Scraped via AI)\n\n"
for section, details in terms.items():
    content += f"### {section}\n"
    if isinstance(details, dict):
        for k, v in details.items():
            if isinstance(v, dict):
                content += f"**{k}**\n"
                for sub_k, sub_v in v.items():
                    content += f"- **{sub_k}**: {sub_v}\n"
            else:
                content += f"- **{k}**: {v}\n"
    content += "\n"

with open(out_path, "a", encoding="utf-8") as f:
    f.write(content)

print("Terms appended!")
