import re

with open('landing_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Top Banner
html = html.replace('Making Tax Digital (MTD) becomes mandatory for UK Sole Traders in April 2026.', 'Making Tax Digital (MTD) becomes mandatory for UK Sole Traders earning over £50k in April 2026.')

# 2. Hero Text
html = html.replace('vaults it directly to HMRC for you.', 'vaults it securely in your digital ledger for your quarterly updates.')

# 3. Features "Forward email receipts"
html = html.replace('links it to your HMRC return.', 'links it to your MTD ledger.')

# 4. Live Inference Engine
html = html.replace('Ready for HMRC', 'Ready for Ledger')
html = html.replace('queued for HMRC', 'queued in your digital ledger')
html = html.replace('Expense irreversibly logged to your HMRC ledger', 'Expense irreversibly logged to your MTD digital ledger')

# 5. Footer disclaimer
disclaimer = 'Our software submits data to HMRC via their official APIs. We adhere strictly to HMRC Developer Hub guidelines. Use of our software does not constitute formal endorsement or "HMRC approval" of your tax affairs. The taxpayer remains legally responsible for the accuracy of their tax submissions, regardless of AI categorization.'
html = re.sub(r'Our software submits data to HMRC.*?of your tax affairs\.', disclaimer, html, flags=re.DOTALL)

# 6. Quiz Logic
quiz_html = '''<div id="quiz-step-1" class="quiz-step">
                    <h3 class="font-heading font-bold text-xl mb-2 text-charcoal">MTD Readiness Assessment</h3>
                    <p class="text-slate mb-6 text-sm">To qualify for the beta vault, please confirm your estimated annual revenue.</p>
                    <button class="quiz-btn" onclick="setRevenue('under50'); nextQuizStep(2)">Under £50,000 <i data-lucide="chevron-right" class="w-4 h-4 text-gray-400"></i></button>
                    <button class="quiz-btn" onclick="setRevenue('over50'); nextQuizStep(2)">£50,000 - £85,000 <i data-lucide="chevron-right" class="w-4 h-4 text-gray-400"></i></button>
                    <button class="quiz-btn" onclick="setRevenue('over85'); nextQuizStep(2)">Over £85,000 <i data-lucide="chevron-right" class="w-4 h-4 text-gray-400"></i></button>
                </div>
                <div id="quiz-step-2" class="quiz-step hidden">
                    <h3 class="font-heading font-bold text-xl mb-2 text-charcoal">Current Workflow</h3>
                    <p class="text-slate mb-6 text-sm">How do you currently track your business expenses?</p>
                    <button class="quiz-btn" onclick="nextQuizStep(3)">Paper & Shoeboxes <i data-lucide="chevron-right" class="w-4 h-4 text-gray-400"></i></button>
                    <button class="quiz-btn" onclick="nextQuizStep(3)">Excel Spreadsheets <i data-lucide="chevron-right" class="w-4 h-4 text-gray-400"></i></button>
                    <button class="quiz-btn" onclick="nextQuizStep(3)">Traditional Accounting Software <i data-lucide="chevron-right" class="w-4 h-4 text-gray-400"></i></button>
                </div>
                <div id="quiz-step-3" class="quiz-step hidden">
                    <div class="flex items-center gap-2 text-emerald-700 bg-mint px-3 py-1 rounded-full text-sm font-bold w-max mb-4">
                        <i data-lucide="check-circle-2" class="w-4 h-4"></i> Qualified for Beta
                    </div>
                    <h3 id="quiz-result-title" class="font-heading font-bold text-xl mb-2 text-charcoal">You are required to comply with MTD.</h3>
                    <p id="quiz-result-desc" class="text-slate mb-6 text-sm leading-relaxed">Based on your profile, you will face quarterly mandatory updates by April 2026. Secure your spot in the Invisible Accountant Beta vault now.</p>
                    <div class="flex items-center justify-between mb-4 bg-gray-50 rounded-lg p-3 border border-gray-200">
                        <span class="text-slate font-medium text-sm">Queue Position</span>
                        <span class="font-mono font-bold text-ukblue text-lg">#143 / 250</span>
                    </div>
                    <a href="https://wa.me/447000000000?text=Add%20me%20to%20the%20UK%20Beta" class="btn-massive w-full py-4 bg-wapp hover:bg-[#20bd5a] text-white rounded-xl flex items-center justify-center gap-3 font-heading font-bold text-lg shadow-[0_4px_14px_0_rgba(37,211,102,0.39)]">
                        <i data-lucide="message-circle" class="w-6 h-6"></i>
                        Join Waitlist via WhatsApp
                    </a>
                </div>'''

# Replace quiz HTML
html = re.sub(r'<div id="quiz-step-1" class="quiz-step">.*?Join Waitlist via WhatsApp\s*</a>\s*</div>', quiz_html, html, flags=re.DOTALL)

# Inject JS for setRevenue
js_func = '''let userRevenue = '';
        function setRevenue(val) {
            userRevenue = val;
        }
        
        function nextQuizStep(step) {
            document.querySelectorAll('.quiz-step').forEach(el => el.classList.add('hidden'));
            document.getElementById('quiz-step-' + step).classList.remove('hidden');
            
            if (step === 3) {
                const title = document.getElementById('quiz-result-title');
                const desc = document.getElementById('quiz-result-desc');
                if (userRevenue === 'under50') {
                    title.innerText = "You have more time, but start preparing.";
                    desc.innerText = "Based on your profile, your MTD compliance deadline is April 2027 (or you may be exempt if under £30k). Get ahead of the curve and secure your beta spot now.";
                } else {
                    title.innerText = "You are required to comply with MTD.";
                    desc.innerText = "Based on your profile, you will face quarterly mandatory updates by April 2026. Secure your spot in the Invisible Accountant Beta vault now.";
                }
            }
        }'''

html = re.sub(r'function nextQuizStep\(step\).*?\}', js_func, html, flags=re.DOTALL)

with open('landing_page.html', 'w', encoding='utf-8') as f:
    f.write(html)
