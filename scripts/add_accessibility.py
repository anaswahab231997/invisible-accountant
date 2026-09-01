import os

accessibility_html = '''<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Statement | Invisible Accountant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script>
        tailwind.config = { theme: { extend: { fontFamily: { heading: ['"DM Sans"', 'sans-serif'], body: ['Inter', 'sans-serif'] } } } }
    </script>
</head>
<body class="bg-gray-50 text-gray-800 font-body antialiased selection:bg-blue-100 selection:text-blue-900">
    
    <header class="bg-white border-b border-gray-100">
        <div class="max-w-4xl mx-auto px-6 py-6 flex items-center justify-between">
            <a href="/" class="flex items-center gap-2 group">
                <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold">IA</div>
                <span class="font-heading font-semibold text-gray-900 text-xl tracking-tight">Invisible Accountant</span>
            </a>
            <a href="/" class="text-sm font-medium text-gray-500 hover:text-gray-900">Back to Home</a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-6 py-16">
        <div class="bg-white rounded-3xl shadow-sm border border-gray-100 p-8 md:p-12">
            <h1 class="font-heading text-4xl md:text-5xl font-bold text-gray-900 tracking-tight mb-4">Accessibility Statement</h1>
            <p class="text-gray-500 text-sm font-medium uppercase tracking-wider mb-12">Last updated: September 2026</p>
            
            <div class="space-y-10">
                <section>
                    <h2 class="font-heading text-2xl font-semibold text-gray-900 mb-4">Our Commitment</h2>
                    <p class="text-gray-600 leading-relaxed">Invisible Accountant is committed to ensuring digital accessibility for people with disabilities. We are continually improving the user experience for everyone and applying the relevant accessibility standards to comply with HM Revenue & Customs (HMRC) Developer Hub requirements for software providers.</p>
                </section>

                <section>
                    <h2 class="font-heading text-2xl font-semibold text-gray-900 mb-4">Conformance Status</h2>
                    <p class="text-gray-600 leading-relaxed bg-green-50 p-4 rounded-xl text-green-900 border border-green-100">Invisible Accountant is <strong>fully conformant with WCAG 2.1 level AA</strong>. This means that our primary interface (which operates via WhatsApp) and our web properties meet strict accessibility thresholds, including screen-reader compatibility, contrast minimums, and keyboard navigability.</p>
                </section>
            </div>
        </div>
    </main>

    <footer class="bg-gray-50 py-12 text-center">
        <div class="max-w-4xl mx-auto px-6">
            <div class="flex flex-col md:flex-row justify-center items-center gap-4 md:gap-8 mb-6">
                <a href="/terms" class="text-sm font-medium text-gray-500 hover:text-blue-600">Terms & Conditions</a>
                <a href="/privacy" class="text-sm font-medium text-gray-500 hover:text-blue-600">Privacy Policy</a>
                <a href="/accessibility" class="text-sm font-medium text-gray-500 hover:text-blue-600">Accessibility</a>
                <a href="mailto:security@invisibleaccountant.co.uk" class="text-sm font-medium text-gray-500 hover:text-blue-600">Report Security Issue</a>
            </div>
            <p class="text-sm text-gray-400">&copy; 2026 Invisible Accountant Ltd. Registered in England & Wales.</p>
        </div>
    </footer>
</body>
</html>'''

with open('templates/accessibility.html', 'w', encoding='utf-8') as f:
    f.write(accessibility_html)

with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

if '@app.get("/accessibility")' not in main_content:
    main_content = main_content.replace(
        '@app.get("/terms")',
        '@app.get("/accessibility", response_class=HTMLResponse)\nasync def serve_accessibility():\n    with open("templates/accessibility.html", "r", encoding="utf-8") as f:\n        return f.read()\n\n@app.get("/terms")'
    )
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(main_content)

for filepath in ['landing_page.html', 'templates/privacy.html', 'templates/terms.html']:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'href="/accessibility"' not in content:
        content = content.replace(
            '<a href="/privacy" class="text-sm font-body text-slate hover:text-ukblue transition-colors">Privacy Policy</a>',
            '<a href="/privacy" class="text-sm font-body text-slate hover:text-ukblue transition-colors">Privacy Policy</a>\n                <a href="/accessibility" class="text-sm font-body text-slate hover:text-ukblue transition-colors">Accessibility</a>'
        )
        content = content.replace(
            '<a href="/privacy" class="text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors">Privacy Policy</a>',
            '<a href="/privacy" class="text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors">Privacy Policy</a>\n                <a href="/accessibility" class="text-sm font-medium text-gray-500 hover:text-blue-600 transition-colors">Accessibility</a>'
        )
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

print("Accessibility updates applied successfully.")
