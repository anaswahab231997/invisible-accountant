import argparse
import json
import os
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

def main():
    parser = argparse.ArgumentParser(description="Scrape websites into the Knowledge Base using LLMs.")
    parser.add_argument("url", help="The URL to scrape")
    parser.add_argument("prompt", help="The extraction prompt for the LLM")
    parser.add_argument("--out", "-o", default="knowledge_base/output.json", help="Output JSON file path")
    
    args = parser.parse_args()
    
    # Ensure kb directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    
    print(f"Scraping {args.url}...")
    scraper = SmartScraperGraph(
        prompt=args.prompt,
        source=args.url,
        config=graph_config
    )
    
    result = scraper.run()
    
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)
        
    print(f"Knowledge Base updated successfully. Result saved to {args.out}")

if __name__ == "__main__":
    main()
