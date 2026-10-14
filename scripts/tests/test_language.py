"""Regression checks for static language controls and Chinese generation."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_chinese import translate
from site_contract import PUBLIC_PATHS

class LanguageControl(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.destination = None
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'span' and values.get('aria-current') == 'true':
            self.current = values.get('lang')
        if tag == 'a' and values.get('href') in PUBLIC_PATHS.values() and values.get('lang'):
            self.destination = (values['href'], values['lang'])

class LanguageRegression(unittest.TestCase):
    def test_language_controls_point_to_opposite_edition(self):
        for name, current, destination in (
            ('index.html', 'en', ('zh.html', 'zh-Hans')),
            ('zh.html', 'zh-Hans', ('index.html', 'en')),
            ('collaboration.html', 'en', ('collaboration-zh.html', 'zh-Hans')),
            ('collaboration-zh.html', 'zh-Hans', ('collaboration.html', 'en')),
        ):
            with self.subTest(page=name):
                parser = LanguageControl()
                parser.feed((ROOT / name).read_text(encoding='utf-8'))
                self.assertEqual(parser.current, current)
                self.assertEqual(parser.destination, (PUBLIC_PATHS[destination[0]], destination[1]))

    def test_chinese_page_matches_generator(self):
        for source, destination in (('index.html','zh.html'), ('collaboration.html','collaboration-zh.html')):
            with self.subTest(page=destination):
                self.assertEqual((ROOT / destination).read_text(encoding='utf-8'), translate((ROOT / source).read_text(encoding='utf-8')))

    def test_translation_preserves_code_comments_and_categories(self):
        source = '<!-- Home --><script>const label="Home";</script><style>.Home{color:red}</style><button data-filter="Lecture">Lecture</button>'
        result = translate(source)
        self.assertIn('<!-- Home -->', result)
        self.assertIn('const label="Home";', result)
        self.assertIn('.Home{color:red}', result)
        self.assertIn('data-filter="Lecture">讲座', result)

    def test_bilingual_blocks_have_one_description(self):
        page = (ROOT / 'contact-zh.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('登记邮箱，接收大同学社的活动通知与最新消息。'), 1)
        self.assertNotIn('&amp;amp;', page)

    def test_contact_has_no_pronoun_annotation(self):
        for name in ('contact.html', 'contact-zh.html'):
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertNotIn('He/Him', text)
            self.assertIn('mailto:greenw@berkeley.edu', text)
