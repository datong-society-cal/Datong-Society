"""Local preview using the same clean routes as OCF, bound to localhost only."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from site_contract import REDIRECTS, ROUTE_FILES, allowed

ROOT = Path(__file__).resolve().parent.parent

class SiteHandler(SimpleHTTPRequestHandler):
    def prepare(self):
        url = urlsplit(self.path)
        path = unquote(url.path).lstrip('/')
        if path.startswith('~datong/'):
            prefix, path = '/~datong/', path[len('~datong/'):]
        else:
            prefix = '/'
        if path in REDIRECTS:
            target = prefix + REDIRECTS[path]
            if url.query:
                target += '?' + url.query
            self.send_response(301)
            self.send_header('Location', target)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return False
        filename = ROUTE_FILES.get(path, path)
        if not allowed(filename) or filename == '.htaccess' or not (ROOT / filename).is_file():
            self.send_error(404)
            return False
        self.path = '/' + filename + ('?' + url.query if url.query else '')
        return True

    def do_GET(self):
        if self.prepare():
            super().do_GET()

    def do_HEAD(self):
        if self.prepare():
            super().do_HEAD()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SiteHandler, directory=str(ROOT)))
    print(f'Preview: http://127.0.0.1:{args.port}/home', flush=True)
    server.serve_forever()

if __name__ == '__main__':
    main()
