#!/usr/bin/env python3
"""Install once in ~/deploy/bin; run only through an SSH forced command.

The CI identity can publish validated static archives or roll back retained releases.
It cannot run a shell, upload a receiver, read archives, or choose filesystem paths.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from urllib.request import Request, urlopen
from site_contract import MAX_FILE, MAX_TOTAL, SITE_URL, allowed, validate_tree

HOME = Path('/home/d/da/datong')
BASE = HOME / 'deploy'
WEB = Path('/services/http/users/d/datong')
MAX_COMPRESSED = 200 * 1024 * 1024

def unpack(archive, target):
    total, seen = 0, set()
    with tarfile.open(archive, 'r:gz') as tar:
        for item in tar:
            name = item.name
            if name in seen or not item.isfile() or not (allowed(name) or name == 'manifest.json'):
                raise ValueError('Archive contains a duplicate, nonregular, or forbidden entry')
            if str(PurePosixPath(name)) != name or item.size < 0 or item.size > MAX_FILE:
                raise ValueError('Invalid archive path or size')
            seen.add(name)
            total += item.size
            if total > MAX_TOTAL or len(seen) > 5000:
                raise ValueError('Archive exceeds bounds')
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(item) as source, destination.open('wb') as output:
                shutil.copyfileobj(source, output)
            destination.chmod(0o644)

def sync(source, dry_run=False, restore=False):
    command = ['rsync', '-a' if restore else '-rltp', '--checksum', '--delete-delay', '--delay-updates']
    if not restore:
        command += ['--chmod=D755,F644', '--exclude=/manifest.json', '--delete-excluded']
    if dry_run:
        command += ['--dry-run', '--itemize-changes']
    command += [str(source) + '/', str(WEB) + '/']
    subprocess.run(command, check=True)

def verify_disk(source):
    expected = json.loads((source / 'manifest.json').read_text())
    actual_files = {p.relative_to(WEB).as_posix(): p for p in WEB.rglob('*') if p.is_file()}
    if any(p.is_symlink() for p in WEB.rglob('*')) or set(actual_files) != set(expected):
        raise ValueError('Production file set differs from artifact')
    for name, path in actual_files.items():
        if path.stat().st_mode & 0o777 != 0o644:
            raise ValueError('Production file permission mismatch: ' + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected[name]:
            raise ValueError('Production hash mismatch: ' + name)

def smoke(source):
    names = ['index.html', 'deploy-version.json', 'assets/css/main.css',
             'assets/js/main.js', 'images/brand/datong-logo-emblem.png',
             'images/qr/qr-wechat-official.jpg']
    for attempt in range(4):
        try:
            for name in names:
                request = Request(SITE_URL + name + '?deployment-check=' + str(time.time_ns()),
                    headers={'Cache-Control': 'no-cache', 'User-Agent': 'Datong-deployment-check'})
                with urlopen(request, timeout=20) as response:
                    if response.status != 200 or response.read() != (source / name).read_bytes():
                        raise ValueError('HTTP content mismatch: ' + name)
            return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2)

def write_json(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n')
    temp.chmod(0o600)
    temp.replace(path)

def run():
    import fcntl  # Linux-only publishing; artifact validation also runs on Windows.
    os.umask(0o077)
    match = re.fullmatch(r'(publish|rollback) ([0-9a-f]{40}) ([1-9][0-9]{0,15}) ([1-9][0-9]{0,5})',
        os.environ.get('SSH_ORIGINAL_COMMAND', ''))
    if not match:
        raise ValueError('Only publish/rollback COMMIT RUN_ID ATTEMPT is accepted')
    mode, commit, run_id, attempt = match.groups()
    sequence = [int(run_id), int(attempt)]
    if Path.home() != HOME or (HOME / 'public_html').resolve() != WEB or WEB.is_symlink() or not WEB.is_dir():
        raise ValueError('Unexpected OCF account or web root')
    BASE.mkdir(mode=0o700, exist_ok=True)
    with (BASE / 'publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state_path = BASE / 'state.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        if sequence <= state.get('sequence', [0, 0]):
            raise ValueError('Stale or already-completed workflow run rejected')
        if not state and not (BASE / 'allow-initial-migration').is_file():
            raise ValueError('Initial migration has not been prepared by the administrator')
        releases = BASE / 'releases'
        releases.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='incoming-', dir=BASE) as temporary:
            incoming = Path(temporary)
            stage = incoming / 'site'
            if mode == 'publish':
                archive = incoming / 'site.tar.gz'
                size = 0
                with archive.open('wb') as output:
                    while chunk := sys.stdin.buffer.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_COMPRESSED:
                            raise ValueError('Compressed upload exceeds limit')
                        output.write(chunk)
                stage.mkdir()
                unpack(archive, stage)
            else:
                retained = releases / commit
                if not retained.is_dir() or retained.is_symlink():
                    raise ValueError('Rollback commit is not a retained release')
                shutil.copytree(retained, stage)
            validate_tree(stage, commit)
            if not (stage / 'manifest.json').is_file():
                raise ValueError('Manifest is required')
            destination = releases / commit
            if destination.exists():
                if (destination / 'manifest.json').read_bytes() != (stage / 'manifest.json').read_bytes():
                    raise ValueError('Commit already has a different retained artifact')
            sync(stage, dry_run=True)
            # Capture the actual served tree before every mutation, including first migration.
            previous = incoming / 'previous'
            shutil.copytree(WEB, previous, symlinks=True)
            try:
                sync(stage)
                verify_disk(stage)
                smoke(stage)
                if not destination.exists():
                    stage.rename(destination)
            except Exception:
                print('Verification failed; restoring the pre-deployment website.', flush=True)
                sync(previous, restore=True)
                raise
            previous_commit = state.get('commit')
            next_state = {'commit': commit, 'previous_commit': previous_commit, 'sequence': sequence,
                'mode': mode, 'published_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
            try:
                write_json(state_path, next_state)
            except Exception:
                sync(previous, restore=True)
                raise
            with (BASE / 'history.jsonl').open('a') as history:
                history.write(json.dumps(next_state) + '\n')
            (BASE / 'allow-initial-migration').unlink(missing_ok=True)
            keep = {commit, previous_commit}
            ordered = sorted((p for p in releases.iterdir() if p.is_dir()), key=lambda p:p.stat().st_mtime, reverse=True)
            keep.update(p.name for p in ordered[:3])
            for release in ordered:
                if release.name not in keep and re.fullmatch(r'[0-9a-f]{40}', release.name) and not release.is_symlink():
                    shutil.rmtree(release)
            print('Verified production release: ' + commit, flush=True)

if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        print('Deployment failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
