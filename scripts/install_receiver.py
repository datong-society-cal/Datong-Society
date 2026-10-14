"""Administrator-only receiver update; run on OCF after uploading .next files."""
import argparse
import fcntl
import hashlib
import os
from pathlib import Path
import shutil

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contract-sha', required=True)
    parser.add_argument('--receiver-sha', required=True)
    args = parser.parse_args()
    home = Path.home()
    if home != Path('/home/d/da/datong'):
        raise SystemExit('Unexpected administrator account')
    base = home / 'deploy'
    directory = base / 'bin'
    if directory.is_symlink():
        raise SystemExit('Receiver directory must not be a symlink')
    with (base / 'publish.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        expected = {'site_contract.py': args.contract_sha, 'ocf_receive.py': args.receiver_sha}
        for name, digest in expected.items():
            source = directory / (name + '.next')
            if source.is_symlink() or not source.is_file():
                raise SystemExit('Missing regular update file')
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise SystemExit('Receiver update hash mismatch')
            compile(data, name, 'exec')
            source.chmod(0o600)
        for name in expected:
            current = directory / name
            backup = directory / (name + '.previous')
            shutil.copyfile(current, backup)
            backup.chmod(0o600)
        try:
            for name in expected:
                os.replace(directory / (name + '.next'), directory / name)
        except OSError:
            for name in expected:
                shutil.copyfile(directory / (name + '.previous'), directory / name)
                (directory / name).chmod(0o600)
            raise
        print('Receiver update verified and installed under the publish lock.')

if __name__ == '__main__':
    main()
