"""Build a self-contained, ad-hoc signed Apple-silicon DMG on macOS 15+."""
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import subprocess
import sys

from verify_bundle import verify_bundle, verify_web

ROOT = Path(__file__).resolve().parents[2]
VERSION = '1.2.2'
WORK = ROOT / 'build/macos'
DIST = ROOT / 'dist/macos'
RELEASE = ROOT / f'dist/releases/{VERSION}-macos-arm64'


def run(*args, cwd=ROOT):
    subprocess.run([str(a) for a in args], cwd=cwd, check=True)


def empty_output(path):
    # Delete only these explicitly owned output directories, never their parents.
    if path not in (WORK, DIST, RELEASE) or path.is_symlink():
        raise ValueError('Refusing to replace an unexpected output path.')
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('Output path is outside the repository.')
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def main():
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        raise SystemExit('Build on an Apple-silicon Mac; cross-compiling is unsupported.')
    if int(platform.mac_ver()[0].split('.')[0]) < 15:
        raise SystemExit('macOS 15 or newer is required.')
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Use Python 3.12 for the build.')
    for path in (WORK, DIST, RELEASE):
        empty_output(path)
    run(sys.executable, ROOT / 'packaging/macos/audit_excel.py')
    venv = ROOT / '.build-venv-macos'
    if not venv.exists():
        run(sys.executable, '-m', 'venv', venv)
    python = venv / 'bin/python'
    run(python, '-m', 'pip', 'install', '-r', ROOT / 'packaging/macos/requirements-build.txt')
    run(python, '-m', 'pip', 'check')
    run('npm', 'ci', cwd=ROOT / 'frontend')
    run('npm', 'run', 'build', cwd=ROOT / 'frontend')
    verify_web(ROOT / 'frontend/dist')
    run(python, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--workpath', WORK / 'pyinstaller', '--distpath', DIST / 'frozen',
        ROOT / 'packaging/macos/BMCPolinexoServer.spec')
    backend = DIST / 'frozen/BMCPolinexoServer'
    verify_bundle(backend)

    app = DIST / 'BMCPolinexo.app'
    contents = app / 'Contents'
    macos = contents / 'MacOS'
    resources = contents / 'Resources'
    macos.mkdir(parents=True)
    resources.mkdir()
    shutil.copytree(backend, resources / 'backend', symlinks=True)
    info = {
        'CFBundleName': 'BMCPolinexo', 'CFBundleDisplayName': 'BMCPolinexo',
        'CFBundleIdentifier': 'il.co.bmc.polinexo', 'CFBundleExecutable': 'BMCPolinexo',
        'CFBundlePackageType': 'APPL', 'CFBundleShortVersionString': VERSION,
        'CFBundleVersion': VERSION, 'LSMinimumSystemVersion': '15.0',
        'LSArchitecturePriority': ['arm64'], 'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication', 'NSQuitAlwaysKeepsWindows': False,
        'NSHumanReadableCopyright': 'BMC — local insurance portfolio review',
    }
    (contents / 'Info.plist').write_bytes(plistlib.dumps(info))
    run('xcrun', 'swiftc', '-O', '-target', 'arm64-apple-macos15.0',
        '-framework', 'AppKit', ROOT / 'desktop/macos/Launcher.swift',
        '-o', macos / 'BMCPolinexo')
    # PyInstaller signs nested native libraries. Sign the completed outer bundle
    # locally as well; this is deliberately not Developer ID/notarization.
    run('codesign', '--force', '--deep', '--sign', '-', app)
    run('codesign', '--verify', '--deep', '--strict', '--verbose=2', app)
    for executable in (macos / 'BMCPolinexo', resources / 'backend/BMCPolinexoServer'):
        arch = subprocess.check_output(['lipo', '-archs', str(executable)], text=True).strip()
        if arch != 'arm64':
            raise ValueError('Expected a native arm64 executable.')

    staging = WORK / 'dmg'
    staging.mkdir()
    run('ditto', app, staging / app.name)
    os.symlink('/Applications', staging / 'Applications')
    notes = (
        f'BMCPolinexo {VERSION} — Apple silicon (M1/M2/M3/M4 or newer), macOS 15+\n\n'
        'Open the DMG and drag BMCPolinexo.app onto Applications. Eject the disk,\n'
        'then open BMCPolinexo from Applications. No Docker/Python/Node required.\n'
        'If macOS blocks this trusted pilot build, attempt opening it once, then\n'
        'System Settings > Privacy & Security > Open Anyway, and confirm Open.\n'
        'This build is ad-hoc signed, not Apple-notarized. Do not disable macOS security.\n\n'
        'Keep the launcher open while working. Closing it quits the local server\n'
        'and clears open browser portfolios. Refresh also clears the workspace.\n'
        'Excel downloads remain in your Downloads folder. Customer data is not saved by the app.\n\n'
        'Upgrade: quit BMCPolinexo, drag the new app to Applications and choose Replace.\n'
        'Uninstall: quit, then move BMCPolinexo.app from Applications to Trash.\n'
        'You can send the DMG as a WhatsApp document. Download it on the Mac first.\n'
    )
    (staging / 'INSTALL.txt').write_text(notes, encoding='utf-8')
    (RELEASE / 'INSTALL.txt').write_text(notes, encoding='utf-8')
    dmg = RELEASE / f'BMCPolinexo-{VERSION}-macos-arm64.dmg'
    run('hdiutil', 'create', '-volname', 'BMCPolinexo', '-srcfolder', staging,
        '-format', 'UDZO', '-ov', dmg)
    checksum = hashlib.sha256(dmg.read_bytes()).hexdigest()
    (RELEASE / 'SHA256SUMS.txt').write_text(f'{checksum}  {dmg.name}\n', encoding='ascii')
    manifest = {
        'version': VERSION, 'platform': 'macOS', 'architecture': 'arm64',
        'minimum_os': '15.0', 'signing': 'ad-hoc', 'notarized': False,
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'sha256': checksum, 'bytes': dmg.stat().st_size,
        'builder_os': platform.mac_ver()[0], 'python': platform.python_version(),
    }
    (RELEASE / 'build-info.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Built {dmg.name}: {checksum}', flush=True)


if __name__ == '__main__':
    main()
