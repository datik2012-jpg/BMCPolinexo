"""Acceptance checks against the real windowed executable, using synthetic data.

Run: .venv/Scripts/python tests/windows_package_check.py --exe <BMCPolinexo.exe>
The executable opens the default browser as it does for employees. The harness
uses its own Playwright browser for assertions and closes only its own launcher.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright, expect
from customer_helpers import fill_customer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
spec = importlib.util.spec_from_file_location('synthetic_fixture', ROOT / 'backend/tests/test_import.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
user32 = ctypes.WinDLL('user32', use_last_error=True)
callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]


def launch(exe):
    env = dict(os.environ)
    for name in ('PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV'):
        env.pop(name, None)
    env['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
    startup = subprocess.STARTUPINFO()
    startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return subprocess.Popen([str(exe)], cwd=exe.parent, env=env, startupinfo=startup)


def address(process):
    deadline = time.monotonic() + 40
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    while time.monotonic() < deadline:
        assert process.poll() is None, 'Packaged launcher exited before readiness'
        output = subprocess.check_output(['netstat.exe', '-ano', '-p', 'tcp'], creationflags=subprocess.CREATE_NO_WINDOW).decode()
        for line in output.splitlines():
            fields = line.split()
            if len(fields) == 5 and fields[-1] == str(process.pid) and fields[2] == '0.0.0.0:0':
                assert fields[1].startswith('127.0.0.1:'), 'Server exposed beyond localhost'
                url = 'http://' + fields[1]
                try:
                    with opener.open(url + '/api/instance', timeout=1) as response:
                        info = json.load(response)
                    assert info['desktop_mode'] is True
                    return url, info['instance_id']
                except OSError:
                    pass
        time.sleep(0.15)
    raise AssertionError('Packaged server did not become ready')


def close_launcher(process):
    found = []

    @callback_type
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == process.pid:
            title = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title, len(title))
            if title.value == 'BMCPolinexo':
                found.append(hwnd)
        return True

    user32.EnumWindows(visit, 0)
    assert found, 'Launcher window not found'
    user32.PostMessageW(found[0], 0x0010, 0, 0)  # WM_CLOSE exercises normal shutdown.
    assert process.wait(timeout=15) == 0


def file_state(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exe', type=Path, required=True)
    parser.add_argument('--skip-browser-suite', action='store_true')
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    before = file_state(exe.parent)
    process = launch(exe)
    try:
        url, identity = address(process)
        print('PASS: frozen app ready on localhost with development tools removed from PATH', flush=True)
        second = launch(exe)
        assert second.wait(timeout=15) == 0
        assert address(process) == (url, identity)
        print('PASS: repeated shortcut launch reuses the running instance', flush=True)
        if not args.skip_browser_suite:
            env = dict(os.environ, BMC_URL=url, BMC_TEST_DESKTOP='1')
            env.pop('BMC_TEST_DOCKER_RESTART', None)
            for name in ['browser', 'family', 'shared', 'export', 'category_filter', 'insurer_logos']:
                subprocess.run([sys.executable, str(ROOT / 'tests' / (name + '_check.py'))], env=env, check=True, timeout=240)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context()
            external_requests = []

            def local_only(route):
                if route.request.url.startswith(url + '/'):
                    route.continue_()
                else:
                    external_requests.append(route.request.url)
                    route.abort()

            context.route('**/*', local_only)
            page = context.new_page()
            page.goto(url)
            expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
            fill_customer(page.locator('.customer-card').first)
            page.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
                'name': 'synthetic.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'buffer': fixture_module.fixture(),
            })
            expect(page.locator('.policy')).to_have_count(8)
            assert not external_requests, 'The application requested external resources'
            close_launcher(process)
            expect(page.locator('.policy')).to_have_count(0, timeout=15000)
            expect(page.get_by_label('שם פרטי', exact=True)).to_have_value('')
            port = int(url.rsplit(':', 1)[1])
            with socket.socket() as probe:
                assert probe.connect_ex(('127.0.0.1', port)) != 0
            process = launch(exe)
            new_url, new_identity = address(process)
            assert identity != new_identity
            url = new_url
            page.goto(new_url)
            expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
            expect(page.locator('.policy')).to_have_count(0)
            assert page.evaluate('localStorage.length + sessionStorage.length') == 0
            fill_customer(page.locator('.customer-card').first)
            process.kill()
            process.wait(timeout=10)
            expect(page.get_by_label('שם פרטי', exact=True)).to_have_value('', timeout=15000)
            browser.close()
        assert file_state(exe.parent) == before, 'Application directory changed at runtime'
        print('PASS: real close/restart/crash clears data; port closes; bundle files remain unchanged', flush=True)
    finally:
        if process.poll() is None:
            close_launcher(process)


if __name__ == '__main__':
    main()
