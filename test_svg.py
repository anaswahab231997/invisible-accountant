import xml.etree.ElementTree as ET

# Full Horizontal Lockup (For Slide 1 Banner / Headers)
svg_horizontal = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 130" width="100%" height="100%" fill="none">
  <defs>
    <!-- Background Shield Gradient -->
    <linearGradient id="iaShieldBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#131F37"/>
      <stop offset="50%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#090E1A"/>
    </linearGradient>

    <!-- Shield Border Gradient -->
    <linearGradient id="iaShieldBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.8"/>
      <stop offset="50%" stop-color="#1D4ED8" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#D4AF37" stop-opacity="0.6"/>
    </linearGradient>

    <!-- Heritage Royal Primary Gradient -->
    <linearGradient id="iaHeritageGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#60A5FA"/>
      <stop offset="35%" stop-color="#2563EB"/>
      <stop offset="100%" stop-color="#1D4ED8"/>
    </linearGradient>

    <!-- Heritage Royal Accent (Darker Facet) -->
    <linearGradient id="iaFacetGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1D4ED8"/>
      <stop offset="100%" stop-color="#1E3A8A"/>
    </linearGradient>

    <!-- Guildhall Sovereign Gold Gradient -->
    <linearGradient id="iaGoldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FEF08A"/>
      <stop offset="40%" stop-color="#FACC15"/>
      <stop offset="100%" stop-color="#CA8A04"/>
    </linearGradient>

    <!-- Treasury Emerald Clearance Gradient -->
    <linearGradient id="iaEmeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34D399"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>

    <!-- Soft Glow Filter -->
    <filter id="iaGlow" x="-20%" y="-20%" width="140%" height="140%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#1D4ED8" flood-opacity="0.35"/>
    </filter>

    <!-- Gold Spark Glow -->
    <filter id="goldGlow" x="-50%" y="-50%" width="200%" height="200%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="0" stdDeviation="3" flood-color="#FACC15" flood-opacity="0.7"/>
    </filter>
  </defs>

  <!-- ================= SYMBOL: THE INVISIBLE LEDGER APERTURE ================= -->
  <g transform="translate(15, 15)">
    <!-- Outer Shield / Precision Squircle -->
    <rect x="0" y="0" width="100" height="100" rx="22" fill="url(#iaShieldBg)" stroke="url(#iaShieldBorder)" stroke-width="1.5" filter="url(#iaGlow)"/>
    <!-- Inner Hairline Bevel -->
    <rect x="4" y="4" width="92" height="92" rx="18" fill="none" stroke="rgba(255, 255, 255, 0.06)" stroke-width="1"/>

    <!-- Subtle Isometric Sub-grid -->
    <line x1="20" y1="50" x2="80" y2="50" stroke="#1E293B" stroke-width="0.75" stroke-dasharray="2 3"/>
    <line x1="50" y1="20" x2="50" y2="80" stroke="#1E293B" stroke-width="0.75" stroke-dasharray="2 3"/>

    <!-- Left Pillar: The I of Invisible &amp; Institutional Integrity -->
    <rect x="22" y="28" width="12" height="46" rx="2.5" fill="url(#iaHeritageGrad)"/>
    <!-- Facet Highlight on I -->
    <rect x="22" y="28" width="4" height="46" rx="1.5" fill="#93C5FD" fill-opacity="0.4"/>
    <!-- The Sovereign Crown Node atop the I -->
    <circle cx="28" cy="19" r="4.5" fill="url(#iaGoldGrad)" filter="url(#goldGlow)"/>
    <circle cx="28" cy="19" r="1.8" fill="#FFFFFF"/>

    <!-- Right Chevron Apex: The A of Accountant &amp; Asset -->
    <!-- Centered at x=62: Outer feet 42 to 82, Top 56 to 68 -->
    <path d="M 42 74 L 56 28 L 68 28 L 82 74 L 72 74 L 67 56 L 57 56 L 52 74 Z" fill="url(#iaHeritageGrad)"/>
    <!-- 3D Shadow Facet -->
    <path d="M 62 28 L 68 28 L 82 74 L 72 74 L 67 56 Z" fill="url(#iaFacetGrad)" fill-opacity="0.45"/>

    <!-- The Negative Space Aperture (The Invisible Ledger Window) -->
    <polygon points="62,38 57,51 67,51" fill="#0F172A"/>

    <!-- The Floating Digital Link Spark (Guildhall Sovereign Gold Pivot) -->
    <circle cx="62" cy="45" r="2.8" fill="url(#iaGoldGrad)" filter="url(#goldGlow)"/>

    <!-- Automated HMAC Digital Link Line -->
    <path d="M 34 74 L 42 74" stroke="url(#iaGoldGrad)" stroke-width="1.5" stroke-linecap="round"/>

    <!-- Precision HMRC Compliance Checkpoint (Bottom Right Status Accent) -->
    <path d="M 78 78 L 84 84 L 90 75" fill="none" stroke="url(#iaEmeraldGrad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <!-- ================= BESPOKE WORDMARK LOCKUP ================= -->
  <g transform="translate(138, 26)">
    <!-- Institutional Compliance Pill -->
    <g transform="translate(0, 0)">
      <rect x="0" y="0" width="186" height="18" rx="9" fill="rgba(16, 185, 129, 0.12)" stroke="rgba(16, 185, 129, 0.35)" stroke-width="1"/>
      <circle cx="10" cy="9" r="3.5" fill="#10B981"/>
      <text x="20" y="12.5" font-family="'Geist Mono', 'SF Mono', Consolas, monospace" font-size="8" font-weight="600" letter-spacing="0.16em" fill="#34D399">HMRC MTD 2026 AUDITED</text>
    </g>

    <!-- Primary Brand Name: INVISIBLE -->
    <text x="0" y="44" font-family="'Cabinet Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="27" font-weight="600" letter-spacing="0.16em" fill="#FFFFFF">
      INVISIBLE
    </text>

    <!-- Primary Brand Name: ACCOUNTANT -->
    <text x="0" y="74" font-family="'Cabinet Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="27" font-weight="800" letter-spacing="0.06em" fill="url(#iaHeritageGrad)">
      ACCOUNTANT
    </text>

    <!-- Statutory Subtext Descriptor -->
    <g transform="translate(1, 94)">
      <text x="0" y="0" font-family="'Geist Mono', 'SF Mono', Consolas, monospace" font-size="9" font-weight="500" letter-spacing="0.22em" fill="#94A3B8">
        LONDON FINANCIAL DISTRICT • MTD SECURE
      </text>
      <!-- Trust Node Indicator -->
      <circle cx="316" cy="-3" r="3" fill="#D4AF37"/>
    </g>
  </g>
</svg>'''

# Standalone Monogram Crest (For Square Viewports, Avatars, Slide 1 Sanctuary Card)
svg_crest = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
  <defs>
    <linearGradient id="cBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#172554"/>
      <stop offset="50%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#050811"/>
    </linearGradient>
    <linearGradient id="cBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.9"/>
      <stop offset="50%" stop-color="#1D4ED8" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="#D4AF37" stop-opacity="0.7"/>
    </linearGradient>
    <linearGradient id="cRoyal" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#60A5FA"/>
      <stop offset="40%" stop-color="#2563EB"/>
      <stop offset="100%" stop-color="#1D4ED8"/>
    </linearGradient>
    <linearGradient id="cFacet" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1D4ED8"/>
      <stop offset="100%" stop-color="#172554"/>
    </linearGradient>
    <linearGradient id="cGold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FEF08A"/>
      <stop offset="40%" stop-color="#FACC15"/>
      <stop offset="100%" stop-color="#CA8A04"/>
    </linearGradient>
    <linearGradient id="cEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34D399"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <filter id="cGlow" x="-20%" y="-20%" width="140%" height="140%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#1D4ED8" flood-opacity="0.45"/>
    </filter>
    <filter id="cSpark" x="-60%" y="-60%" width="220%" height="220%" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="0" stdDeviation="4" flood-color="#FACC15" flood-opacity="0.8"/>
    </filter>
  </defs>
  
  <!-- Outer Shield Container -->
  <rect x="10" y="10" width="140" height="140" rx="32" fill="url(#cBg)" stroke="url(#cBorder)" stroke-width="2" filter="url(#cGlow)"/>
  <!-- Inner Hairline Bevel -->
  <rect x="16" y="16" width="128" height="128" rx="26" fill="none" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1"/>

  <!-- Subtle Alignment Crosshairs -->
  <line x1="30" y1="80" x2="130" y2="80" stroke="#1E293B" stroke-width="0.8" stroke-dasharray="3 3"/>
  <line x1="80" y1="30" x2="80" y2="130" stroke="#1E293B" stroke-width="0.8" stroke-dasharray="3 3"/>

  <!-- Left Pillar: The I of Invisible &amp; Institutional Integrity -->
  <rect x="36" y="46" width="18" height="66" rx="4" fill="url(#cRoyal)"/>
  <rect x="36" y="46" width="6" height="66" rx="2" fill="#93C5FD" fill-opacity="0.45"/>
  <circle cx="45" cy="33" r="6.5" fill="url(#cGold)" filter="url(#cSpark)"/>
  <circle cx="45" cy="33" r="2.5" fill="#FFFFFF"/>

  <!-- Right Chevron Apex: The A of Accountant &amp; Asset (Centered at x=98) -->
  <path d="M 68 112 L 89 46 L 107 46 L 128 112 L 112 112 L 105 88 L 91 88 L 84 112 Z" fill="url(#cRoyal)"/>
  <path d="M 98 46 L 107 46 L 128 112 L 112 112 L 105 88 Z" fill="url(#cFacet)" fill-opacity="0.5"/>

  <!-- The Negative Space Aperture (The Invisible Ledger Portal) -->
  <polygon points="98,61 90,81 106,81" fill="#0F172A"/>

  <!-- The Floating Digital Link Spark (Guildhall Sovereign Gold Pivot) -->
  <circle cx="98" cy="72" r="4" fill="url(#cGold)" filter="url(#cSpark)"/>

  <!-- Automated HMAC Digital Link Line -->
  <path d="M 54 112 L 68 112" stroke="url(#cGold)" stroke-width="2.5" stroke-linecap="round"/>

  <!-- HMRC Statutory Clearance Seal Accent -->
  <path d="M 120 120 L 128 128 L 136 116" fill="none" stroke="url(#cEmerald)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Validate XML for both
ET.fromstring(svg_horizontal)
ET.fromstring(svg_crest)

with open("assets/invisible_accountant_logo.svg", "w", encoding="utf-8") as f:
    f.write(svg_horizontal)

with open("assets/invisible_accountant_crest.svg", "w", encoding="utf-8") as f:
    f.write(svg_crest)

print("ALL SVG ASSETS VALIDATED AND SAVED TO assets/")
