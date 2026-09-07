"""
Generate Clean, Pure British Institutional SVG Assets
Zero AI Slop: No gradients, no glows, no drop shadows, no sci-fi gimmicks.
"""

OBSIDIAN = "#0B0F19"
ADMIRALTY = "#1D4ED8"
GILT = "#C5A880"
CHALK = "#FFFFFF"
MUTED = "#64748B"
BORDER = "#1E293B"

# 1. Primary Crest / Monogram (160x160)
crest_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Obsidian Slate Foundation Plaque -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.35"/>

  <!-- THE SOVEREIGN MONOLINE LEDGER (Interlocking IA Monogram) -->
  <!-- Mathematical Grid: Two Stately Columns, Golden Ratio Aperture (phi = 1.618) -->
  <g stroke="{CHALK}" stroke-width="3.5" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Pillar I: Stately Left Column of Invisible & Institutional Integrity (x=46, y=38..122) -->
    <line x1="46" y1="38" x2="46" y2="122"/>
    <!-- Classical Plinth & Capital Terminals on Pillar I -->
    <line x1="36" y1="38" x2="56" y2="38"/>
    <line x1="36" y1="122" x2="56" y2="122"/>

    <!-- Pillar & Chevron A: Accountant & Asset Foundation -->
    <!-- Apex at (96, 38) -->
    <!-- Left diagonal strut descends across aperture to baseline at x=68 -->
    <line x1="96" y1="38" x2="68" y2="122"/>
    <!-- Right leg descends vertically to baseline at x=114 -->
    <line x1="96" y1="38" x2="114" y2="122"/>
    
    <!-- Classical Plinths on Chevron A -->
    <line x1="60" y1="122" x2="76" y2="122"/>
    <line x1="106" y1="122" x2="122" y2="122"/>
    <line x1="88" y1="38" x2="104" y2="38"/>
  </g>

  <!-- The Golden Section Ledger Beam: Hallmarked Antique Gilt (#C5A880) -->
  <!-- Crossbar at y = 80 bridges Pillar I across the Aperture -->
  <line x1="46" y1="80" x2="114" y2="80" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>

  <!-- Central Trust Pivot: Flat Admiralty Blue (#1D4ED8) -->
  <rect x="74" y="78.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

# 2. Standalone App Icon / Monogram (128x128)
monogram_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="100%" height="100%" fill="none">
  <rect width="128" height="128" fill="{OBSIDIAN}"/>
  <rect x="6" y="6" width="116" height="116" stroke="{BORDER}" stroke-width="1"/>
  <rect x="9" y="9" width="110" height="110" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.35"/>

  <g stroke="{CHALK}" stroke-width="3" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Pillar I (x=37, y=30..98) -->
    <line x1="37" y1="30" x2="37" y2="98"/>
    <line x1="29" y1="30" x2="45" y2="30"/>
    <line x1="29" y1="98" x2="45" y2="98"/>

    <!-- Chevron A (Apex 77, 30; Left 54, 98; Right 91, 98) -->
    <line x1="77" y1="30" x2="54" y2="98"/>
    <line x1="77" y1="30" x2="91" y2="98"/>
    <line x1="48" y1="98" x2="60" y2="98"/>
    <line x1="85" y1="98" x2="97" y2="98"/>
    <line x1="71" y1="30" x2="83" y2="30"/>
  </g>

  <!-- Golden Section Crossbar -->
  <line x1="37" y1="64" x2="91" y2="64" stroke="{GILT}" stroke-width="2" stroke-linecap="square"/>
  <rect x="59" y="63" width="2.5" height="2.5" fill="{ADMIRALTY}"/>
</svg>'''

# 3. Horizontal Master Lockup (600x120)
lockup_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 120" width="100%" height="100%" fill="none">
  <rect width="600" height="120" fill="{OBSIDIAN}"/>
  <rect x="6" y="6" width="588" height="108" stroke="{BORDER}" stroke-width="1"/>
  <rect x="9" y="9" width="582" height="102" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.25"/>

  <!-- Left Emblem: The Sovereign Monoline Ledger (Scaled: 80x80 at x=20, y=20) -->
  <g transform="translate(20, 20)">
    <rect width="80" height="80" fill="{OBSIDIAN}"/>
    <rect x="3" y="3" width="74" height="74" stroke="{BORDER}" stroke-width="0.75"/>
    
    <g stroke="{CHALK}" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter">
      <!-- Pillar I -->
      <line x1="23" y1="19" x2="23" y2="61"/>
      <line x1="18" y1="19" x2="28" y2="19"/>
      <line x1="18" y1="61" x2="28" y2="61"/>

      <!-- Chevron A -->
      <line x1="48" y1="19" x2="34" y2="61"/>
      <line x1="48" y1="19" x2="57" y2="61"/>
      <line x1="30" y1="61" x2="38" y2="61"/>
      <line x1="53" y1="61" x2="61" y2="61"/>
      <line x1="44" y1="19" x2="52" y2="19"/>
    </g>

    <!-- Golden Section Crossbar -->
    <line x1="23" y1="40" x2="57" y2="40" stroke="{GILT}" stroke-width="1.5" stroke-linecap="square"/>
    <rect x="37" y="39" width="2" height="2" fill="{ADMIRALTY}"/>
  </g>

  <!-- Divider Hairline -->
  <line x1="120" y1="24" x2="120" y2="96" stroke="{BORDER}" stroke-width="1"/>

  <!-- Wordmark Lockup -->
  <g transform="translate(142, 34)">
    <!-- Regulatory Status Micro-Bar -->
    <text x="0" y="0" font-family="'Geist Mono', 'SF Mono', Consolas, monospace" font-size="8.5" font-weight="600" letter-spacing="0.24em" fill="{GILT}">
      HMRC MAKING TAX DIGITAL 2026 · STATUTORY COMPLIANCE
    </text>

    <!-- Primary Title -->
    <text x="0" y="32" font-family="'Cabinet Grotesk', -apple-system, sans-serif" font-size="28" font-weight="700" letter-spacing="0.12em" fill="{CHALK}">
      INVISIBLE ACCOUNTANT
    </text>

    <!-- Subtitle Footnote -->
    <text x="0" y="56" font-family="'Geist Mono', 'SF Mono', Consolas, monospace" font-size="9" font-weight="400" letter-spacing="0.18em" fill="{MUTED}">
      LONDON FINANCIAL DISTRICT · SEIS / EIS ADVANCE ASSURANCE
    </text>
  </g>

  <!-- Right Quality Mark / Hallmarked Plaque -->
  <g transform="translate(520, 44)">
    <rect x="0" y="0" width="56" height="32" stroke="{BORDER}" stroke-width="1" fill="none"/>
    <text x="28" y="14" font-family="'Geist Mono', monospace" font-size="6.5" font-weight="600" letter-spacing="0.16em" fill="{GILT}" text-anchor="middle">
      MTD 2026
    </text>
    <text x="28" y="24" font-family="'Geist Mono', monospace" font-size="6.5" font-weight="500" letter-spacing="0.1em" fill="{MUTED}" text-anchor="middle">
      AUDITED
    </text>
  </g>
</svg>'''

# Write all three assets
with open('C:/Antigravity/UK MTD/invisible-accountant/assets/invisible_accountant_crest.svg', 'w', encoding='utf-8') as f:
    f.write(crest_svg)

with open('C:/Antigravity/UK MTD/invisible-accountant/assets/ia_monogram.svg', 'w', encoding='utf-8') as f:
    f.write(monogram_svg)

with open('C:/Antigravity/UK MTD/invisible-accountant/assets/invisible_accountant_logo.svg', 'w', encoding='utf-8') as f:
    f.write(lockup_svg)

print("All assets successfully deployed to assets/ directory.")
