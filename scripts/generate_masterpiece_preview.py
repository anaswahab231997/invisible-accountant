import os

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Invisible Accountant — Refined Masterpiece Comparison</title>
<link href="https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@400,500,700,800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600&family=Geist:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  body {
    background: #07090E;
    color: #F8FAFC;
    font-family: 'Geist', sans-serif;
    padding: 40px;
    margin: 0;
  }
  h1 {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 6px;
    letter-spacing: -0.02em;
  }
  .sub {
    color: #64748B;
    font-size: 0.85rem;
    margin-bottom: 40px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
    margin-bottom: 48px;
  }
  .card {
    background: #0B0F19;
    border: 1px solid #1E293B;
    padding: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .card-title {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
    text-transform: uppercase;
    text-align: center;
  }
  .svg-box {
    width: 160px;
    height: 160px;
    margin-bottom: 20px;
  }
  .scale-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #1E293B;
    width: 100%;
    justify-content: center;
  }
  .lockups {
    margin-top: 40px;
    border-top: 1px solid #1E293B;
    padding-top: 40px;
  }
  .lockup-row {
    background: #0B0F19;
    border: 1px solid #1E293B;
    padding: 24px 36px;
    display: flex;
    align-items: center;
    gap: 28px;
    margin-bottom: 20px;
  }
  .lockup-brand {
    display: flex;
    flex-direction: column;
  }
  .lockup-title {
    font-family: 'Cabinet Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #FFFFFF;
    text-transform: uppercase;
    line-height: 1.1;
  }
  .lockup-sub {
    font-family: 'Geist Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    color: #64748B;
    letter-spacing: 0.22em;
    margin-top: 6px;
    text-transform: uppercase;
  }
</style>
</head>
<body>
  <h1>Invisible Accountant — Masterpiece Logo Selection</h1>
  <div class="sub">Audited for British Institutional Elegance & Zero AI Slop</div>

  <div class="grid">
'''

names = ['m1', 'm2', 'm3', 'm4']
titles = [
    "M1: Savile Row Interlock",
    "M2: Sovereign Portico",
    "M3: Mayfair Monolith",
    "M4: Pure Architectural Ledger"
]

svgs = {}
for i, name in enumerate(names):
    with open(f'C:/Antigravity/UK MTD/invisible-accountant/scripts/{name}.svg') as f:
        code = f.read()
        svgs[name] = code
    html += f'''
    <div class="card">
      <div class="card-title">{titles[i]}</div>
      <div class="svg-box">{code}</div>
      <div class="scale-row">
        <div style="width: 48px; height: 48px;">{code}</div>
        <div style="width: 28px; height: 28px;">{code}</div>
        <div style="width: 16px; height: 16px;">{code}</div>
      </div>
    </div>
    '''

html += '''
  </div>

  <div class="lockups">
    <h2>Horizontal Brand Plaque Lockups (Letterheads & Memoranda)</h2>
'''

for i, name in enumerate(names):
    html += f'''
    <div class="lockup-row">
      <div style="width: 64px; height: 64px; flex-shrink: 0;">{svgs[name]}</div>
      <div class="lockup-brand">
        <div class="lockup-title">Invisible Accountant</div>
        <div class="lockup-sub">HMRC Making Tax Digital · Statutory Compliance Infrastructure</div>
      </div>
      <div style="margin-left: auto; text-align: right;">
        <span style="font-family: 'Geist Mono'; font-size: 0.7rem; color: #C5A880; border: 1px solid rgba(197, 168, 128, 0.3); padding: 4px 10px;">SEIS / EIS ELIGIBLE</span>
      </div>
    </div>
    '''

html += '''
  </div>
</body>
</html>
'''

with open('C:/Antigravity/UK MTD/invisible-accountant/scripts/preview_masterpiece.html', 'w') as f:
    f.write(html)
print("Preview page generated successfully.")
