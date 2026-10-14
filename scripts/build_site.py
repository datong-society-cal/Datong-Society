"""Build bilingual static pages with Python's standard library. No server runtime."""
import argparse
from datetime import datetime
from html import escape
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from build_chinese import translate

ROOT = Path(__file__).resolve().parent.parent
PAGES = {'home': ('index.html', 'zh.html', 'Home'),
         'workshops': ('workshops.html', 'workshops-zh.html', 'Workshops'),
         'events': ('events.html', 'events-zh.html', 'Public Events'),
         'resources': ('resources.html', 'resources-zh.html', 'Resources'),
         'about': ('about.html', 'about-zh.html', 'About Us'),
         'contact': ('contact.html', 'contact-zh.html', 'Contact Us'),
         'collaboration': ('collaboration.html', 'collaboration-zh.html', 'Collaboration')}

def read_json(name):
    return json.loads((ROOT / 'content' / name).read_text(encoding='utf-8'))

def localized_block(content_id, en, zh, blocks):
    blocks[content_id] = zh
    return f'<div data-zh="{content_id}">{en}</div>'

def validate_content(events, resources):
    for items in (events, resources):
        ids = [item['id'] for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate content ID')
        for item in items:
            if not all(item['title'].get(language) for language in ('en', 'zh')):
                raise ValueError('Missing bilingual title: ' + item['id'])
    for item in resources:
        if urlsplit(item['url']).scheme != 'https':
            raise ValueError('Resource URL must use HTTPS')
    for event in events:
        start, end = datetime.fromisoformat(event['start']), datetime.fromisoformat(event['end'])
        if not start.tzinfo or not end.tzinfo or end <= start:
            raise ValueError('Event requires timezone-aware start/end')
        poster = Path(event['poster'])
        if poster.is_absolute() or '..' in poster.parts or not (ROOT / poster).is_file():
            raise ValueError('Invalid event poster')

def event_html(event, language, featured=False, past=False):
    title = escape(event['title'][language])
    date = datetime.fromisoformat(event['start']).strftime('%b %d, %Y · %I:%M %p')
    heading = ('Recent event' if past else 'Upcoming event') if language == 'en' else ('近期回顾' if past else '近期活动')
    details = 'View event poster' if language == 'en' else '查看活动海报'
    image = f'<a class="home-poster" href="{escape(event["poster"])}" target="_blank" rel="noopener"><img src="{escape(event["poster"])}" alt="{title}" loading="lazy" decoding="async"></a>'
    text = f'<div><p class="home-eyebrow">{heading}</p><h2>{title}</h2><p>{escape(event["description"][language])}</p><p><time datetime="{event["start"]}">{date} · Pacific Time</time><br>{escape(event["location"][language])}</p><a class="button" href="{event["poster"]}" target="_blank" rel="noopener">{details} ↗</a></div>'
    return f'<section class="home-feature">{image if featured else ""}{text}</section>'

def render(as_of):
    config, events, resources = read_json('site.json'), read_json('events.json'), read_json('resources.json')
    validate_content(events, resources)
    analytics = config.get('analytics', {'provider': 'none'})
    analytics_tag = ''
    if analytics['provider'] == 'goatcounter':
        endpoint = analytics.get('endpoint', '')
        parsed = urlsplit(endpoint)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path != '/count' or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('GoatCounter requires an HTTPS /count endpoint')
        analytics_tag = f'<script data-goatcounter="{escape(endpoint)}" async src="https://gc.zgo.at/count.js"></script>'
    elif analytics['provider'] != 'none':
        raise ValueError('Unknown analytics provider')
    import build_chinese
    blocks = build_chinese.CONTENT['blocks']
    future = sorted([e for e in events if datetime.fromisoformat(e['end']) >= as_of], key=lambda e: e['start'])
    past = sorted([e for e in events if datetime.fromisoformat(e['end']) < as_of], key=lambda e: e['start'], reverse=True)
    featured = (future or past or [None])[0]
    feature = localized_block('featured-event', event_html(featured, 'en', True, not future), event_html(featured, 'zh', True, not future), blocks) if featured else ''
    program = localized_block('event-programs', ''.join(event_html(e, 'en', past=e in past) for e in future + past), ''.join(event_html(e, 'zh', past=e in past) for e in future + past), blocks)
    def links(language):
        title = 'Useful links for students &amp; researchers at Cal' if language == 'en' else '伯克利学生与研究者常用链接'
        rows = ''.join(f'<li><a href="{escape(r["url"])}" target="_blank" rel="noopener noreferrer">{escape(r["title"][language])} ↗</a></li>' for r in resources)
        return f'<section class="resource-directory"><h3>{title}</h3><ul>{rows}</ul></section>'
    resource_block = localized_block('campus-links', links('en'), links('zh'), blocks)
    footer = (ROOT / 'templates/footer.html').read_text(encoding='utf-8')
    for page, (en_name, zh_name, title) in PAGES.items():
        nav = '<nav id="site-navigation" aria-label="Main navigation"><ul>' + ''.join(f'<li><a href="{en}"'+ (' aria-current="page"' if key == page else '') + f'>{label}</a></li>' for key,(en,zh,label) in PAGES.items() if key != 'collaboration') + '</ul></nav>'
        body = (ROOT / 'content/pages' / (page + '.html')).read_text(encoding='utf-8')
        body = body.replace('{{ featured_event }}', feature).replace('{{ event_programs }}', program).replace('{{ resources }}', resource_block)
        hero = (ROOT / 'templates/hero.html').read_text(encoding='utf-8') if page == 'home' else ''
        brand = '<a class="site-brand" href="index.html"><img src="images/brand/datong-logo-emblem.png" alt="Datong Society emblem" width="52" height="52"><span>DATONG <span lang="zh-Hans">大同</span></span></a>'
        article_title = title if page != 'home' else 'Home'
        html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#101a30">
<title>{article_title} | Datong Society · UC Berkeley</title><meta name="description" content="Datong Society of China Studies at UC Berkeley — {title}.">
<link rel="canonical" href="{config['url'] + (en_name if page != 'home' else '')}"><link rel="icon" type="image/png" href="images/brand/datong-logo-emblem.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600&amp;family=Inter:wght@400;600&amp;family=Noto+Serif+SC:wght@400;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/main.css"></head>
<body class="page-{page}"><a class="skip-link" href="#main">Skip to content</a><header class="site-header">{brand}{nav}<div class="language-switch" aria-label="Language"><span lang="en" aria-current="true">EN</span> / <a href="{zh_name}" lang="zh-Hans">中文</a></div></header>
{hero}<main id="main"><article id="{page}">{body}</article></main>{footer}
<div id="lb-overlay"><figure><img id="lb-img" alt=""><figcaption id="lb-cap"></figcaption></figure></div>
<script src="assets/js/main.js" defer></script><script src="assets/js/effects.js" defer></script><script src="assets/js/language.js" defer></script>{analytics_tag}</body></html>'''
        for section,(en,zh,label) in PAGES.items():
            html = html.replace(f'href="#{section}"', f'href="{en}"').replace(f'href="index.html#{section}"', f'href="{en}"')
        html = html.replace('href="#"', 'href="index.html"')
        html = re.sub(r'<h2 class="major">(.*?)</h2>', r'<h1 class="major">\1</h1>', html)
        def fingerprint(match):
            path = match[2]
            asset = ROOT / path
            data = asset.read_bytes()
            # Git checks text out as CRLF on Windows and LF on Linux. Version
            # equivalent text identically so generated pages remain reproducible.
            if asset.suffix in ('.css', '.js'):
                data = data.replace(b'\r\n', b'\n')
            version = hashlib.sha256(data).hexdigest()[:12]
            return match[1] + path + '?v=' + version + '"'
        html = re.sub(r'((?:src|href)=")((?:assets/(?:css|js)/[^"?]+|images/qr/[^"?]+))(?:\?[^" ]*)?"', fingerprint, html)
        (ROOT / en_name).write_text(html + '\n', encoding='utf-8')
        translated = translate(html)
        translated = translated.replace(config['url'] + en_name, config['url'] + zh_name)
        if page == 'home':
            translated = translated.replace('rel="canonical" href="' + config['url'] + '"', 'rel="canonical" href="' + config['url'] + zh_name + '"')
        (ROOT / zh_name).write_text(translated + '\n', encoding='utf-8')
    # Persist generated localized blocks so the translation check uses the same content IDs.
    (ROOT / 'content/zh.json').write_text(json.dumps(build_chinese.CONTENT, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Built {len(PAGES) * 2} pages; {len(future)} upcoming and {len(past)} past events.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', help='Timezone-aware ISO timestamp for reproducible event classification')
    args = parser.parse_args()
    now = datetime.fromisoformat(args.as_of or read_json('site.json')['as_of'])
    if not now.tzinfo:
        raise SystemExit('Build timestamp must include a timezone')
    render(now)
