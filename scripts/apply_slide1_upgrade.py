import shutil

# Create backup
shutil.copyfile(
    'C:/Antigravity/UK MTD/invisible-accountant/investor_jury_deck.html',
    'C:/Antigravity/UK MTD/invisible-accountant/investor_jury_deck.html.bak'
)

with open('C:/Antigravity/UK MTD/invisible-accountant/investor_jury_deck.html', 'r', encoding='utf-8') as f:
    deck_html = f.read()

# CSS to inject before </style>
css_injection = '''
        /* -------------------------------------------------------------
           SLIDE 1: SINGLE-PLANE EXPANSIVE EDITORIAL MEMORANDUM
           British Institutional Elegance (Coutts / Rothschild / Savile Row)
           Zero AI Slop: No neon gradients, no glow filters, no drop shadows
        ------------------------------------------------------------- */
        #slide-1.slide {
            display: flex;
            padding: 0;
            align-items: stretch;
            justify-content: stretch;
        }

        .editorial-memorandum {
            width: 100%;
            height: 100%;
            background: #0B0F19;
            border: 1px solid #1E293B;
            position: relative;
            padding: clamp(36px, 4.5vw, 64px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: hidden;
            box-sizing: border-box;
        }

        .editorial-memorandum::before {
            content: "";
            position: absolute;
            top: 12px; left: 12px; right: 12px; bottom: 12px;
            border: 1px solid rgba(197, 168, 128, 0.2);
            pointer-events: none;
        }

        .memorandum-eyebrow {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            z-index: 2;
            gap: 16px;
        }

        .eyebrow-text {
            font-family: 'Geist Mono', monospace;
            font-size: clamp(0.68rem, 0.88vw, 0.75rem);
            font-weight: 600;
            letter-spacing: clamp(0.14em, 0.2vw, 0.25em);
            text-transform: uppercase;
            color: #C5A880;
            white-space: nowrap;
        }

        .eyebrow-id {
            font-family: 'Geist Mono', monospace;
            font-size: 0.72rem;
            font-weight: 400;
            letter-spacing: 0.15em;
            color: #64748B;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .memorandum-hero {
            display: grid;
            grid-template-columns: 7fr 5fr;
            gap: clamp(36px, 4.5vw, 64px);
            align-items: center;
            flex: 1;
            padding: clamp(20px, 2.8vw, 40px) 0;
            z-index: 2;
        }

        .hero-left {
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .hero-title {
            font-family: 'Cabinet Grotesk', sans-serif;
            font-size: clamp(2.8rem, 4.8vw, 4.2rem);
            font-weight: 700;
            letter-spacing: -0.035em;
            line-height: 1.05;
            color: #FFFFFF;
            margin-bottom: 20px;
        }

        .hero-proposition {
            font-size: clamp(1.25rem, 1.7vw, 1.5rem);
            font-weight: 300;
            line-height: 1.5;
            color: #94A3B8;
            margin-bottom: 16px;
            max-width: 580px;
        }

        .hero-detail {
            font-size: clamp(0.92rem, 1.05vw, 1.02rem);
            font-weight: 400;
            line-height: 1.6;
            color: #64748B;
            max-width: 540px;
        }

        .hero-right {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-left: 1px solid rgba(255, 255, 255, 0.08);
            padding-left: clamp(28px, 3.5vw, 56px);
            height: 100%;
        }

        .emblem-wrapper {
            width: clamp(170px, 18vw, 220px);
            height: clamp(170px, 18vw, 220px);
            position: relative;
        }

        .emblem-inscription {
            margin-top: 18px;
            text-align: center;
        }

        .emblem-title {
            font-family: 'Cabinet Grotesk', sans-serif;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.18em;
            color: #FFFFFF;
            text-transform: uppercase;
        }

        .emblem-sub {
            font-family: 'Geist Mono', monospace;
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.2em;
            color: #64748B;
            margin-top: 6px;
            text-transform: uppercase;
        }

        .memorandum-footer {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-top: 18px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            z-index: 2;
            gap: 20px;
        }

        .thesis-block {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .thesis-label {
            font-family: 'Geist Mono', monospace;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.2em;
            color: #C5A880;
            text-transform: uppercase;
        }

        .thesis-text {
            font-size: clamp(0.85rem, 0.98vw, 0.95rem);
            font-weight: 400;
            color: #E2E8F0;
            letter-spacing: -0.01em;
        }

        .status-block {
            text-align: right;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
            flex-shrink: 0;
        }

        .status-badge {
            font-family: 'Geist Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            color: #C5A880;
            border: 1px solid rgba(197, 168, 128, 0.35);
            padding: 5px 12px;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .status-note {
            font-family: 'Geist Mono', monospace;
            font-size: 0.68rem;
            letter-spacing: 0.12em;
            color: #64748B;
            text-transform: uppercase;
            white-space: nowrap;
        }
    </style>'''

# Slide 1 Replacement HTML
slide1_replacement = '''        <!-- Slide 1: British Institutional Masterpiece -->
        <div class="slide active" id="slide-1">
            <div class="editorial-memorandum">
                <!-- Top Regulatory Inscription -->
                <div class="memorandum-eyebrow">
                    <div class="eyebrow-text">HMRC Making Tax Digital 2026 · Statutory Compliance Infrastructure</div>
                    <div class="eyebrow-id">Document Ref: IA-MTD-2026-PRESEED</div>
                </div>

                <!-- Main Hero: 7:5 Architectural Ratio -->
                <div class="memorandum-hero">
                    <div class="hero-left">
                        <h1 class="hero-title">Invisible Accountant</h1>
                        <p class="hero-proposition">The end of tax anxiety. Just send a text.</p>
                        <p class="hero-detail">Autonomous fiscal compliance for 3.2 million UK sole traders delivered natively via WhatsApp. Zero applications to download. Zero chart-of-accounts training. Full statutory HMRC filing.</p>
                    </div>

                    <div class="hero-right">
                        <div class="emblem-wrapper">
                            <!-- Inlined Master SVG Crest: The Sovereign Monoline Ledger -->
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="100%" height="100%" fill="none">
                              <!-- Obsidian Slate Ground -->
                              <rect width="160" height="160" fill="#0B0F19"/>
                              <rect x="8" y="8" width="144" height="144" stroke="#1E293B" stroke-width="1"/>
                              <rect x="12" y="12" width="136" height="136" stroke="#C5A880" stroke-width="0.5" stroke-opacity="0.35"/>

                              <!-- The Sovereign Monoline Ledger (Interlocking IA Monogram) -->
                              <g stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="square" stroke-linejoin="miter">
                                <!-- Pillar I (Invisible / Institutional Integrity) -->
                                <line x1="46" y1="38" x2="46" y2="122"/>
                                <line x1="36" y1="38" x2="56" y2="38"/>
                                <line x1="36" y1="122" x2="56" y2="122"/>

                                <!-- Chevron Apex & Pillars (Accountant / Asset) -->
                                <line x1="96" y1="38" x2="68" y2="122"/>
                                <line x1="96" y1="38" x2="114" y2="122"/>
                                
                                <line x1="60" y1="122" x2="76" y2="122"/>
                                <line x1="106" y1="122" x2="122" y2="122"/>
                                <line x1="88" y1="38" x2="104" y2="38"/>
                              </g>

                              <!-- Golden Section Ledger Beam: Hallmarked Antique Gilt -->
                              <line x1="46" y1="80" x2="114" y2="80" stroke="#C5A880" stroke-width="2.5" stroke-linecap="square"/>

                              <!-- Central Trust Anchor: Admiralty Blue -->
                              <rect x="74" y="78.5" width="3" height="3" fill="#1D4ED8"/>
                            </svg>
                        </div>
                        <div class="emblem-inscription">
                            <div class="emblem-title">The Sovereign Ledger</div>
                            <div class="emblem-sub">Monoline Monogram · φ = 1.618</div>
                        </div>
                    </div>
                </div>

                <!-- Bottom Institutional Footer -->
                <div class="memorandum-footer">
                    <div class="thesis-block">
                        <span class="thesis-label">Investment Thesis</span>
                        <span class="thesis-text">The B2C illusion masking a B2B2C enterprise powerhouse.</span>
                    </div>
                    <div class="status-block">
                        <span class="status-badge">SEIS / EIS Advance Assurance</span>
                        <span class="status-note">Pre-Seed Syndicate · £350,000 Allocation</span>
                    </div>
                </div>
            </div>
        </div>'''

# Inject CSS before </style>
if "/* -------------------------------------------------------------\n           SLIDE 1: SINGLE-PLANE EXPANSIVE EDITORIAL MEMORANDUM" not in deck_html:
    deck_html = deck_html.replace('    </style>', css_injection)

# Replace Slide 1
# Find the exact start and end of Slide 1
slide1_start = deck_html.find('<!-- Slide 1 -->')
slide2_start = deck_html.find('<!-- Slide 2 -->')

if slide1_start != -1 and slide2_start != -1:
    deck_html = deck_html[:slide1_start] + slide1_replacement + '\n\n        ' + deck_html[slide2_start:]
    print("Slide 1 successfully replaced.")
else:
    print("Error: Could not locate Slide 1 boundaries.")

with open('C:/Antigravity/UK MTD/invisible-accountant/investor_jury_deck.html', 'w', encoding='utf-8') as f:
    f.write(deck_html)

print("Updated investor_jury_deck.html written.")
