"""HTTP regression checks for legacy redirects, clean URLs, and subpath hosting."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPRedirectHandler, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve_site import ROOT, SiteHandler
from site_contract import PUBLIC_PATHS, ROUTE_FILES, REWRITES, SITE_URL

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

class QuietHandler(SiteHandler):
    def log_message(self, *args):
        pass

class CleanRoutes(unittest.TestCase):
    def test_production_redirects_use_absolute_https_targets(self):
        redirects = [line for line in REWRITES.splitlines() if '[R=301' in line]
        self.assertTrue(redirects)
        for rule in redirects:
            self.assertTrue(rule.split()[2].startswith(SITE_URL), rule)

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_pages_and_subpath_assets(self):
        for prefix in ('/', '/~datong/'):
            for path, filename in ROUTE_FILES.items():
                with urlopen(self.base + prefix + path) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), (ROOT / filename).read_bytes())
            with urlopen(self.base + prefix + 'assets/css/main.css') as response:
                self.assertEqual(response.status, 200)

    def test_old_urls_redirect_once_and_keep_query(self):
        for prefix in ('/', '/~datong/'):
            for old, new in {'': 'home', **PUBLIC_PATHS}.items():
                with self.assertRaises(HTTPError) as caught:
                    build_opener(NoRedirect).open(self.base + prefix + old + '?utm_source=test')
                self.assertEqual(caught.exception.code, 301)
                self.assertEqual(caught.exception.headers['Location'], prefix + new + '?utm_source=test')
                caught.exception.close()

    def test_trailing_slashes_and_unknown_paths(self):
        for path in ('workshops/', 'zh/workshops/'):
            with urlopen(self.base + '/' + path) as response:
                self.assertEqual(response.url, self.base + '/' + path.rstrip('/'))
        for path in ('not-a-page', 'zh/not-a-page', 'scripts/build_site.py', '.git/config'):
            with self.assertRaises(HTTPError) as caught:
                urlopen(self.base + '/' + path)
            self.assertEqual(caught.exception.code, 404)
            caught.exception.close()
