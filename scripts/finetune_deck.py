# Fine-tune investor_jury_deck.html for immaculate responsiveness across all displays

with open('C:/Antigravity/UK MTD/invisible-accountant/investor_jury_deck.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Refine eyebrow and footer in CSS
old_css_part = '''        .eyebrow-id {
            font-family: 'Geist Mono', monospace;
            font-size: 0.72rem;
            font-weight: 400;
            letter-spacing: 0.15em;
            color: #64748B;
            text-transform: uppercase;
            white-space: nowrap;
        }'''

new_css_part = '''        .eyebrow-id {
            font-family: 'Geist Mono', monospace;
            font-size: 0.72rem;
            font-weight: 400;
            letter-spacing: 0.15em;
            color: #64748B;
            text-transform: uppercase;
            white-space: nowrap;
        }

        @media (max-width: 1080px) {
            .eyebrow-id {
                display: none;
            }
            .hero-right {
                padding-left: 24px;
            }
        }'''

content = content.replace(old_css_part, new_css_part)

# Ensure footer avoids overlapping with bottom-right controls
old_footer = '''        .memorandum-footer {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-top: 18px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            z-index: 2;
            gap: 20px;
        }'''

new_footer = '''        .memorandum-footer {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-top: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            z-index: 2;
            gap: 20px;
            padding-bottom: 4px;
        }'''

content = content.replace(old_footer, new_footer)

with open('C:/Antigravity/UK MTD/invisible-accountant/investor_jury_deck.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("investor_jury_deck.html fine-tuning complete.")
