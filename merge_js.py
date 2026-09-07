import re

with open('landing_page.html', 'r', encoding='utf-8') as f:
    local_html = f.read()

# Extract Scroll JS
js_match = re.search(r'(// Soft Scroll-driven Receipt Scanner Logic.*?\n        \}\);)', local_html, re.DOTALL)
if not js_match:
    js_match = re.search(r'(// Scroll-driven Inference Engine Logic.*?\n        \}\);)', local_html, re.DOTALL)
thermal_js = js_match.group(1) if js_match else ''
print(f"Extracted JS: {bool(thermal_js)}")


with open('landing_page_merged.html', 'r', encoding='utf-8') as f:
    live_html = f.read()

if thermal_js:
    live_html = re.sub(r'// Scroll-driven Inference Engine Logic.*?\n        \}\);', thermal_js, live_html, flags=re.DOTALL)
    
with open('landing_page_merged.html', 'w', encoding='utf-8') as f:
    f.write(live_html)
