"""The archive must preserve dated facts and remain readable without client rendering."""
from pathlib import Path
import sys
import unittest
import re
from html import unescape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_site import read_json
from event_archive import validate_archive, render_archive


class EventArchive(unittest.TestCase):
    def test_public_records_are_unique_and_community_archives_are_relocated(self):
        for filename in ('events.html', 'events-zh.html'):
            html = (ROOT / filename).read_text(encoding='utf-8')
            ids = re.findall(r'class="event-card public-event" id="([^"]+)"', html)
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(set(ids)), 10)
            self.assertEqual(ids.count('2024-geling-yan'), 1)
            self.assertNotIn('archive-title-7', html)
            self.assertNotIn('archive-title-6', html)
        about = (ROOT / 'content/pages/about.html').read_text(encoding='utf-8')
        workshops = (ROOT / 'content/pages/workshops.html').read_text(encoding='utf-8')
        for number in (7, 8, 11):
            self.assertIn(f'archive-title-{number}', about)
        self.assertIn('decal-semester-archive', workshops)

    def test_archive_facts_and_assets(self):
        records = read_json('event-archive.json')
        validate_archive(records, ROOT)
        events = {event['id']: event for event in records}
        self.assertEqual(events['2024-geling-yan']['date'], '2024-04-12')
        self.assertIn('2030', events['2023-piano-in-a-factory']['location']['en'])
        self.assertIn('online', events['2023-still-life']['people']['en'])
        self.assertNotIn('Zhou Hao', events['2021-chinese-mayor']['people']['en'])

    def test_bad_date_and_missing_assets_rejected(self):
        events = read_json('event-archive.json')
        events[0]['date'] = '2024-02-30'
        with self.assertRaises(ValueError):
            validate_archive(events, ROOT)
        events = read_json('event-archive.json')
        events[0]['cover'] = 'images/missing.jpg'
        with self.assertRaises(ValueError):
            validate_archive(events, ROOT)

    def test_static_bilingual_archive_order_and_details(self):
        events = read_json('event-archive.json')
        for language in ('en', 'zh'):
            html = render_archive(events, language)
            self.assertLess(html.index('id="2024-geling-yan"'), html.index('id="2021-chinese-mayor"'))
            self.assertIn('<details', html)
            self.assertIn('datetime="2024-04"', html)
            self.assertNotIn('mail.google.com', html)
            self.assertNotIn('2023 · 10 · 22', html)
            self.assertNotIn('event-logistics', html)
            self.assertNotIn('Around 2017', html)
            self.assertNotIn('datetime="2024-04-12"', html)
