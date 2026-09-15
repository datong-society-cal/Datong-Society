"""Negative-path tests for the deployment boundary, not website content snapshots."""
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from site_contract import APACHE, MAX_FILE, MAX_TOTAL, SITE_URL, allowed, digest, validate_tree
from ocf_receive import unpack

COMMIT = 'a' * 40

class ArtifactSecurity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def make_archive(self, entries):
        archive = self.root / 'upload.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            for name, kind, content in entries:
                member = tarfile.TarInfo(name)
                member.type = kind
                member.linkname = '/etc/passwd' if kind == tarfile.SYMTYPE else ''
                member.size = len(content) if kind == tarfile.REGTYPE else 0
                tar.addfile(member, io.BytesIO(content) if member.isfile() else None)
        return archive
    def rejects(self, entries):
        with self.assertRaises((ValueError, tarfile.TarError)):
            unpack(self.make_archive(entries), self.root / 'site')
    def test_path_traversal(self):
        self.rejects([('../index.html', tarfile.REGTYPE, b'bad')])
        self.assertFalse((self.root.parent / 'index.html').exists())
    def test_absolute_path(self):
        self.rejects([('/index.html', tarfile.REGTYPE, b'bad')])
    def test_symlink(self):
        self.rejects([('images/test.png', tarfile.SYMTYPE, b'')])
    def test_duplicate(self):
        self.rejects([('index.html', tarfile.REGTYPE, b'1'), ('index.html', tarfile.REGTYPE, b'2')])
    def test_server_executable(self):
        self.rejects([('images/attack.php', tarfile.REGTYPE, b'bad')])
    def test_hidden_config(self):
        self.assertFalse(allowed('images/.htaccess'))
        self.assertFalse(allowed('.ssh/authorized_keys'))
        self.assertFalse(allowed('assets/js/../../index.html'))
    def test_regular_static_extract(self):
        unpack(self.make_archive([('images/photo.jpg', tarfile.REGTYPE, b'image')]), self.root / 'site')
        self.assertEqual((self.root / 'site/images/photo.jpg').read_bytes(), b'image')

class ManifestSecurity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        html = f'<html><head><link rel="canonical" href="{SITE_URL}"><link rel="icon" type="image/png" href="images/brand/datong-logo-emblem.png"></head><body>Hosted by the OCF; acting independently of the University of California' + ' ' * 1000 + '</body></html>'
        for name, value in {'index.html':html, '.htaccess':APACHE, 'LICENSE.txt':'License',
                'deploy-version.json':json.dumps({'commit':COMMIT})}.items():
            (self.root / name).write_text(value)
        favicon = self.root / 'images/brand/datong-logo-emblem.png'
        favicon.parent.mkdir(parents=True)
        favicon.write_bytes(b'logo')
        self.manifest()
    def tearDown(self):
        self.temp.cleanup()
    def manifest(self):
        (self.root / 'manifest.json').write_text(json.dumps({
            p.relative_to(self.root).as_posix():digest(p)
            for p in self.root.rglob('*') if p.is_file() and p.name != 'manifest.json'
        }))
    def test_valid_manifest(self):
        validate_tree(self.root, COMMIT)
    def test_tampered_file(self):
        (self.root / 'LICENSE.txt').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'manifest mismatch'):
            validate_tree(self.root, COMMIT)
    def test_wrong_commit(self):
        with self.assertRaisesRegex(ValueError, 'commit mismatch'):
            validate_tree(self.root, 'b' * 40)
    def test_unreviewed_apache_directive(self):
        with (self.root / '.htaccess').open('a') as f:
            f.write('SetHandler application/x-httpd-php\n')
        self.manifest()
        with self.assertRaisesRegex(ValueError, 'Apache configuration'):
            validate_tree(self.root, COMMIT)
    def test_linux_filename_case(self):
        with (self.root / 'index.html').open('a') as f:
            f.write('<a href="license.txt">License</a>')
        self.manifest()
        with self.assertRaisesRegex(ValueError, 'case sensitive'):
            validate_tree(self.root, COMMIT)
    def test_extra_server_file(self):
        (self.root / 'debug.php').write_text('unexpected')
        with self.assertRaisesRegex(ValueError, 'Unexpected file'):
            validate_tree(self.root, COMMIT)

    def test_performance_budget(self):
        self.assertEqual(MAX_FILE, 8 * 1024 * 1024)
        self.assertEqual(MAX_TOTAL, 32 * 1024 * 1024)

if __name__ == '__main__':
    unittest.main()
