import os
import json
import time
from scrapegraphai.graphs import SmartScraperGraph
from dotenv import load_dotenv

load_dotenv()

graph_config = {
    "llm": {
        "api_key": os.environ.get("GEMINI_API_KEY"),
        "model": "google_genai/gemini-2.5-flash", 
    },
    "verbose": True,
    "headless": True
}

urls = [
    ("using-the-hub", "https://developer.service.hmrc.gov.uk/api-documentation/docs/using-the-hub"),
    ("name-guidelines", "https://developer.service.hmrc.gov.uk/api-documentation/docs/name-guidelines"),
    ("api-statuses", "https://developer.service.hmrc.gov.uk/api-documentation/docs/api-statuses"),
    ("reference-guide", "https://developer.service.hmrc.gov.uk/api-documentation/docs/reference-guide"),
    ("development-practices", "https://developer.service.hmrc.gov.uk/api-documentation/docs/development-practices"),
    ("fraud-prevention", "https://developer.service.hmrc.gov.uk/guides/fraud-prevention"),
    ("authorisation", "https://developer.service.hmrc.gov.uk/api-documentation/docs/authorisation"),
    ("tutorials", "https://developer.service.hmrc.gov.uk/api-documentation/docs/tutorials"),
    ("testing", "https://developer.service.hmrc.gov.uk/api-documentation/docs/testing"),
]

prompt = "Extract all the technical rules, compliance guidelines, limitations, API requirements, and developer responsibilities from this page. Provide a highly structured summary so that our backend MTD architecture agents can ingest it and ensure 100% compliance."

os.makedirs("knowledge_base", exist_ok=True)

for name, url in urls:
    out_path = f"knowledge_base/{name}.json"
    if os.path.exists(out_path):
        print(f"Skipping {name}, already scraped.")
        continue
        
    print(f"Scraping {url}...")
    scraper = SmartScraperGraph(
        prompt=prompt,
        source=url,
        config=graph_config
    )
    
    success = False
    retries = 3
    while not success and retries > 0:
        try:
            result = scraper.run()
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4)
            print(f"Success! Saved to {out_path}")
            success = True
        except Exception as e:
            print(f"Failed (Retries left: {retries}): {e}")
            retries -= 1
            if retries > 0:
                print("Sleeping for 60 seconds before retry due to Gemini Free Tier limits...")
                time.sleep(60)
                
    print("Sleeping for 30 seconds to respect Gemini Free Tier 20 RPM limits...")
    time.sleep(30)

print("HMRC Knowledge Base successfully compiled!")
