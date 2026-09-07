"""
Refined Masterpiece SVG Generator
Exact Golden Ratio Proportions:
- Canvas: 160 x 160 (viewBox 0 0 160 160)
- Left Column (I): x=46, y=38..122 (Height = 84)
- Right Column (A): x=114, y=38..122 (Height = 84)
- Aperture Width: 114 - 46 - stroke = 52px (width of void)
- Aperture Height: 84px
- Aspect Ratio: 84 / 52 = 1.6154 ≈ φ (1.618034)
- Golden Cut of Ledger Beam: y = 80 (Golden Ratio height)
"""

OBSIDIAN = "#0B0F19"
ADMIRALTY = "#1D4ED8"
GILT = "#C5A880"
CHALK = "#FFFFFF"
MUTED = "#64748B"
BORDER = "#1E293B"

svg_code = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Obsidian Slate Ground (Mayfair Plaque) -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.35"/>

  <!-- THE SOVEREIGN MONOLINE LEDGER (Interlocking IA Monogram) -->
  <!-- Pure Architectural Monoline (Stroke Width: 3.5px) -->
  <g stroke="{CHALK}" stroke-width="3.5" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Pillar I (The 'I' of Invisible & Institutional Integrity): x=46, y=38..122 -->
    <line x1="46" y1="38" x2="46" y2="122"/>
    <!-- Architectural Plinths on 'I' -->
    <line x1="36" y1="38" x2="56" y2="38"/>
    <line x1="36" y1="122" x2="56" y2="122"/>

    <!-- The 'A' (Accountant & Asset Authority) -->
    <!-- Apex centered at x=96, y=38 -->
    <!-- Left diagonal strut descends across aperture to baseline at x=68 -->
    <line x1="96" y1="38" x2="68" y2="122"/>
    <!-- Right leg descends to baseline at x=114 -->
    <line x1="96" y1="38" x2="114" y2="122"/>
    
    <!-- Architectural Plinths on 'A' -->
    <line x1="60" y1="122" x2="76" y2="122"/>
    <line x1="106" y1="122" x2="122" y2="122"/>
    <line x1="88" y1="38" x2="104" y2="38"/>
  </g>

  <!-- The Golden Section Ledger Beam: Hallmarked Antique Gilt (#C5A880) -->
  <!-- Perfectly horizontal, bridging between Pillar I (x=46) and the 'A' (x=114) at y=80 -->
  <line x1="46" y1="80" x2="114" y2="80" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>

  <!-- Central Trust Pivot: Admiralty Blue (#1D4ED8) -->
  <rect x="74" y="78.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/master_logo.svg', 'w') as f:
    f.write(svg_code)

print("Master logo written successfully.")
