import os

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="80" height="80">
  <defs>
    <!-- Soft shadow for the logo mark -->
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#1A56DB" flood-opacity="0.15"/>
    </filter>
  </defs>

  <!-- Logo Mark: Rounded UK Blue Square -->
  <g transform="translate(16, 16)" filter="url(#shadow)">
    <rect width="48" height="48" rx="12" fill="#1A56DB" />
    
    <!-- Modern Calculator/Check Icon inside the square -->
    <!-- Calculator Outline -->
    <rect x="12" y="10" width="24" height="28" rx="4" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    <!-- Display -->
    <line x1="16" y1="16" x2="32" y2="16" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
    <!-- Buttons -->
    <circle cx="16" cy="24" r="1.5" fill="#FFFFFF"/>
    <circle cx="24" cy="24" r="1.5" fill="#FFFFFF"/>
    <circle cx="32" cy="24" r="1.5" fill="#FFFFFF"/>
    <circle cx="16" cy="30" r="1.5" fill="#FFFFFF"/>
    <circle cx="24" cy="30" r="1.5" fill="#FFFFFF"/>
    <!-- A small checkmark instead of the last button to symbolize completion/compliance -->
    <path d="M29 30 L31 32 L35 28" fill="none" stroke="#25D366" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
</svg>
"""

os.makedirs("brand_assets/svg", exist_ok=True)
with open("brand_assets/svg/logo_icon.svg", "w") as f:
    f.write(svg_content)

print("Generated brand_assets/svg/logo_icon.svg")
