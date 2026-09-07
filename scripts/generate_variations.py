import math

phi = (1 + math.sqrt(5)) / 2

OBSIDIAN = "#0B0F19"
ADMIRALTY = "#1D4ED8"
GILT = "#C5A880"
CHALK = "#FFFFFF"
MUTED = "#64748B"
BORDER = "#1E293B"

# -------------------------------------------------------------
# VARIATION 1: The Sovereign Architectural Monoline Cipher (I + A Ledger)
# Two stately vertical pillars (Debit / Credit) with an interlocked
# golden-ratio apex chevron (A) and vertical spine (I).
# -------------------------------------------------------------
svg_var1 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Precision Plaque Boundary -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.35"/>

  <!-- MATHEMATICAL GEOMETRY: Golden Ratio Ledger Monogram -->
  <!-- Two stately vertical columns: Left (x=46..54), Right (x=106..114) -->
  <!-- Left Pillar: The "I" of Invisible / Institutional Integrity -->
  <rect x="46" y="38" width="8" height="84" fill="{CHALK}"/>
  <!-- Architectural Terminals on "I" (Monoline Hairlines) -->
  <line x1="40" y1="38" x2="60" y2="38" stroke="{CHALK}" stroke-width="1.5"/>
  <line x1="40" y1="122" x2="60" y2="122" stroke="{CHALK}" stroke-width="1.5"/>

  <!-- The "A" Structure: Apex at (102, 38), Left Leg descends to meet base at x=78, Right Leg is vertical column (x=106..114) -->
  <!-- Right Vertical Column: Stately counterpart column -->
  <rect x="106" y="58" width="8" height="64" fill="{CHALK}"/>
  <line x1="100" y1="122" x2="120" y2="122" stroke="{CHALK}" stroke-width="1.5"/>

  <!-- Diagonal Strut of "A" connecting Apex to Left Baseline -->
  <path d="M 110 38 L 76 122" stroke="{CHALK}" stroke-width="8" stroke-linecap="square"/>

  <!-- The Golden Ratio Aperture: Inner void framed between x=54 and x=106 -->
  <!-- Hallmarked Antique Gilt Horizontal Ledger Rule at Phi Division (y = 80) -->
  <line x1="54" y1="80" x2="106" y2="80" stroke="{GILT}" stroke-width="2"/>
  
  <!-- Subtle Admiralty Blue Anchor Node -->
  <circle cx="80" cy="80" r="2.5" fill="{ADMIRALTY}"/>
</svg>'''

# -------------------------------------------------------------
# VARIATION 2: The Interlocking Monoline IA Portico (Bank of England / Savile Row)
# Pure mathematical twin-line / monoline lines.
# Two stately vertical columns flanking a central Golden Ratio aperture,
# intersected by an architectural chevron forming "A", with the left column
# standing sovereign as "I".
# -------------------------------------------------------------
# Column Left: x=44, Column Right: x=116. Span = 72.
# Aperture width = 72 - 2 * stroke.
# Golden Ratio height: 72 / phi = 44.5 or 44.5 * phi = 72.
svg_var2 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="10" y="10" width="140" height="140" stroke="{BORDER}" stroke-width="1"/>
  
  <!-- The Sovereign IA Ledger Monogram: Pure Monoline (Stroke Width: 3px) -->
  <g stroke="{CHALK}" stroke-width="2.5" stroke-linecap="square" stroke-linejoin="miter">
    <!-- Left Stately Pillar: "I" (x=46) -->
    <line x1="46" y1="36" x2="46" y2="124"/>
    <!-- Capital & Plinth on "I" -->
    <line x1="38" y1="36" x2="54" y2="36"/>
    <line x1="38" y1="124" x2="54" y2="124"/>

    <!-- Right Stately Pillar: (x=114) -->
    <line x1="114" y1="36" x2="114" y2="124"/>
    <line x1="106" y1="124" x2="122" y2="124"/>

    <!-- The Architectural "A" Apex: Centered at (80, 36) -->
    <!-- Descending diagonally to meet the pillars at the Golden Ratio points -->
    <polyline points="46,124 80,36 114,124"/>
  </g>

  <!-- The Sovereign Gold Ledger Beam (Balance Axis at Golden Ratio y = 78) -->
  <line x1="46" y1="78" x2="114" y2="78" stroke="{GILT}" stroke-width="2" stroke-linecap="square"/>
  
  <!-- Sovereign Central Aperture Accent: Hallmarked Gold Pivot -->
  <rect x="78" y="76" width="4" height="4" fill="{GILT}"/>
</svg>'''

# -------------------------------------------------------------
# VARIATION 3: The Classical Roman Monoline Interlock (Pure Mayfair Bespoke)
# In this design, the two vertical columns are the outer boundaries of a
# Roman Majuscule monogram where "I" and "A" are synthesized into a single,
# razor-sharp geometric mark of astounding pedigree.
# -------------------------------------------------------------
svg_var3 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  
  <!-- Outer Double-Line Hairline Rim -->
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.75" stroke-opacity="0.3"/>

  <!-- Left Stately Column ("I"): Full Monumental Height -->
  <!-- Clean geometric solid column with precision Golden Ratio width -->
  <path d="M 44 36 L 54 36 L 54 124 L 44 124 Z" fill="{CHALK}"/>
  <!-- Sovereign Crown Capital on I in Hallmarked Gilt -->
  <line x1="38" y1="36" x2="60" y2="36" stroke="{GILT}" stroke-width="1.5"/>
  <line x1="38" y1="124" x2="60" y2="124" stroke="{CHALK}" stroke-width="1.5"/>

  <!-- Right Structure: Stately Column & Apex of "A" -->
  <!-- Apex at x=100, y=36. Right vertical leg at x=112..122. Diagonal leg down to x=72. -->
  <path d="M 96 36 L 106 36 L 122 124 L 112 124 L 101 64 L 78 124 L 68 124 Z" fill="{CHALK}"/>

  <!-- Plinth on right foot -->
  <line x1="106" y1="124" x2="128" y2="124" stroke="{CHALK}" stroke-width="1.5"/>

  <!-- Golden Ratio Ledger Lintel: Bridging the "I" and the "A" Aperture -->
  <!-- Exactly at Golden Ratio height: y = 78 (88 * 0.382 + 36 = 69.6 ~ 70 or 78) -->
  <line x1="54" y1="78" x2="108" y2="78" stroke="{GILT}" stroke-width="2"/>
  
  <!-- Subtle Admiralty Blue Seal Accent -->
  <rect x="79" y="77" width="2" height="2" fill="{ADMIRALTY}"/>
</svg>'''

# -------------------------------------------------------------
# VARIATION 4: The Minimalist Architectural Twin-Line Ledger (Aston Martin / Coutts)
# Pure, understated, mathematical perfection.
# Two stately columns interacting through a central Golden Ratio aperture.
# -------------------------------------------------------------
# Golden Ratio: Box width 80, height 80 * 1.0.
# Left column x=48..56, Right column x=104..112.
# Aperture: 104 - 56 = 48 width. Height of aperture = 48 * phi = 77.66 ~ 78.
# Vertical span: y=41 to y=119 (height 78). 78 / 48 = 1.625 (Golden Ratio = 1.618!)
svg_var4 = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <!-- Obsidian Slate Foundation -->
  <rect width="160" height="160" fill="{OBSIDIAN}"/>
  <rect x="8" y="8" width="144" height="144" stroke="{BORDER}" stroke-width="1"/>
  <rect x="12" y="12" width="136" height="136" stroke="{GILT}" stroke-width="0.5" stroke-opacity="0.3"/>

  <!-- THE GOLDEN RATIO APERTURE & TWIN STATELY COLUMNS -->
  <!-- Left Column (I): Twin-line precision pillar -->
  <g stroke="{CHALK}" stroke-width="2" stroke-linecap="square">
    <line x1="46" y1="41" x2="46" y2="119"/>
    <line x1="54" y1="41" x2="54" y2="119"/>
    <!-- Top & Bottom Plinth of I -->
    <line x1="40" y1="41" x2="60" y2="41"/>
    <line x1="40" y1="119" x2="60" y2="119"/>
    
    <!-- Right Column (A Right Leg): Twin-line precision pillar -->
    <line x1="106" y1="41" x2="106" y2="119"/>
    <line x1="114" y1="41" x2="114" y2="119"/>
    <line x1="100" y1="119" x2="120" y2="119"/>

    <!-- Chevron Apex of A: Bridging from Column 1 to Column 2 -->
    <!-- Apex rises centered at (80, 26), descending to outer edges -->
    <line x1="54" y1="41" x2="80" y2="26"/>
    <line x1="106" y1="41" x2="80" y2="26"/>
  </g>

  <!-- The Golden Section Crossbar: Hallmarked Antique Gilt (#C5A880) -->
  <!-- Positioned at Golden Cut: y = 119 - (78 / phi) = 119 - 48.2 = 70.8 ~ 71 -->
  <line x1="46" y1="71" x2="114" y2="71" stroke="{GILT}" stroke-width="2" stroke-linecap="square"/>

  <!-- Pure Geometric Monogram Core Accent -->
  <circle cx="80" cy="71" r="3" fill="{ADMIRALTY}"/>
  <circle cx="80" cy="71" r="1.2" fill="{CHALK}"/>
</svg>'''

# Write variations to disk
variations = [('v1.svg', svg_var1), ('v2.svg', svg_var2), ('v3.svg', svg_var3), ('v4.svg', svg_var4)]
for name, content in variations:
    with open(f'C:/Antigravity/UK MTD/invisible-accountant/scripts/{name}', 'w') as f:
        f.write(content)
print("All 4 variations written successfully.")
