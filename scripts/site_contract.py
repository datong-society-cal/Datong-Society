"""Shared static artifact contract. Python standard library only."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit

SITE_URL = 'https://datong.studentorg.berkeley.edu/'
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 32 * 1024 * 1024
PAGE_ROUTES = {
    'home': ('index.html', 'zh.html', 'Home'),
    'workshops': ('workshops.html', 'workshops-zh.html', 'Workshops'),
    'events': ('events.html', 'events-zh.html', 'Public Events'),
    'resources': ('resources.html', 'resources-zh.html', 'Resources'),
    'about': ('about.html', 'about-zh.html', 'About Us'),
    'contact': ('contact.html', 'contact-zh.html', 'Contact Us'),
    'collaboration': ('collaboration.html', 'collaboration-zh.html', 'Collaboration'),
}
PUBLIC_PATHS = {filename: ('zh/' if language else '') + slug
                for slug, row in PAGE_ROUTES.items()
                for language, filename in enumerate(row[:2])}
ROUTE_FILES = {path: filename for filename, path in PUBLIC_PATHS.items()}
REDIRECTS = {'': 'home', **PUBLIC_PATHS,
             **{path + '/': path for path in ROUTE_FILES}}
REWRITES = 'RewriteEngine On\n'
for filename, path in PUBLIC_PATHS.items():
    REWRITES += r'RewriteCond %{THE_REQUEST} \s/+[^\s?]*' + re.escape(filename) + r'(?:[?\s])' + '\n'
    REWRITES += 'RewriteRule ^' + re.escape(filename) + '$ ' + path + ' [R=301,L,NE]\n'
REWRITES += 'RewriteRule ^$ home [R=301,L]\n'
REWRITES += 'RewriteRule ^((?:zh/)?(?:' + '|'.join(PAGE_ROUTES) + '))/$ $1 [R=301,L]\n'
for path, filename in ROUTE_FILES.items():
    REWRITES += 'RewriteRule ^' + path + '$ ' + filename + ' [END]\n'
APACHE = '''# Managed static website. Do not restore legacy WordPress rewrite rules.
DirectoryIndex index.html
Options -Indexes -MultiViews
''' + REWRITES + '''
<IfModule mod_headers.c>
    Header set X-Content-Type-Options "nosniff"
    <FilesMatch "\\.(html|json)$">
        Header set Cache-Control "no-cache"
    </FilesMatch>
    <FilesMatch "\\.(css|js)$">
        Header set Cache-Control "public, max-age=3600"
    </FilesMatch>
    <FilesMatch "\\.(jpg|jpeg|png|svg|webp|gif|ico|otf|woff2?|ttf|eot)$">
        Header set Cache-Control "public, max-age=86400"
    </FilesMatch>
</IfModule>
'''
# Retained releases used this previously reviewed static configuration. Accept
# its exact bytes as well so rollback remains possible after the URL migration.
LEGACY_APACHE = APACHE[:APACHE.index('Options')] + 'Options -Indexes\n' + APACHE[APACHE.index('<IfModule'):]
ROOT_FILES = {'index.html', 'collaboration.html', 'LICENSE.txt', '.htaccess', 'deploy-version.json'}
LANGUAGE_FILES = {'zh.html', 'collaboration-zh.html'}
CONTENT_FILES = {name + suffix + '.html' for name in ('about', 'contact', 'events', 'resources', 'workshops') for suffix in ('', '-zh')}
EXTENSIONS = {
    'assets/css': {'.css'}, 'assets/js': {'.js'},
    'assets/fonts': {'.otf', '.woff2', '.woff', '.ttf', '.svg', '.eot'},
    'images': {'.jpg', '.jpeg', '.png', '.svg', '.webp', '.gif', '.ico'},
}

def allowed(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or any(p.startswith('.') for p in path.parts):
        return name == '.htaccess'
    if str(path) != name or not re.fullmatch(r'[A-Za-z0-9_./-]+', name):
        return False
    return name in ROOT_FILES | LANGUAGE_FILES | CONTENT_FILES or any(name.startswith(prefix + '/') and path.suffix.lower() in exts
        for prefix, exts in EXTENSIONS.items())

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'base':
            return
        if 'id' in values:
            self.ids.add(values['id'])
        for attr in ('src', 'href', 'poster'):
            if values.get(attr):
                self.refs.append(values[attr])

        source = values.get('src', '')
        if tag == 'img' and (source.startswith('images/events/') or source.startswith('images/qr/')):
            if values.get('loading') != 'lazy' or values.get('decoding') != 'async':
                raise ValueError('Noncritical event and QR images must use lazy loading: ' + source)

def validate_tree(root, expected_commit=None):
    root = Path(root)
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Symlinks are not deployable')
    if set(files) - {n for n in files if allowed(n) or n == 'manifest.json'}:
        raise ValueError('Unexpected file in artifact')
    if not ROOT_FILES.issubset(files):
        raise ValueError('Missing required public files')
    if sum(p.stat().st_size for p in files.values()) > MAX_TOTAL or any(p.stat().st_size > MAX_FILE for p in files.values()):
        raise ValueError('Artifact exceeds size limit')
    if files['.htaccess'].read_text() not in (APACHE, LEGACY_APACHE):
        raise ValueError('Apache configuration differs from the reviewed static configuration')
    html = files['index.html'].read_text(encoding='utf-8')
    if len(html) < 1000 or 'Hosted by the OCF' not in html or 'acting independently of the University of California' not in html:
        raise ValueError('Missing site content or required hosting attribution')
    if not any(f'rel="canonical" href="{url}"' in html for url in (SITE_URL, SITE_URL + 'home')):
        raise ValueError('Production canonical URL missing')
    if 'rel="icon" type="image/png" href="images/brand/datong-logo-emblem.png"' not in html:
        raise ValueError('Datong logo favicon missing')
    parsed = References()
    parsed.feed(html)
    parsed.feed(files['collaboration.html'].read_text(encoding='utf-8'))
    for name in (LANGUAGE_FILES | CONTENT_FILES) & files.keys():
        parsed.feed(files[name].read_text(encoding='utf-8'))
    missing = []
    def check(ref, parent):
        url = urlsplit(ref)
        if url.scheme or url.netloc:
            return
        if not url.path:
            return  # SVG references and client-side navigation use fragments.
        if url.path.startswith('/'):
            raise ValueError('Root-relative asset breaks the OCF /~datong path: ' + ref)
        # resolve() is case-insensitive on Windows; compare normalized names instead.
        import posixpath
        name = posixpath.normpath(posixpath.join(parent, unquote(url.path)))
        name = ROUTE_FILES.get(name, name)
        if name not in files:
            missing.append(name)
    for ref in parsed.refs:
        check(ref, '')
    for name, path in files.items():
        if name.endswith('.css'):
            for match in re.finditer(r'''url\(\s*['"]?([^)'"\s]+)['"]?\s*\)''', path.read_text(encoding='utf-8')):
                check(match.group(1), str(PurePosixPath(name).parent))
    if missing:
        raise ValueError('Missing references (case sensitive): ' + ', '.join(sorted(set(missing))))
    version = json.loads(files['deploy-version.json'].read_text())
    if not re.fullmatch(r'[0-9a-f]{40}', version.get('commit', '')):
        raise ValueError('Invalid commit identifier')
    if expected_commit and version['commit'] != expected_commit:
        raise ValueError('Artifact commit mismatch')
    if 'manifest.json' in files:
        manifest = json.loads(files['manifest.json'].read_text())
        actual = {name: digest(path) for name, path in files.items() if name != 'manifest.json'}
        if manifest != actual:
            raise ValueError('Artifact manifest mismatch')
    return files
