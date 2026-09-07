import os

preview_html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Invisible Accountant - Brand Identity Evaluation</title>
<link href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@400,500,700,800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600&family=Geist:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  body {
    background: #07090E;
    color: #E2E8F0;
    font-family: 'Geist', sans-serif;
    padding: 40px;
    margin: 0;
  }
  h1 {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-size: 2rem;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
  }
  .sub {
    color: #64748B;
    font-size: 0.9rem;
    margin-bottom: 40px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
    max-width: 1200px;
    margin-bottom: 60px;
  }
  .card {
    background: #0B0F19;
    border: 1px solid #1E293B;
    padding: 32px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .card-title {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    text-transform: uppercase;
  }
  .card-desc {
    color: #64748B;
    font-size: 0.8rem;
    margin-bottom: 24px;
    text-align: center;
  }
  .svg-box {
    width: 200px;
    height: 200px;
    margin-bottom: 20px;
  }
  .scale-row {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #1E293B;
    width: 100%;
    justify-content: center;
  }
</style>
</head>
<body>
  <h1>Invisible Accountant — Sovereign Identity Audit</h1>
  <div class="sub">Visual Semiotics & Mathematical Proportions (Phi = 1.618033)</div>

  <div class="grid">
'''

for i in range(1, 5):
    with open(f'C:/Antigravity/UK MTD/invisible-accountant/scripts/v{i}.svg') as f:
        svg_code = f.read()
    titles = [
        "V1: Balanced Ledger Monogram (I + A)",
        "V2: Interlocking Portico Cipher (The Double Pillar)",
        "V3: Roman Majuscule Synthesis (Mayfair Plaque)",
        "V4: Minimalist Architectural Twin-Line (Coutts / Savile Row)"
    ]
    descs = [
        "Independent vertical column 'I' paired with an interlocking 'A' with Golden Ratio crossbar.",
        "Monoline double-entry columns flanking central Golden Ratio apex and hallmarked gold ledger beam.",
        "Monumental Roman solid columns with precision negative space and antique gilt lintel.",
        "Pure twin-line architectural drafting lines with exact Golden Ratio aperture (48px x 78px)."
    ]
    preview_html += f'''
    <div class="card">
      <div class="card-title">{titles[i-1]}</div>
      <div class="card-desc">{descs[i-1]}</div>
      <div class="svg-box">{svg_code}</div>
      <div class="scale-row">
        <div style="width: 64px; height: 64px;">{svg_code}</div>
        <div style="width: 32px; height: 32px;">{svg_code}</div>
        <div style="width: 16px; height: 16px;">{svg_code}</div>
        <span style="font-family: 'Geist Mono'; font-size: 0.7rem; color: #64748B;">64px / 32px / 16px</span>
      </div>
    </div>
    '''

preview_html += '''
  </div>
</body>
</html>
'''

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/preview_logos.html', 'w') as f:
    f.write(preview_html)
print("Preview page generated.")
