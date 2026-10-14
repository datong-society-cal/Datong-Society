"""Run the same source and artifact checks locally and in GitHub Actions."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', help='Artifact version; defaults to HEAD')
    args = parser.parse_args()
    subprocess.run([sys.executable, 'scripts/build_site.py'], cwd=ROOT, check=True)
    node = shutil.which('node') or str(Path(sys.executable).parents[1] / 'node/bin/node.exe')
    if not Path(node).is_file():
        raise SystemExit('Node.js is required for JavaScript syntax checks; supply it on PATH.')
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts/tests', '-v'], cwd=ROOT, check=True)
    for script in sorted((ROOT / 'assets/js').glob('*.js')):
        subprocess.run([node, '--check', str(script)], cwd=ROOT, check=True)
    subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
    commit = args.commit or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    subprocess.run([sys.executable, 'scripts/package_site.py', '--commit', commit], cwd=ROOT, check=True)
    print('Source tests, JavaScript syntax and static artifact checks passed.')

if __name__ == '__main__':
    main()
