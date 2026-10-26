"""Render the public event archive from bilingual, dated records."""
from datetime import date
from html import escape
from pathlib import Path
import re

LABELS = {
    'en': {'all': 'All programs', 'year': 'Year', 'years': 'All years', 'more': 'Read more & view images',
           'photos': 'Archive images', 'count': 'events', 'none': 'No events match these filters.',
           'Film & Panel': 'Film & Panel', 'Author Talk': 'Author Talk', 'Lecture': 'Lecture', 'Exhibition': 'Exhibition', 'Field Trip': 'Visit', 'Salon': 'Salon'},
    'zh': {'all': '全部类型', 'year': '年份', 'years': '全部年份', 'more': '展开详情与图片',
           'photos': '活动与档案影像', 'count': '场活动', 'none': '暂无符合筛选条件的活动。',
           'Film & Panel': '电影与映后', 'Author Talk': '作家对谈', 'Lecture': '讲座', 'Exhibition': '展览', 'Field Trip': '参访', 'Salon': '沙龙'},
}


def validate_archive(records, root):
    ids = set()
    for item in records:
        if item['id'] in ids:
            raise ValueError('Duplicate archive ID: ' + item['id'])
        ids.add(item['id'])
        date.fromisoformat(item['date'] if len(item['date']) == 10 else item['date'] + ('-01-01' if len(item['date']) == 4 else '-01'))
        if item['category'] not in ('Film & Panel', 'Author Talk', 'Lecture', 'Exhibition', 'Field Trip', 'Salon'):
            raise ValueError('Unknown public event category')
        for key in ('title', 'summary', 'paragraphs', 'cover_caption'):
            if not all(item[key].get(lang) for lang in ('en', 'zh')):
                raise ValueError('Missing archive translation: ' + item['id'] + '/' + key)
        for asset in ([item['cover']] if item.get('cover') else []) + [photo['src'] for photo in item.get('gallery', [])]:
            path = Path(asset)
            if path.is_absolute() or '..' in path.parts or not (root / path).is_file():
                raise ValueError('Invalid archive image: ' + asset)
        for photo in item.get('gallery', []):
            if not all(photo['caption'].get(lang) for lang in ('en', 'zh')):
                raise ValueError('Missing image caption')


def render_archive(records, language):
    labels = LABELS[language]
    records = sorted(records, key=lambda e: e['date'], reverse=True)
    years = sorted({e['date'][:4] for e in records}, reverse=True)
    buttons = ''.join(f'<button type="button" data-filter="{escape(cat, quote=True)}"'
                      + (' class="is-active" aria-pressed="true"' if cat == 'all' else ' aria-pressed="false"')
                      + f'>{labels["all"] if cat == "all" else labels[cat]}</button>'
                      for cat in ('all', 'Film & Panel', 'Author Talk', 'Lecture', 'Exhibition', 'Field Trip', 'Salon'))
    options = '<option value="all">' + labels['years'] + '</option>' + ''.join(f'<option>{year}</option>' for year in years)
    html = f'<div class="archive-controls"><div id="public-events-filter" aria-label="{labels["all"]}">{buttons}</div><label class="archive-year-select">{labels["year"]}<select id="event-year">{options}</select></label></div>'
    html += f'<p class="archive-count" id="event-count" aria-live="polite">{len(records)} {labels["count"]}</p><p id="events-empty" hidden>{labels["none"]}</p>'
    for year in years:
        html += f'<section class="archive-year" data-year="{year}"><h2 class="archive-year-heading">{year}</h2>'
        for event in [e for e in records if e['date'].startswith(year)]:
            title = escape(event['title'][language])
            caption = escape(event['cover_caption'][language])
            path = escape(event.get('cover', ''), quote=True)
            html += f'<article class="event-card public-event" id="{event["id"]}" data-cat="{escape(event["category"], quote=True)}" data-year="{year}">'
            html += '<div class="public-event-layout' + (' public-event-text-only' if not path else '') + '">'
            if path:
                html += f'<figure class="event-cover"><img src="{path}" alt="{caption}" loading="lazy" decoding="async"><figcaption>{caption}</figcaption></figure>'
            html += '<div class="public-event-copy"><div class="event-meta">'
            month = event['date'][:7]
            date_label = month.replace('-', ' · ') if language == 'en' else (month[:4] + '年' + str(int(month[5:7])) + '月' if len(month) == 7 else month + '年')
            html += f'<time datetime="{month}">{date_label}</time><span class="event-tag">{labels[event["category"]]}</span></div>'
            html += f'<h3>{title}</h3>'
            if event.get('people', {}).get(language):
                html += f'<p class="event-people">{escape(event["people"][language])}</p>'
            html += f'<p class="event-desc">{escape(event["summary"][language])}</p>'
            html += '</div></div>'
            more_label = labels['more'] if event.get('gallery') else ('Read more' if language == 'en' else '展开详情')
            html += f'<details class="event-details"><summary>{more_label}</summary><div class="event-details-content">'
            html += ''.join(f'<p>{escape(p)}</p>' for p in event['paragraphs'][language] if p != event['summary'][language])
            photos = event.get('gallery', [])
            if photos:
                html += f'<h4>{labels["photos"]}</h4><div class="event-gallery">'
                for photo in photos:
                    cap = escape(photo['caption'][language], quote=True)
                    src = escape(photo['src'], quote=True)
                    html += f'<a href="{src}" data-cap="{cap}"><img src="{src}" alt="{cap}" loading="lazy" decoding="async"></a>'
                html += '</div>'
            html += '</div></details></article>'
        html += '</section>'
    return html
