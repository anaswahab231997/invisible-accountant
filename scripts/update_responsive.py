# Update test_slide1.html with perfected responsive CSS and single-line eyebrow

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/test_slide1.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make eyebrow responsive and prevent wrap
content = content.replace(
    "font-size: 0.75rem;\n            font-weight: 500;\n            letter-spacing: 0.25em;",
    "font-size: clamp(0.65rem, 0.9vw, 0.75rem);\n            font-weight: 500;\n            letter-spacing: clamp(0.12em, 0.2vw, 0.25em);\n            white-space: nowrap;"
)

# Refine padding for perfect 16:9 and laptop fit
content = content.replace(
    "padding: clamp(48px, 6vw, 84px);",
    "padding: clamp(36px, 4.5vw, 64px);"
)

content = content.replace(
    "padding: clamp(32px, 4vw, 56px) 0;",
    "padding: clamp(20px, 2.5vw, 40px) 0;"
)

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/test_slide1.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated responsive styles in test_slide1.html.")
