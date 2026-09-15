"""Stream the static artifact to the restricted OCF receiver, without shell interpolation."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('mode', choices=['publish', 'rollback'])
parser.add_argument('--commit', required=True)
parser.add_argument('--run-id', required=True)
parser.add_argument('--attempt', required=True)
parser.add_argument('--key', required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parent.parent
command = ['ssh', '-i', args.key, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=yes', '-o', 'UserKnownHostsFile=' + str(repo / 'scripts/ocf-known-hosts'),
    '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=4',
    'datong@ssh.ocf.berkeley.edu', f'{args.mode} {args.commit} {args.run_id} {args.attempt}']
if args.mode == 'publish':
    with (repo / 'site.tar.gz').open('rb') as artifact:
        subprocess.run(command, stdin=artifact, check=True)
else:
    subprocess.run(command, stdin=subprocess.DEVNULL, check=True)
