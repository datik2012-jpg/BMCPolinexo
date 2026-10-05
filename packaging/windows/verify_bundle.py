"""Audit explicit web assets and reject private/source artifacts in a bundle."""
import argparse
import hashlib
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = {'.xlsx', '.xls', '.xlsm', '.xlsb', '.xlt', '.xltm', '.xltx', '.xla', '.xlam', '.csv', '.pdf', '.docx', '.py', '.map'}


def verify_web(web):
    public = [Path(line) for line in (Path(__file__).with_name('public-assets.txt')).read_text(encoding='utf-8-sig').splitlines() if line]
    expected = {p.relative_to('frontend/public').as_posix(): ROOT / p for p in public}
    seen = set()
    for file in web.rglob('*'):
        if not file.is_file():
            continue
        relative = file.relative_to(web).as_posix()
        seen.add(relative)
        if relative in expected:
            if file.read_bytes() != expected[relative].read_bytes():
                raise ValueError('An approved public asset was changed during packaging.')
        elif relative == 'index.html':
            pass
        elif file.parent == web / 'assets' and file.suffix in {'.js', '.css'}:
            pass
        else:
            raise ValueError('Unexpected file in built frontend: ' + relative)
    if not set(expected).union({'index.html'}).issubset(seen):
        raise ValueError('The built frontend is missing approved assets.')
    if not list((web / 'assets').glob('*.js')):
        raise ValueError('The built frontend is missing JavaScript.')
    return len(seen)


def verify_bundle(bundle):
    if not (bundle / 'BMCPolinexo.exe').is_file():
        raise ValueError('Packaged executable is missing.')
    count = verify_web(bundle / '_internal/web')
    assets = [Path(line) for line in Path(__file__).with_name('backend-assets.txt').read_text(encoding='utf-8').splitlines() if line]
    expected = {p.relative_to('backend/app/assets').as_posix(): ROOT / p for p in assets}
    bundled_assets = bundle / '_internal/app/assets'
    actual = {p.relative_to(bundled_assets).as_posix(): p for p in bundled_assets.rglob('*') if p.is_file()}
    if set(actual) != set(expected):
        raise ValueError('Bundled Excel export assets do not match the approved manifest.')
    for relative, source in expected.items():
        if actual[relative].read_bytes() != source.read_bytes():
            raise ValueError('An approved Excel export asset changed during packaging: ' + relative)
    entries = []
    for file in sorted(bundle.rglob('*')):
        if not file.is_file():
            continue
        relative = file.relative_to(bundle)
        if file.suffix.lower() in FORBIDDEN or any(part.lower() in {'tests', 'test-results', '.git', 'node_modules'} for part in relative.parts):
            raise ValueError('Forbidden artifact in bundle: ' + str(relative))
        if 'prompt' in file.name.lower() or 'screenshot' in file.name.lower():
            raise ValueError('Forbidden artifact in bundle: ' + str(relative))
        entries.append({'path': relative.as_posix(), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    # Build evidence lives beside the bundle, never inside the installed app.
    bundle.with_name('bundle-manifest.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
    print(f'PASS: {len(entries)} bundle files audited, including {count} approved web files and {len(expected)} Excel export assets.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--web', type=Path)
    group.add_argument('--bundle', type=Path)
    args = parser.parse_args()
    if args.web:
        print(f'PASS: {verify_web(args.web)} frontend files audited.')
    else:
        verify_bundle(args.bundle)
