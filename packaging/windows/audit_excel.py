"""Fail if Excel files exist in the index or reachable local Git history.

Use --remote to additionally verify that advertised GitHub heads/tags are
represented locally. This is a read-only audit, not a history rewrite.
"""
import argparse
from pathlib import Path
import subprocess

EXCEL = {'.xls', '.xlsx', '.xlsm', '.xlsb', '.xlt', '.xltx', '.xltm', '.xla', '.xlam'}
ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote', action='store_true')
    args = parser.parse_args()
    if git('rev-parse', '--is-shallow-repository').strip() != b'false':
        raise SystemExit('A full clone is required to audit history.')
    indexed = git('ls-files', '-z').split(b'\0')
    # --no-renames exposes both old and new names, including deleted files.
    historical = git('log', '--all', '-m', '--format=', '--name-only', '--no-renames', '-z').split(b'\0')
    matches = {p.decode('utf-8', 'replace').strip('\n') for p in indexed + historical
               if Path(p.decode('utf-8', 'replace').strip('\n')).suffix.lower() in EXCEL}
    if matches:
        raise SystemExit('Excel paths found in Git. Stop packaging and remove them from Git history.')
    if args.remote:
        for line in git('ls-remote', '--heads', '--tags', 'origin').splitlines():
            oid, ref = line.split()
            # Verify the exact remote history, even if local tracking refs are stale.
            history = git('log', oid.decode(), '-m', '--format=', '--name-only', '--no-renames', '-z')
            if any(Path(p.decode('utf-8', 'replace').strip('\n')).suffix.lower() in EXCEL
                   for p in history.split(b'\0')):
                raise SystemExit('Excel paths found in remote history: ' + ref.decode())
        print('Remote branches and tags: no Excel paths in reachable history.')
    for extension in EXCEL:
        for variant in (extension, extension.upper()):
            path = '__excel_ignore_audit__/example' + variant
            result = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--', path])
            if result.returncode:
                raise SystemExit('Excel ignore coverage is incomplete: ' + variant)
    # Enumerate source areas only; do not enter environments/caches or read files.
    ignored = {'.git', '.venv', '.build-venv', '.pytest_cache', 'node_modules', 'build', 'dist', 'test-results'}
    import os
    count = 0
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ignored]
        for name in files:
            if Path(name).suffix.lower() in EXCEL:
                path = str(Path(directory, name).relative_to(ROOT))
                result = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '--', path])
                if result.returncode:
                    raise SystemExit('An Excel file is not ignored. Stop packaging.')
                count += 1
    print(f'PASS: index/history contain no Excel paths; {count} local Excel files are ignored.')


if __name__ == '__main__':
    main()
