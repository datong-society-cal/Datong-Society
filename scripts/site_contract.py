"""Shared static artifact contract. Python standard library only."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import unquote, urlsplit

SITE_URL = 'https://datong.studentorg.berkeley.edu/'
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL = 400 * 1024 * 1024
APACHE = '''# Managed static website. Do not restore legacy WordPress rewrite rules.
DirectoryIndex index.html
Options -Indexes
<IfModule mod_headers.c>
    Header set X-Content-Type-Options "nosniff"
    <FilesMatch "\\.(html|css|js|json)$">
        Header set Cache-Control "no-cache"
    </FilesMatch>
</IfModule>
'''
ROOT_FILES = {'index.html', 'LICENSE.txt', '.htaccess', 'deploy-version.json'}
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
    return name in ROOT_FILES or any(name.startswith(prefix + '/') and path.suffix.lower() in exts
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
        if 'id' in values:
            self.ids.add(values['id'])
        for attr in ('src', 'href', 'poster'):
            if values.get(attr):
                self.refs.append(values[attr])

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
    if files['.htaccess'].read_text() != APACHE:
        raise ValueError('Apache configuration differs from the reviewed static configuration')
    html = files['index.html'].read_text(encoding='utf-8')
    if len(html) < 1000 or 'Hosted by the OCF' not in html or 'acting independently of the University of California' not in html:
        raise ValueError('Missing site content or required hosting attribution')
    if f'rel="canonical" href="{SITE_URL}"' not in html:
        raise ValueError('Production canonical URL missing')
    parsed = References()
    parsed.feed(html)
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
