import requests
import html2text
import os

urls = {
    "using-the-hub": "https://developer.service.hmrc.gov.uk/api-documentation/docs/using-the-hub",
    "name-guidelines": "https://developer.service.hmrc.gov.uk/api-documentation/docs/name-guidelines",
    "api-statuses": "https://developer.service.hmrc.gov.uk/api-documentation/docs/api-statuses",
    "reference-guide": "https://developer.service.hmrc.gov.uk/api-documentation/docs/reference-guide",
    "development-practices": "https://developer.service.hmrc.gov.uk/api-documentation/docs/development-practices",
    "fraud-prevention": "https://developer.service.hmrc.gov.uk/guides/fraud-prevention",
    "authorisation": "https://developer.service.hmrc.gov.uk/api-documentation/docs/authorisation",
    "tutorials": "https://developer.service.hmrc.gov.uk/api-documentation/docs/tutorials",
    "testing": "https://developer.service.hmrc.gov.uk/api-documentation/docs/testing"
}

os.makedirs("knowledge_base_raw", exist_ok=True)
h = html2text.HTML2Text()
h.ignore_links = False

for name, url in urls.items():
    try:
        res = requests.get(url)
        md = h.handle(res.text)
        with open(f"knowledge_base_raw/{name}.md", "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Scraped {name}")
    except Exception as e:
        print(f"Failed {name}: {e}")
