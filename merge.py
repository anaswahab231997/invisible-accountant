import re

with open('landing_page.html', 'r', encoding='utf-8') as f:
    local_html = f.read()

# Extract Thermal Receipt CSS
css_match = re.search(r'(/\* Mock Receipt Style \*/.*?\n        })', local_html, re.DOTALL)
thermal_css = css_match.group(1) if css_match else ''
print(f"Extracted CSS: {bool(thermal_css)}")

# Extract Inference Wrapper HTML
html_match = re.search(r'(<section id="inference-wrapper".*?</section>)', local_html, re.DOTALL)
thermal_html = html_match.group(1) if html_match else ''
print(f"Extracted HTML: {bool(thermal_html)}")

# Read Live HTML
with open('clean_live.html', 'r', encoding='utf-8') as f:
    live_html = f.read()

# Inject CSS (if not already there)
if thermal_css and 'Mock Receipt Style' not in live_html:
    live_html = live_html.replace('</style>', thermal_css + '\n    </style>')

# Replace Inference Wrapper
if thermal_html:
    live_html = re.sub(r'<!-- LIVE INFERENCE DECRYPTOR SECTION \(SCROLL-DRIVEN\) -->.*?<section id="inference-wrapper".*?</section>', thermal_html, live_html, flags=re.DOTALL)

with open('landing_page_merged.html', 'w', encoding='utf-8') as f:
    f.write(live_html)
