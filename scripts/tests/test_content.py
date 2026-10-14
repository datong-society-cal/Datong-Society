"""Checks for content boundaries and the generated multi-page navigation."""
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_site import PAGES, read_json, validate_content
from build_chinese import translate

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.language = None
        self.destinations = []
        self.current = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.language = attrs.get('lang')
        if tag == 'a':
            self.destinations.append(attrs.get('href', ''))
            if attrs.get('aria-current') == 'page':
                self.current.append(attrs['href'])

class ContentInfrastructure(unittest.TestCase):
    def test_content_is_valid(self):
        validate_content(read_json('events.json'), read_json('resources.json'))

    def test_duplicate_ids_and_insecure_urls_rejected(self):
        resources = read_json('resources.json')
        with self.assertRaises(ValueError):
            validate_content([], resources + [resources[0]])
        resources[0]['url'] = 'javascript:alert(1)'
        with self.assertRaises(ValueError):
            validate_content([], resources)

    def test_event_end_requires_timezone_and_order(self):
        events = read_json('events.json')
        events[0]['end'] = events[0]['start']
        with self.assertRaises(ValueError):
            validate_content(events, [])

    def test_all_pages_translate_and_link_to_same_language(self):
        for page, (en, zh, title) in PAGES.items():
            english = (ROOT / en).read_text(encoding='utf-8')
            chinese = (ROOT / zh).read_text(encoding='utf-8')
            self.assertEqual(chinese, translate(english), zh)
            for filename, html, language in ((en, english, 'en'), (zh, chinese, 'zh-Hans')):
                parser = Links()
                parser.feed(html)
                self.assertEqual(parser.language, language)
                expected = [row[0 if language == 'en' else 1] for key, row in PAGES.items() if key != 'collaboration']
                self.assertTrue(set(expected).issubset(parser.destinations), filename)
                self.assertNotIn('href="#resources"', html)
                if page != 'collaboration':
                    self.assertEqual(parser.current, [filename])

    def test_contact_uses_society_inbox(self):
        for filename in ('contact.html', 'contact-zh.html'):
            html = (ROOT / filename).read_text(encoding='utf-8')
            self.assertIn('mailto:datongsociety@gmail.com', html)
            self.assertNotIn('formsubmit.co', html)
