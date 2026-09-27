"""Install/upgrade/uninstall in an isolated Hebrew path under the current user.

Refuses to run if BMCPolinexo is already installed. Needs two installer versions.
Never run against an employee installation or real customer work.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import winreg

from windows_package_check import address, close_launcher, launch, ROOT

KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{CB22149E-7991-4D17-BA3B-A28AD790BA03}_is1'


def installed_version():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as key:
            return winreg.QueryValueEx(key, 'DisplayVersion')[0]
    except FileNotFoundError:
        return None


def execute(path, *args):
    startup = subprocess.STARTUPINFO()
    startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return subprocess.run([str(path), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', *args],
                          startupinfo=startup, timeout=120).returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--installer', type=Path, required=True)
    parser.add_argument('--version', default='1.1.0')
    args = parser.parse_args()
    assert not installed_version(), 'Existing installation detected: use a separate test user'
    assert not ctypes.windll.shell32.IsUserAnAdmin(), 'Run this test without administrator elevation'
    # Resolve actual shell folders, including redirected Desktop/Start Menu.
    def shell_folder(identifier):
        buffer = ctypes.create_unicode_buffer(32768)
        assert ctypes.windll.shell32.SHGetFolderPathW(None, identifier, None, 0, buffer) == 0
        return Path(buffer.value)
    shortcuts = [shell_folder(0x10) / 'BMCPolinexo.lnk', shell_folder(0x02) / 'BMCPolinexo/BMCPolinexo.lnk']
    assert not any(p.exists() for p in shortcuts), 'Existing shortcut detected: use a separate test user'
    directory = ROOT / 'test-results' / ('התקנת בדיקה ' + uuid.uuid4().hex[:8])
    directory.parent.mkdir(exist_ok=True)
    baseline, installer = args.baseline.resolve(strict=True), args.installer.resolve(strict=True)
    process = None
    installed = False
    try:
        assert execute(baseline, '/LANG=hebrew', '/DIR=' + str(directory)) == 0
        installed = True
        assert installed_version() and installed_version() != args.version
        assert all(p.is_file() for p in shortcuts)
        process = launch(directory / 'BMCPolinexo.exe')
        address(process)
        # Silent setup/uninstall must refuse instead of forcibly stopping work.
        assert execute(installer, '/DIR=' + str(directory)) != 0
        assert execute(directory / 'unins000.exe') != 0
        assert process.poll() is None
        close_launcher(process)
        process = None
        print('PASS: non-admin Hebrew-path install, shortcuts, running-app upgrade/uninstall guards', flush=True)
        # Verify runtime replacement removes obsolete files on upgrade.
        stale = directory / '_internal/obsolete-test-marker.txt'
        stale.write_text('synthetic obsolete runtime marker', encoding='utf-8')
        assert execute(installer, '/LANG=hebrew', '/DIR=' + str(directory)) == 0
        assert installed_version() == args.version
        assert not stale.exists()
        manifest = json.loads((ROOT / 'dist/windows/bundle-manifest.json').read_text(encoding='utf-8'))
        import hashlib
        for entry in manifest:
            assert hashlib.sha256((directory / entry['path']).read_bytes()).hexdigest() == entry['sha256']
        subprocess.run([sys.executable, str(ROOT / 'tests/windows_package_check.py'), '--exe', str(directory / 'BMCPolinexo.exe')], check=True, timeout=600)
        print('PASS: upgrade to ' + args.version + ', installed files match audited bundle', flush=True)
        # An unrelated user file outside the application folder must survive.
        marker = directory.with_name(directory.name + '-unrelated.txt')
        marker.write_text('synthetic external file', encoding='utf-8')
        assert execute(directory / 'unins000.exe') == 0
        installed = False
        assert installed_version() is None
        assert not any(p.exists() for p in shortcuts)
        assert not (directory / 'BMCPolinexo.exe').exists()
        assert not (directory / '_internal').exists()
        assert marker.read_text(encoding='utf-8') == 'synthetic external file'
        marker.unlink()
        print('PASS: uninstall removes application, registry entry and shortcuts; unrelated file retained', flush=True)
    finally:
        if process is not None and process.poll() is None:
            close_launcher(process)
        if installed and (directory / 'unins000.exe').is_file():
            execute(directory / 'unins000.exe')


if __name__ == '__main__':
    main()
