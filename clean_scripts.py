import re

for file in ['landing_page.html', 'public/privacy.html', 'public/terms.html', 'public/index.html']:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            html = f.read()
            
        html = re.sub(r'<a href="/cdn-cgi/l/email-protection.*?".*?>Report Security Issue</a>', '<a href="mailto:security@invisibleaccountant.co.uk" class="text-sm font-body text-slate hover:text-ukblue transition-colors">Report Security Issue</a>', html)
        
        # Remove cloudflare scripts if they exist
        html = re.sub(r'<script data-cfasync=.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<script type="module" src="https://static.cloudflareinsights.com.*?</script>', '', html, flags=re.DOTALL)
        html = re.sub(r'<script>\(function\(\).*?</script></body>', '</body>', html, flags=re.DOTALL)
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(html)
    except Exception as e:
        print(f'Error with {file}: {e}')
