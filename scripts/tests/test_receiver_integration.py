"""Exercise real rsync and restore in a temporary webspace, never production.

HTTPS checks are mocked here; the actual deployment performs live HTTPS checks.
"""
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ocf_receive as receiver
from site_contract import APACHE, SITE_URL, digest

@unittest.skipUnless(sys.platform.startswith('linux') and shutil.which('rsync'), 'Requires Linux rsync')
class ReceiverIntegration(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.web = self.root / 'web'
        self.web.mkdir()
        self.base = self.home / 'deploy'
        self.base.mkdir()
        (self.home / 'public_html').symlink_to(self.web, target_is_directory=True)
        (self.web / 'old.php').write_text('legacy')
        (self.web / 'old.php').chmod(0o400)
        (self.web / '.htaccess').write_text('legacy rewrite')
        (self.base / 'allow-initial-migration').touch()
    def tearDown(self):
        self.temporary.cleanup()
    def artifact(self, commit):
        stage = self.root / ('build-' + commit)
        stage.mkdir()
        values = {
            'index.html':f'<link rel="canonical" href="{SITE_URL}"><link rel="icon" type="image/png" href="images/brand/datong-logo-emblem.png"> Hosted by the OCF; acting independently of the University of California ' + 'content ' * 200,
            '.htaccess':APACHE, 'LICENSE.txt':'license',
            'deploy-version.json':json.dumps({'commit':commit})
        }
        for name, data in values.items():
            (stage / name).write_text(data)
        favicon = stage / 'images/brand/datong-logo-emblem.png'
        favicon.parent.mkdir(parents=True)
        favicon.write_bytes(b'logo')
        (stage / 'manifest.json').write_text(json.dumps({
            p.relative_to(stage).as_posix():digest(p)
            for p in stage.rglob('*') if p.is_file()
        }))
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode='w:gz') as tar:
            for file in stage.rglob('*'):
                if file.is_file():
                    tar.add(file, arcname=file.relative_to(stage).as_posix())
        return output.getvalue()
    def invoke(self, mode, commit, run, payload=b'', fail_http=False):
        with patch.multiple(receiver, HOME=self.home, BASE=self.base, WEB=self.web), \
             patch.object(Path, 'home', return_value=self.home), \
             patch.dict('os.environ', {'SSH_ORIGINAL_COMMAND':f'{mode} {commit} {run} 1'}), \
             patch.object(sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(payload))), \
             patch.object(receiver, 'smoke', side_effect=RuntimeError('simulated HTTPS failure') if fail_http else None):
            receiver.run()
    def test_publish_then_rollback_and_reject_stale_run(self):
        a, b = 'a' * 40, 'b' * 40
        self.invoke('publish', a, 1, self.artifact(a))
        self.assertFalse((self.web / 'old.php').exists())
        self.assertFalse((self.web / 'manifest.json').exists())
        self.assertEqual((self.web / 'index.html').stat().st_mode & 0o777, 0o644)
        self.invoke('publish', b, 2, self.artifact(b))
        self.invoke('rollback', a, 3)
        self.assertEqual(json.loads((self.web / 'deploy-version.json').read_text())['commit'], a)
        self.assertEqual(json.loads((self.base / 'state.json').read_text())['sequence'], [3, 1])
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.invoke('rollback', b, 2)
        self.assertEqual(json.loads((self.web / 'deploy-version.json').read_text())['commit'], a)
    def test_failed_first_publish_restores_legacy_and_permissions(self):
        a = 'a' * 40
        with self.assertRaisesRegex(RuntimeError, 'simulated HTTPS failure'):
            self.invoke('publish', a, 1, self.artifact(a), fail_http=True)
        self.assertEqual((self.web / 'old.php').read_text(), 'legacy')
        self.assertEqual((self.web / 'old.php').stat().st_mode & 0o777, 0o400)
        self.assertEqual((self.web / '.htaccess').read_text(), 'legacy rewrite')
        self.assertFalse((self.base / 'state.json').exists())
        self.assertTrue((self.base / 'allow-initial-migration').exists())
    def test_initial_publish_requires_administrator_marker(self):
        (self.base / 'allow-initial-migration').unlink()
        with self.assertRaisesRegex(ValueError, 'not been prepared'):
            self.invoke('publish', 'a' * 40, 1)
        self.assertTrue((self.web / 'old.php').exists())
