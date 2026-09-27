# Build from an isolated environment; never collect the repository as data.
from pathlib import Path
from importlib.metadata import distributions
import sys

root = Path(SPECPATH).parents[1]
web = root / 'frontend' / 'dist'
allowed = {'.html', '.js', '.css', '.svg', '.png', '.jpg'}
datas = []
for file in sorted(web.rglob('*')):
    if file.is_file():
        if file.suffix.lower() not in allowed:
            raise ValueError(f'Unexpected frontend artifact: {file.name}')
        datas.append((str(file), str(Path('web') / file.relative_to(web).parent)))
if not (web / 'index.html').is_file():
    raise ValueError('Build the frontend before packaging.')

# Retain redistribution notices without collecting unrelated project files.
datas.append((str(Path(sys.base_prefix) / 'LICENSE.txt'), 'licenses/python'))
for package in ['react', 'react-dom', 'scheduler', 'decimal.js']:
    directory = root / 'frontend/node_modules' / package
    license_file = next(p for p in directory.iterdir() if p.name.lower().startswith('licen'))
    datas.append((str(license_file), 'licenses/' + package))
for distribution in distributions():
    for file in distribution.files or []:
        if file.name.lower().startswith(('license', 'copying')) and '.dist-info' in str(file):
            datas.append((str(distribution.locate_file(file)), 'licenses/' + distribution.metadata['Name']))

a = Analysis(
    [str(root / 'desktop' / 'launcher.py')],
    pathex=[str(root / 'backend'), str(root / 'desktop')],
    binaries=[], datas=datas,
    hiddenimports=['uvicorn.logging', 'uvicorn.loops.asyncio', 'uvicorn.protocols.http.h11_impl'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pytest', 'playwright', 'pip', 'setuptools', 'unittest'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='BMCPolinexo',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=True)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='BMCPolinexo')
