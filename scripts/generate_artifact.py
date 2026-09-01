import os
import glob

content = "# HMRC Developer Hub - Scraped Compliance Guidelines\n\n"
content += "> [!IMPORTANT]\n> This artifact contains the raw fast-scraped markdown of the HMRC developer portal links requested. Review it to understand all rules before building further.\n\n"

for fp in glob.glob("knowledge_base_raw/*.md"):
    name = os.path.basename(fp).replace(".md", "")
    with open(fp, "r", encoding="utf-8") as f:
        text = f.read()
    
    start = text.find("Your [feedback")
    if start != -1:
        text = text[start+100:]
        end = text.find("Is this page not working properly?")
        if end != -1:
            text = text[:end]
    
    content += f"## {name.replace('-', ' ').title()}\n\n"
    content += text.strip() + "\n\n---\n\n"

out_path = r"C:\Users\ANAS\.gemini\antigravity\brain\78ff27f1-8259-43b9-b7a1-bc6c2f498cda\hmrc_compliance_docs.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Artifact written!")
