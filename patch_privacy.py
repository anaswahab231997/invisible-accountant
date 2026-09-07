import re

with open('public/privacy.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Fraud Prevention Headers
fraud_clause = '<li><strong class="text-gray-900">Fraud Prevention Headers & Telemetry:</strong> To comply strictly with HMRC legal requirements for the MTD APIs, we are mandated to collect and transmit \'Fraud Prevention Headers\' during your transactions. This includes your IP address, device identifiers, and network telemetry data. This data is securely transmitted directly to HMRC for audit and fraud prevention purposes.</li>\n                    </ul>'

html = re.sub(r'</ul>', fraud_clause, html, count=1)

# 2. Update Section 4
section4_old = r'<section>\s*<h2 class="font-heading text-2xl font-semibold text-gray-900 mb-4">4\. Your Data Rights \(Portability, Access & Deletion\)</h2>.*?privacy@invisibleaccountant\.co\.uk\.</p>\s*</section>'

section4_new = '''<section>
                    <h2 class="font-heading text-2xl font-semibold text-gray-900 mb-4">4. Statutory Retention & Your Data Rights</h2>
                    <p class="text-gray-600 leading-relaxed mb-4">Under UK law, businesses are required to keep financial and tax records for at least 5 years after the 31 January submission deadline of the relevant tax year (effectively 6 years). We retain your data to help you comply with this statutory obligation.</p>
                    <p class="text-gray-600 leading-relaxed mb-4">Under UK GDPR, you have the right to access, amend, export, or permanently delete your data. You can exercise your "Right to be Forgotten" or request a data export at any time by texting <strong>"DELETE MY DATA"</strong> or <strong>"EXPORT MY DATA"</strong> to the Invisible Accountant WhatsApp bot.</p>
                    <p class="text-gray-600 leading-relaxed bg-amber-50 p-4 rounded-xl text-amber-900 border border-amber-100"><strong class="font-semibold">Important HMRC Warning:</strong> If you exercise your Right to Deletion, we will permanently erase your digital ledger from our systems. However, you remain legally responsible for maintaining your own statutory tax records elsewhere to comply with HMRC's 6-year retention rules.</p>
                </section>'''

html = re.sub(section4_old, section4_new, html, flags=re.DOTALL)

with open('public/privacy.html', 'w', encoding='utf-8') as f:
    f.write(html)
