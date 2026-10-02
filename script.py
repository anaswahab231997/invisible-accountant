from html.parser import HTMLParser
import urllib.request

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())

parser = MyHTMLParser()
html = urllib.request.urlopen('https://developer.service.hmrc.gov.uk/guides/fraud-prevention/missing-header-data/').read().decode('utf-8')
parser.feed(html)
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(parser.text))
