"""Build bilingual static pages with Python's standard library. No server runtime."""
import argparse
from datetime import date, datetime
from html import escape
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import build_chinese
from event_archive import LABELS as EVENT_LABELS, render_archive, validate_archive

from site_contract import PAGE_ROUTES, PUBLIC_PATHS

ROOT = Path(__file__).resolve().parent.parent

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
        start = datetime.fromisoformat(event['start'])
        end = datetime.fromisoformat(event['end']) if event.get('end') else None
        if not start.tzinfo or (end and (not end.tzinfo or end <= start)):
            raise ValueError('Event requires timezone-aware start/end')
        if event['category'] not in EVENT_LABELS['en']:
            raise ValueError('Unknown event category: ' + event['id'])
        for key in ('location', 'description'):
            if not all(event[key].get(language) for language in ('en', 'zh')):
                raise ValueError('Missing event translation: ' + event['id'] + '/' + key)
        if event.get('registration') and urlsplit(event['registration']).scheme != 'https':
            raise ValueError('Registration link must use HTTPS: ' + event['id'])
        for asset in ([event['poster']] if event.get('poster') else []) + [photo['src'] for photo in event.get('gallery', [])]:
            path = Path(asset)
            if path.is_absolute() or '..' in path.parts or not (ROOT / path).is_file():
                raise ValueError('Invalid event image: ' + asset)

def event_end(event):
    return datetime.fromisoformat(event.get('end') or event['start'])

def event_date(event, language):
    start = datetime.fromisoformat(event['start'])
    if language == 'en':
        return start.strftime('%A, %B ') + str(start.day) + start.strftime(', %Y')
    return f'{start.year} 年 {start.month} 月 {start.day} 日，星期' + '一二三四五六日'[start.weekday()]

def event_time(event, language):
    start = datetime.fromisoformat(event['start'])
    end = datetime.fromisoformat(event['end']) if event.get('end') else None
    if language == 'zh':
        return start.strftime('%H:%M') + ('–' + end.strftime('%H:%M') if end else '') + ' · 太平洋时间'
    clock = lambda t: t.strftime('%I:%M').lstrip('0')
    if not end:
        span = clock(start) + start.strftime(' %p')
    elif start.strftime('%p') == end.strftime('%p'):
        span = clock(start) + '–' + clock(end) + end.strftime(' %p')
    else:
        span = clock(start) + start.strftime(' %p') + '–' + clock(end) + end.strftime(' %p')
    return span + ' · Pacific Time'

def full_title(event, language):
    sub = event.get('subtitle', {}).get(language)
    return event['title'][language] + (('：' if language == 'zh' else ': ') + sub if sub else '')

def event_people(event, language):
    if not event.get('speaker'):
        return ''
    guest = event['category'] == 'Film & Panel'
    label = ('Guest: ' if guest else 'Speaker: ') if language == 'en' else ('嘉宾：' if guest else '主讲人：')
    return label + event['speaker'][language]

def event_hosts(event, language):
    if not event.get('hosts'):
        return ''
    return ('Hosted by ' if language == 'en' else '主办：') + event['hosts'][language]

def event_copy(event, language, upcoming):
    """Shared text block: tag and date, title, speaker, logistics, description, hosts, actions."""
    status = ('Upcoming' if language == 'en' else '近期活动') if upcoming else ('Recent' if language == 'en' else '近期回顾')
    category = EVENT_LABELS[language][event['category']]
    html = f'<div class="event-meta"><span class="event-tag">{status} · {category}</span><time datetime="{event["start"][:10]}">{event_date(event, language)}</time></div>'
    html += f'<h3>{escape(event["title"][language])}</h3>'
    if event.get('subtitle'):
        html += f'<p class="event-subtitle">{escape(event["subtitle"][language])}</p>'
    if event_people(event, language):
        html += f'<p class="event-people">{escape(event_people(event, language))}</p>'
    html += f'<p class="event-logistics">{escape(event_time(event, language))}<br>{escape(event["location"][language])}</p>'
    html += f'<p class="event-desc">{escape(event["description"][language])}</p>'
    if event_hosts(event, language):
        html += f'<p class="event-hosts">{escape(event_hosts(event, language))}</p>'
    actions = []
    if upcoming and event.get('registration'):
        actions.append(f'<a class="button primary" href="{escape(event["registration"], quote=True)}" target="_blank" rel="noopener noreferrer">' + ('Register' if language == 'en' else '报名') + ' ↗</a>')
    if event.get('poster'):
        actions.append(f'<a class="button" href="{escape(event["poster"], quote=True)}" target="_blank" rel="noopener noreferrer">' + ('View poster' if language == 'en' else '查看海报') + ' ↗</a>')
    if actions:
        html += '<p class="event-actions">' + ''.join(actions) + '</p>'
    return html

def poster_figure(event, language, css_class='event-cover'):
    alt = escape(full_title(event, language) + (' — event poster' if language == 'en' else ' — 活动海报'), quote=True)
    src = escape(event['poster'], quote=True)
    return f'<figure class="{css_class}"><a href="{src}" target="_blank" rel="noopener noreferrer"><img src="{src}" alt="{alt}" loading="lazy" decoding="async"></a></figure>'

def upcoming_html(event, language):
    layout = 'public-event-layout' + ('' if event.get('poster') else ' public-event-text-only')
    cover = poster_figure(event, language) if event.get('poster') else ''
    return (f'<article class="event-card planned-event public-event" id="{event["id"]}"><div class="{layout}">{cover}'
            f'<div class="public-event-copy">{event_copy(event, language, True)}</div></div></article>')

def event_html(event, language, past=False):
    image = poster_figure(event, language, 'home-poster') if event.get('poster') else ''
    return f'<section class="home-feature{"" if image else " home-feature-text-only"}">{image}<div>{event_copy(event, language, not past)}</div></section>'

def workshops_html(sessions, language, as_of):
    rows = []
    for session in sorted(sessions, key=lambda item: item['date']):
        past = date.fromisoformat(session['date']) < as_of
        status = ('Past session' if past else 'Upcoming session') if language == 'en' else ('往期讨论' if past else '近期安排')
        row = f'<section class="workshop-session"><p class="home-eyebrow"><time datetime="{session["date"]}">{session["date"]}</time> · {status}</p><h3>{escape(session["title"][language])}</h3>'
        speaker = session.get('speaker', {}).get(language, '')
        affiliation = session.get('affiliation', {}).get(language, '')
        if speaker:
            label = 'Speaker: ' if language == 'en' else '主讲人：'
            byline = escape(speaker) + (', ' + escape(affiliation) if affiliation else '')
            row += f'<p class="workshop-speaker">{label}{byline}</p>'
        metadata = [session.get(key, {}).get(language, '') for key in ('time', 'location')]
        if any(metadata):
            row += '<p class="workshop-meta">' + '<br>'.join(escape(value) for value in metadata if value) + '</p>'
        row += f'<p>{escape(session["summary"][language])}</p>'
        if session.get('reading'):
            row += f'<p class="workshop-meta">{escape(session["reading"][language])}</p>'
        if session.get('registration') and not past:
            if urlsplit(session['registration']).scheme != 'https':
                raise ValueError('Registration link must use HTTPS: ' + session['id'])
            label = 'Register ↗' if language == 'en' else '报名 ↗'
            row += f'<p><a class="button" href="{escape(session["registration"])}" target="_blank" rel="noopener noreferrer">{label}</a></p>'
        if session.get('questions'):
            label = 'Discussion questions' if language == 'en' else '讨论问题'
            row += '<details><summary>' + label + '</summary><ul>' + ''.join('<li>' + escape(question) + '</li>' for question in session['questions'][language]) + '</ul></details>'
        rows.append(row + '</section>')
    heading = 'Fall 2026' if language == 'en' else '2026 年秋季'
    return f'<h2>{heading}</h2>' + ''.join(rows)

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
    blocks = build_chinese.CONTENT['blocks']
    archive = read_json('event-archive.json')
    validate_archive(archive, ROOT)
    public_records = list(archive)
    future = sorted([e for e in events if event_end(e).date() >= as_of], key=lambda e: e['start'])
    past = sorted([e for e in events if event_end(e).date() < as_of], key=lambda e: e['start'], reverse=True)
    for event in past:
        public_records.append({
            'id': event['id'], 'date': event['start'][:10], 'category': event['category'],
            'title': {lang: full_title(event, lang) for lang in ('en', 'zh')}, 'location': event['location'],
            'time': {lang: event_time(event, lang) for lang in ('en', 'zh')},
            'people': {lang: ' · '.join(x for x in (event_people(event, lang), event_hosts(event, lang)) if x) for lang in ('en', 'zh')},
            'summary': event['description'],
            'paragraphs': {lang: [event['description'][lang], event_time(event, lang) + ' · ' + event['location'][lang]] for lang in ('en', 'zh')},
            'cover': event.get('poster', ''), 'cover_caption': {'en': 'Original event poster', 'zh': '原活动海报'},
            'gallery': event.get('gallery', []),
        })
    validate_archive(public_records, ROOT)
    public_archive = localized_block('public-event-archive', render_archive(public_records, 'en'), render_archive(public_records, 'zh'), blocks)
    featured = (future or past or [None])[0]
    feature = localized_block('featured-event', event_html(featured, 'en', not future), event_html(featured, 'zh', not future), blocks) if featured else ''
    none = ('<p>No upcoming events are scheduled. Join the mailing list for announcements.</p>', '<p>暂无近期活动，欢迎订阅邮件列表获取通知。</p>')
    upcoming = localized_block('upcoming-events', ''.join(upcoming_html(e, 'en') for e in future) or none[0], ''.join(upcoming_html(e, 'zh') for e in future) or none[1], blocks)
    def links(language):
        title = 'Useful links for students &amp; researchers at Cal' if language == 'en' else '伯克利学生与研究者常用链接'
        rows = ''.join(f'<li><a href="{escape(r["url"])}" target="_blank" rel="noopener noreferrer">{escape(r["title"][language])} ↗</a></li>' for r in resources)
        return f'<section class="resource-directory"><h3>{title}</h3><ul>{rows}</ul></section>'
    resource_block = localized_block('campus-links', links('en'), links('zh'), blocks)
    reading = read_json('reading-list.json')
    def reading_html(language):
        count = sum(len(section['books']) for section in reading['sections'])
        label = f'{count} titles in {len(reading["sections"])} topics' if language == 'en' else f'共 {len(reading["sections"])} 个主题、{count} 本书'
        groups = ''.join('<details class="reading-group"><summary>' + escape(section['title'][language]) + f' <span class="reading-count">({len(section["books"])})</span></summary><ul>'
            + ''.join('<li>' + escape(book) + '</li>' for book in section['books']) + '</ul></details>' for section in reading['sections'])
        return (f'<section class="reading-list" id="reading-list"><h3>{escape(reading["title"][language])}</h3>'
            f'<p>{escape(reading["intro"][language])}</p><p class="reading-count">{label}</p>{groups}</section>')
    resource_block += localized_block('reading-list', reading_html('en'), reading_html('zh'), blocks)
    workshops = read_json('workshops.json')
    workshop_block = localized_block('workshop-schedule', workshops_html(workshops, 'en', as_of), workshops_html(workshops, 'zh', as_of), blocks)
    updated = date.fromisoformat(config['updated'])
    stamp = localized_block('updated', 'Updated ' + updated.strftime('%b ') + str(updated.day) + updated.strftime(', %Y'),
        f'更新于 {updated.year} 年 {updated.month} 月 {updated.day} 日', blocks).replace('<div ', '<span ').replace('</div>', '</span>')
    footer = (ROOT / 'templates/footer.html').read_text(encoding='utf-8').replace('{{ updated }}', stamp)
    for page, (en_name, zh_name, title) in PAGE_ROUTES.items():
        nav = '<nav id="site-navigation" aria-label="Main navigation"><ul>' + ''.join(f'<li><a href="{en}"'+ (' aria-current="page"' if key == page else '') + f'>{label}</a></li>' for key,(en,zh,label) in PAGE_ROUTES.items() if key != 'collaboration') + '</ul></nav>'
        body = (ROOT / 'content/pages' / (page + '.html')).read_text(encoding='utf-8')
        body = body.replace('{{ featured_event }}', feature).replace('{{ upcoming_events }}', upcoming).replace('{{ resources }}', resource_block)
        body = body.replace('{{ workshop_schedule }}', workshop_block)
        body = body.replace('{{ public_event_archive }}', public_archive)
        hero = (ROOT / 'templates/hero.html').read_text(encoding='utf-8') if page == 'home' else ''
        brand = '<a class="site-brand" href="index.html"><img src="images/brand/datong-logo-emblem.png" alt="Datong Society emblem" width="52" height="52"><span>DATONG <span lang="zh-Hans">大同</span></span></a>'
        article_title = title if page != 'home' else 'Home'
        html = f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#101a30"><base href="./">
<title>{article_title} | Datong Society · UC Berkeley</title><meta name="description" content="Datong Society of China Studies at UC Berkeley — {title}.">
<link rel="canonical" href="{config['url'] + PUBLIC_PATHS[en_name]}"><link rel="icon" type="image/png" href="images/brand/datong-logo-emblem.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600&amp;family=Inter:wght@400;600&amp;family=Noto+Serif+SC:wght@400;600&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/main.css"></head>
<body class="page-{page}"><a class="skip-link" href="#main">Skip to content</a><header class="site-header">{brand}{nav}<div class="language-switch" aria-label="Language"><span lang="en" aria-current="true">EN</span> / <a href="{zh_name}" lang="zh-Hans">中文</a></div></header>
{hero}<main id="main"><article id="{page}">{body}</article></main>{footer}
<div id="lb-overlay"><figure><img id="lb-img" alt=""><figcaption id="lb-cap"></figcaption></figure></div>
<script src="assets/js/main.js" defer></script><script src="assets/js/effects.js" defer></script><script src="assets/js/language.js" defer></script>{analytics_tag}</body></html>'''
        for section,(en,zh,label) in PAGE_ROUTES.items():
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
        for filename, path in PUBLIC_PATHS.items():
            html = html.replace('href="' + filename + '"', 'href="' + path + '"')
        html = html.replace('href="#main"', 'href="' + PUBLIC_PATHS[en_name] + '#main"')
        (ROOT / en_name).write_text(html + '\n', encoding='utf-8', newline='\n')
        translated = build_chinese.translate(html)
        (ROOT / zh_name).write_text(translated + '\n', encoding='utf-8', newline='\n')
    # Persist generated localized blocks so the translation check uses the same content IDs.
    (ROOT / 'content/zh.json').write_text(json.dumps(build_chinese.CONTENT, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'Built {len(PAGE_ROUTES) * 2} pages; {len(future)} upcoming and {len(past)} past events.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--as-of', help='Classification date (YYYY-MM-DD); defaults to "updated" in content/site.json')
    args = parser.parse_args()
    render(date.fromisoformat(args.as_of or read_json('site.json')['updated']))
