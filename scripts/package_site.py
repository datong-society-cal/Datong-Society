"""Validate and package committed static files; no CSS rebuild or dependencies."""
import argparse
import gzip
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import tarfile
from urllib.parse import unquote, urlsplit
from site_contract import APACHE, EXTENSIONS, ROOT_FILES, PAGE_FILES, References, allowed, digest, validate_tree

def unreferenced(output):
    """Published assets that no page or stylesheet references."""
    refs = set()
    def add(ref, parent):
        url = urlsplit(ref)
        if not (url.scheme or url.netloc) and url.path:
            refs.add(posixpath.normpath(posixpath.join(parent, unquote(url.path))))
    for page in output.glob('*.html'):
        parser = References()
        parser.feed(page.read_text(encoding='utf-8'))
        for ref in parser.refs:
            add(ref, '')
    for sheet in output.glob('assets/css/*.css'):
        for match in re.finditer(r'''url\(\s*['"]?([^)'"\s]+)['"]?\s*\)''', sheet.read_text(encoding='utf-8')):
            add(match.group(1), str(PurePosixPath(sheet.relative_to(output).as_posix()).parent))
    assets = {p.relative_to(output).as_posix() for prefix in EXTENSIONS for p in (output / prefix).rglob('*') if p.is_file()}
    return sorted(assets - refs)

def package(commit):

    repo = Path(__file__).resolve().parent.parent
    output = repo / 'dist'
    if output.is_symlink():
        raise ValueError('Refusing symlink output')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=repo).decode().split('\0')
    for name in tracked:
        if name in ROOT_FILES | PAGE_FILES or any(name.startswith(p + '/') for p in EXTENSIONS):
            if not allowed(name):
                continue  # e.g. images/README.md and CSS build notes are maintenance files.
            source = repo / name
            if source.is_symlink():
                raise ValueError('Tracked symlink rejected: ' + name)
            destination = output / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    unused = unreferenced(output)
    if unused:
        raise ValueError('Unreferenced files would be published; delete them or link them: ' + ', '.join(unused))
    (output / '.htaccess').write_text(APACHE, encoding='utf-8', newline='\n')
    (output / 'deploy-version.json').write_text(json.dumps({'commit': commit}) + '\n', encoding='utf-8')
    files = validate_tree(output, commit)
    (output / 'manifest.json').write_text(json.dumps({n: digest(p) for n, p in sorted(files.items())}, indent=2) + '\n')
    validate_tree(output, commit)
    archive = repo / 'site.tar.gz'
    with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as tar:
            for file in sorted(output.rglob('*')):
                if file.is_file():
                    data = file.read_bytes()
                    info = tarfile.TarInfo(file.relative_to(output).as_posix())
                    info.size, info.mode, info.mtime = len(data), 0o644, 0
                    tar.addfile(info, io.BytesIO(data))
    print(f'Validated {len(files)} public files; artifact {archive.name}: {archive.stat().st_size:,} bytes; commit {commit}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    package(args.commit)
