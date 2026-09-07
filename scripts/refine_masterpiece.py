import math

phi = (1 + math.sqrt(5)) / 2

OBSIDIAN = "#0B0F19"
ADMIRALTY = "#1D4ED8"
GILT = "#C5A880"
CHALK = "#FFFFFF"
MUTED = "#64748B"
BORDER = "#1E293B"

# -------------------------------------------------------------
# CANDIDATE M1: The Savile Row Architectural Interlock
# Monoline stroke (3.5px stroke-width)
# Left: Stately Pillar 'I' (x=46, y=34..126) with refined architectural plinths
# Right/Center: Majestic 'A' (Apex at x=98, y=34).
# Left diagonal descends to x=68 at y=126.
# Right column drops vertically at x=114 (y=58..126) with diagonal apex link.
# Golden Ratio Ledger Beam: y = 84 in Hallmarked Gilt.
# -------------------------------------------------------------
svg_m1 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Precision Institutional Bounding Plaque -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="10" y="10" width="140" height="140" stroke="{BORDER}" stroke-width="1"/>
  <rect x="14" y="14" width="132" height="132" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.3"/>

  <!-- Left Stately Column: The 'I' of Invisible -->
  <g stroke="{CHALK}" stroke-width="3.5" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Vertical Pillar -->
    <line x1="46" y1="36" x2="46" y2="124"/>
    <!-- Architectural Plinths (Serifs) -->
    <line x1="36" y1="36" x2="56" y2="36"/>
    <line x1="36" y1="124" x2="56" y2="124"/>

    <!-- The 'A' Apex & Columns -->
    <!-- Apex at (98, 36) -->
    <!-- Left diagonal descends to (70, 124) -->
    <!-- Right leg descends to (118, 124) -->
    <line x1="98" y1="36" x2="70" y2="124"/>
    <line x1="98" y1="36" x2="118" y2="124"/>
    <!-- Plinths on 'A' -->
    <line x1="62" y1="124" x2="78" y2="124"/>
    <line x1="110" y1="124" x2="126" y2="124"/>
    <line x1="90" y1="36" x2="106" y2="36"/>
  </g>

  <!-- Golden Ratio Ledger Balance Beam (y = 80) in Hallmarked Antique Gilt -->
  <!-- Spanning from inner face of 'I' (46) across both legs of 'A' (83 to 109) -->
  <line x1="46" y1="80" x2="114" y2="80" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>
  
  <!-- Subtle Admiralty Blue Balance Point -->
  <rect x="78" y="78.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

# -------------------------------------------------------------
# CANDIDATE M2: The Bank of England Sovereign Ledger Portico
# Pure architectural symmetry where the two stately columns form the outer bounds (x=44, x=116)
# and the interlocking monogram creates both the classical Roman portico
# and the letters I + A in a single stroke of genius.
# Left column = 'I'
# The 'A' chevron springs from both columns to an apex at (80, 28)
# At the Golden Cut (y=78), the sovereign gold ledger beam spans across.
# In the center, a vertical hairline spine of the 'I' drops down.
# -------------------------------------------------------------
svg_m2 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Obsidian Slate Ground -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.35"/>

  <!-- Architectural Vector Paths -->
  <g stroke="{CHALK}" stroke-width="3" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Left Stately Pillar: 'I' (Debit Foundation) -->
    <line x1="46" y1="34" x2="46" y2="126"/>
    <line x1="36" y1="34" x2="56" y2="34"/>
    <line x1="36" y1="126" x2="56" y2="126"/>

    <!-- Right Stately Pillar: (Credit Foundation) -->
    <line x1="114" y1="34" x2="114" y2="126"/>
    <line x1="104" y1="34" x2="124" y2="34"/>
    <line x1="104" y1="126" x2="124" y2="126"/>

    <!-- The Architectural Pediment Apex (The 'A') -->
    <!-- Springs from (46, 78) to Apex (80, 34) and down to (114, 78) -->
    <polyline points="46,88 80,34 114,88"/>
  </g>

  <!-- The Golden Section Ledger Beam: Hallmarked Antique Gilt (#C5A880) -->
  <!-- Span: 46 to 114 at y = 88 -->
  <line x1="46" y1="88" x2="114" y2="88" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>
  
  <!-- Central Sovereign Gold Aperture Keystone -->
  <polygon points="80,34 76,42 84,42" fill="{GILT}"/>
  <circle cx="80" cy="88" r="2.5" fill="{ADMIRALTY}"/>
</svg>'''

# -------------------------------------------------------------
# CANDIDATE M3: The Bespoke Mayfair Monogram (Pure Interlocking IA Monolith)
# Stately architectural solid bars with hairline precision gaps (1.5px negative space).
# Left Pillar: The Monumental 'I' (x=42..54, y=34..126)
# Right Chevron: The Monumental 'A' (Apex at x=102, y=34, Right leg x=108..120, Left leg diagonal to x=72..84)
# Connected by a Hallmarked Gilt Ledger Bar (y=82) that passes BEHIND the 'I' and 'A'
# via mathematical hairline clearance.
# -------------------------------------------------------------
svg_m3 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.3"/>

  <!-- Left Column: The Monumental 'I' -->
  <rect x="44" y="34" width="10" height="92" fill="{CHALK}"/>
  <!-- Architectural Plinth Lines -->
  <line x1="36" y1="34" x2="62" y2="34" stroke="{CHALK}" stroke-width="2"/>
  <line x1="36" y1="126" x2="62" y2="126" stroke="{CHALK}" stroke-width="2"/>

  <!-- Right Structure: The Majestic 'A' -->
  <!-- Apex at (102, 34) -->
  <!-- Right Leg: Vertical Stately Pillar (x=108..118, y=56..126) -->
  <rect x="108" y="56" width="10" height="70" fill="{CHALK}"/>
  <line x1="102" y1="126" x2="124" y2="126" stroke="{CHALK}" stroke-width="2"/>
  
  <!-- Left Diagonal Strut of 'A' (from 102,34 down to 72,126) -->
  <polygon points="98,34 108,34 84,126 74,126" fill="{CHALK}"/>
  <!-- Apex connector -->
  <polygon points="98,34 118,56 108,56 98,42" fill="{CHALK}"/>

  <!-- The Golden Ratio Ledger Beam (Hallmarked Antique Gilt) -->
  <!-- Bridging from inner edge of 'I' (54) to inner edge of 'A' (108) at y=80 -->
  <line x1="54" y1="80" x2="108" y2="80" stroke="{GILT}" stroke-width="3" stroke-linecap="square"/>
  
  <!-- Sovereign Admiralty Accent Pivot -->
  <rect x="79" y="78.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

# -------------------------------------------------------------
# CANDIDATE M4: The Sovereign Architectural Portico (Pure Mathematical Perfection)
# Two stately vertical columns: Left column (x=46) is 'I', Right column (x=114) is right anchor of 'A'.
# Apex of 'A' is centered at x=80, y=34.
# Left diagonal of 'A' drops from (80,34) to (46,126).
# Right diagonal of 'A' drops from (80,34) to (114,126).
# Vertical 'I' column at x=46 rises straight up through the left foot.
# Vertical right column at x=114 rises straight up through the right foot.
# Golden Ratio crossbar connects them at y=78 in Antique Gilt.
# -------------------------------------------------------------
svg_m4 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Obsidian Slate Background Plaque -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.3"/>

  <!-- The Sovereign Vector Monogram: Strict Monoline 3.2px -->
  <g stroke="{CHALK}" stroke-width="3.2" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Left Stately Pillar: 'I' of Invisible -->
    <line x1="46" y1="34" x2="46" y2="126"/>
    <line x1="36" y1="34" x2="56" y2="34"/>
    <line x1="36" y1="126" x2="56" y2="126"/>

    <!-- Right Stately Pillar: Counterpart Column -->
    <line x1="114" y1="34" x2="114" y2="126"/>
    <line x1="104" y1="34" x2="124" y2="34"/>
    <line x1="104" y1="126" x2="124" y2="126"/>

    <!-- The Architectural Chevron (The 'A') -->
    <!-- Apex at (80, 34), descending diagonally to the base of both columns (46, 126) and (114, 126) -->
    <line x1="80" y1="34" x2="46" y2="126"/>
    <line x1="80" y1="34" x2="114" y2="126"/>
  </g>

  <!-- The Golden Section Ledger Beam: Hallmarked Antique Gilt (#C5A880) -->
  <!-- Positioned at Golden Ratio division: (126 - 34) / 1.618 = 56.86 => 126 - 56.86 = 69.14 or 34 + 56.86 = 90.86 -->
  <!-- Crossbar at y = 82 bridges across both pillars -->
  <line x1="46" y1="82" x2="114" y2="82" stroke="{GILT}" stroke-width="2.5" stroke-linecap="square"/>

  <!-- Admiralty Blue Central Trust Pivot -->
  <rect x="78.5" y="80.5" width="3" height="3" fill="{ADMIRALTY}"/>
</svg>'''

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/m1.svg', 'w') as f:
    f.write(svg_m1)
with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/m2.svg', 'w') as f:
    f.write(svg_m2)
with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/m3.svg', 'w') as f:
    f.write(svg_m3)
with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/m4.svg', 'w') as f:
    f.write(svg_m4)

print("M1, M2, M3, M4 written.")
