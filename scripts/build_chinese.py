"""Generate both Chinese editions from English markup and content/zh.json."""
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = json.loads((ROOT / 'content/zh.json').read_text(encoding='utf-8'))
TRANSLATIONS = {unescape(key): unescape(value) for key, value in CONTENT['text'].items()}
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
PAGES = {'index.html':'zh.html', 'collaboration.html':'collaboration-zh.html'}

class ChinesePage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.stack = []
        self.suppressed = 0

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        blocked = self.suppressed > 0 or values.get('data-zh-omit') == 'true'
        replacement = CONTENT['blocks'].get(values.get('data-zh'))
        if tag not in VOID:
            self.stack.append((tag, blocked or replacement is not None, not blocked, values))
        if blocked:
            if tag not in VOID: self.suppressed += 1
            return
        converted = []
        for key,value in attrs:
            if key.startswith('data-zh'): continue
            if value is not None:
                if key == 'lang' and (tag == 'html' or values.get('aria-current') == 'true'): value = 'zh-Hans'
                elif key == 'lang' and tag == 'a' and value == 'zh-Hans': value = 'en'
                elif key == 'href':
                    path, sep, fragment = value.partition('#')
                    if path == 'zh.html': path = 'index.html'
                    elif path == 'collaboration-zh.html': path = 'collaboration.html'
                    else: path = PAGES.get(path, path)
                    value = path + sep + fragment
                    if value.startswith('https://datong.studentorg.berkeley.edu/'):
                        value = value.replace('/collaboration.html','/collaboration-zh.html')
                        if value == 'https://datong.studentorg.berkeley.edu/': value += 'zh.html'
                elif key in ('alt','aria-label','placeholder','value','content'):
                    value = TRANSLATIONS.get(value, value)
                    if value == 'Language': value = '语言切换'
            converted.append(key if value is None else key+'="'+escape(value,quote=True)+'"')
        self.output.append('<'+tag+(' '+' '.join(converted) if converted else '')+'>')
        if replacement is not None:
            self.output.append(replacement)
            if tag not in VOID: self.suppressed += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID: self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack: return
        _, blocked, emit, _ = self.stack.pop()
        if blocked:
            self.suppressed -= 1
            if self.suppressed: return
        if emit:
            self.output.append('</'+tag+'>')

    def handle_data(self, text):
        if self.suppressed: return
        if any(item[0] in ('script','style') for item in self.stack): self.output.append(text); return
        core = text.strip()
        if core == 'EN' and self.stack and self.stack[-1][3].get('aria-current') == 'true': core_translation = '中文'
        elif core == '中文' and self.stack and self.stack[-1][3].get('lang') == 'zh-Hans' and self.stack[-1][0] == 'a': core_translation = 'EN'
        else: core_translation = TRANSLATIONS.get(core, core)
        result = text.replace(core,core_translation) if core else text
        self.output.append(escape(result, quote=False))

    def handle_comment(self, text):
        if not self.suppressed: self.output.append('<!--'+text+'-->')
    def handle_decl(self, text): self.output.append('<!'+text+'>')
    def handle_entityref(self, name):
        if not self.suppressed: self.output.append('&'+name+';')
    def handle_charref(self, name):
        if not self.suppressed: self.output.append('&#'+name+';')

def translate(source):
    parser = ChinesePage()
    parser.feed(source)
    return ''.join(parser.output)

if __name__ == '__main__':
    for source,destination in PAGES.items():
        (ROOT/destination).write_text(translate((ROOT/source).read_text(encoding='utf-8')),encoding='utf-8')
