import math

phi = (1 + math.sqrt(5)) / 2

OBSIDIAN = "#0B0F19"
ADMIRALTY = "#1D4ED8"
GILT = "#C5A880"
CHALK = "#FFFFFF"
MUTED = "#64748B"
BORDER = "#1E293B"

# Let's create two refined interlock studies:
# Study A: Razor-sharp monoline interlock with negative space pass-through
# Study B: Stately architectural balanced ledger cipher (Luca Pacioli / Bank of England)

study_a = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.3"/>

  <!-- Left Stately Pillar 'I' -->
  <g stroke="{CHALK}" stroke-width="3.6" stroke-linecap="square" stroke-linejoin="miter">
    <line x1="44" y1="36" x2="44" y2="124"/>
    <!-- Architectural Plinths -->
    <line x1="34" y1="36" x2="54" y2="36"/>
    <line x1="34" y1="124" x2="54" y2="124"/>

    <!-- 'A' Apex and Columns -->
    <line x1="98" y1="36" x2="70" y2="124"/>
    <line x1="98" y1="36" x2="120" y2="124"/>
    <!-- 'A' Plinths -->
    <line x1="62" y1="124" x2="78" y2="124"/>
    <line x1="112" y1="124" x2="128" y2="124"/>
    <line x1="90" y1="36" x2="106" y2="36"/>
  </g>

  <!-- Hallmarked Antique Gilt Ledger Beam at Golden Section y = 82 -->
  <!-- Anchored from I (x=44) across A (to x=116) -->
  <line x1="44" y1="82" x2="116" y2="82" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>

  <!-- Sovereign Trust Anchor: Admiralty Blue Pivot -->
  <rect x="76" y="80.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

study_b = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.3"/>

  <!-- THE BALANCED LEDGER CIPHER: Dual Architectural Columns + Golden Ratio Aperture -->
  <!-- Left Pillar (Debit / Invisible 'I'): x=44..52 -->
  <rect x="44" y="36" width="8" height="88" fill="{CHALK}"/>
  <line x1="38" y1="36" x2="58" y2="36" stroke="{CHALK}" stroke-width="2"/>
  <line x1="38" y1="124" x2="58" y2="124" stroke="{CHALK}" stroke-width="2"/>

  <!-- Right Pillar (Credit / Authority 'A' Stem): x=108..116 -->
  <rect x="108" y="36" width="8" height="88" fill="{CHALK}"/>
  <line x1="102" y1="36" x2="122" y2="36" stroke="{CHALK}" stroke-width="2"/>
  <line x1="102" y1="124" x2="122" y2="124" stroke="{CHALK}" stroke-width="2"/>

  <!-- The Architectural Lintel Chevron: Forming the Apex of 'A' -->
  <!-- Rises from both columns to meet at apex (80, 24) -->
  <path d="M 52 36 L 80 24 L 108 36" stroke="{CHALK}" stroke-width="3" stroke-linecap="square" stroke-linejoin="miter"/>

  <!-- The Golden Ratio Ledger Fulcrum Beam: Hallmarked Antique Gilt -->
  <!-- Spans the central aperture (52 to 108) at Golden Ratio cut y = 78 -->
  <line x1="44" y1="78" x2="116" y2="78" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>

  <!-- Central Sanctuary Aperture: Width = 56, Height = 56 * 1.618 = 90 (matches overall height!) -->
  <!-- Golden Keystone -->
  <polygon points="80,24 76,32 84,32" fill="{GILT}"/>
  <rect x="78.5" y="76.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/study_a.svg', 'w') as f:
    f.write(study_a)
with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/study_b.svg', 'w') as f:
    f.write(study_b)
print("Studies A and B written.")
