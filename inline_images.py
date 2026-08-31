import base64
import re
import os

html_path = "investor_deck.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

def replace_img(match):
    img_path = match.group(1)
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
            ext = img_path.split('.')[-1]
            return f'src="data:image/{ext};base64,{encoded_string}"'
    return match.group(0)

# Replace src="assets/..." with base64
new_html = re.sub(r'src="(assets/[^"]+)"', replace_img, html_content)

with open("investor_deck_standalone.html", "w", encoding="utf-8") as f:
    f.write(new_html)

print("Created investor_deck_standalone.html with all images embedded!")
