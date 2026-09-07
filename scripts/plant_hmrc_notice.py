import os

notice_html = '''
            <!-- HMRC AUDIT NOTICE -->
            <div class="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-10">
                <h2 class="font-heading text-blue-900 font-semibold mb-2 flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    HMRC Audit & Sandbox Notice
                </h2>
                <p class="text-blue-800 text-sm leading-relaxed">
                    This application is currently operating in a <strong>Sandbox / Pre-Production environment</strong> for testing and HMRC auditing purposes. While current testing infrastructure utilizes secure EEA-based cloud processing, <strong>upon receiving HMRC production credentials, our entire architecture will be migrated exclusively to a UK-based data center (e.g., AWS London)</strong> to permanently fulfill the UK-exclusive data processing clauses outlined below.
                </p>
            </div>
'''

for filename in ['templates/privacy.html', 'templates/terms.html']:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'HMRC AUDIT NOTICE' not in content:
        # Insert right after the "Last updated:" paragraph
        target = '<p class="text-gray-500 text-sm font-medium uppercase tracking-wider mb-12">Last updated: September 2026</p>'
        
        content = content.replace(target, target + '\n' + notice_html)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
            
print("HMRC Audit Notice planted successfully in Privacy and Terms pages.")
