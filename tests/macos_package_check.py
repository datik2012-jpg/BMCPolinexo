"""Exercise the actual DMG on an Apple-silicon Mac, using synthetic data only."""
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright, expect
from browser_check import fixture_module
from customer_helpers import fill_customer

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / 'dist/releases/1.2.2-macos-arm64'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def wait_for(fn, message, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = fn()
        if result:
            return result
        time.sleep(0.1)
    raise AssertionError(message)


def instance(url):
    try:
        with OPENER.open(url + '/api/instance', timeout=0.5) as response:
            return json.load(response)
    except (OSError, ValueError):
        return None


def find_backend(parent):
    children = subprocess.run(['pgrep', '-P', str(parent)], capture_output=True, text=True)
    for pid in children.stdout.split():
        result = subprocess.run(['/usr/sbin/lsof', '-Pan', '-p', pid, '-iTCP', '-sTCP:LISTEN'],
                                capture_output=True, text=True)
        for line in result.stdout.splitlines()[1:]:
            match = re.search(r'127\.0\.0\.1:(\d+)\s+\(LISTEN\)', line)
            if match:
                url = 'http://127.0.0.1:' + match[1]
                record = instance(url)
                if record:
                    assert record['desktop_mode'] is True
                    return int(pid), url, record['instance_id']
    return None


def files_snapshot(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def launch(app):
    environment = os.environ.copy()
    environment['BMC_TEST_NO_BROWSER'] = '1'
    environment['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'
    environment['PYTHONHOME'] = '/not-a-python-installation'
    environment['PYTHONPATH'] = '/not-a-python-installation'
    process = subprocess.Popen([str(app / 'Contents/MacOS/BMCPolinexo')], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return process


def import_sample(page, url):
    page.goto(url)
    expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    fill_customer(page.get_by_role('region', name='פרטי לקוח', exact=True).first)
    page.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
        'name': 'synthetic.xlsx',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': fixture_module.fixture(),
    })
    expect(page.locator('.policy:visible')).to_have_count(8)


def assert_stopped(process, backend, url, page):
    process.wait(timeout=15)
    wait_for(lambda: instance(url) is None, 'Backend still responds after launcher exit', 12)
    def ended():
        state = subprocess.run(['ps', '-p', str(backend), '-o', 'stat='], capture_output=True, text=True).stdout.strip()
        return not state or state.startswith('Z')
    wait_for(ended, 'Backend process outlived its launcher', 12)
    expect(page.locator('.policy:visible')).to_have_count(0, timeout=12000)
    expect(page.get_by_role('status')).to_contain_text('הנתונים נוקו')
    expect(page.get_by_label('תעודת זהות', exact=True)).to_have_value('')


def verify(app):
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    before = files_snapshot(app)
    process = launch(app)
    try:
        backend, url, identity = wait_for(lambda: find_backend(process.pid), 'Native launcher did not start its packaged backend')
        second = launch(app)
        assert second.wait(timeout=10) == 0, 'Second launch did not activate the existing instance'
        assert instance(url)['instance_id'] == identity
        child_pids = subprocess.check_output(['pgrep', '-P', str(process.pid)], text=True).split()
        assert child_pids == [str(backend)], 'More than one backend was started'
        environment = dict(os.environ, BMC_URL=url, BMC_TEST_DESKTOP='1')
        for name in ['browser', 'family', 'shared', 'proposal', 'category_filter', 'insurer_logos', 'export']:
            subprocess.run([sys.executable, str(ROOT / f'tests/{name}_check.py')],
                           cwd=ROOT, env=environment, check=True, timeout=180)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            import_sample(page, url)
            process.send_signal(signal.SIGTERM)
            assert_stopped(process, backend, url, page)
            process = launch(app)
            backend, url, new_identity = wait_for(lambda: find_backend(process.pid), 'Restart failed')
            assert new_identity != identity
            page.goto(url)
            expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
            expect(page.locator('.policy:visible')).to_have_count(0)
            expect(page.get_by_label('תעודת זהות', exact=True)).to_have_value('')
            import_sample(page, url)
            process.kill()
            assert_stopped(process, backend, url, page)
            browser.close()
        assert files_snapshot(app) == before, 'Installed app changed during use'
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=12)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    print('PASS: native ARM launcher, single instance, seven packaged browser suites, normal quit, restart, crash cleanup, unchanged app files', flush=True)


def main():
    assert sys.platform == 'darwin' and platform.machine() == 'arm64'
    dmg = RELEASE / 'BMCPolinexo-1.2.2-macos-arm64.dmg'
    expected = (RELEASE / 'SHA256SUMS.txt').read_text().split()[0]
    assert hashlib.sha256(dmg.read_bytes()).hexdigest() == expected
    attached = plistlib.loads(subprocess.check_output(['hdiutil', 'attach', '-readonly', '-nobrowse', '-plist', str(dmg)]))
    mount = next(Path(p['mount-point']) for p in attached['system-entities'] if 'mount-point' in p)
    try:
        with tempfile.TemporaryDirectory(prefix='BMC Mac בדיקה ') as directory:
            destination = Path(directory) / 'Applications בדיקה'
            destination.mkdir()
            marker = destination / 'unrelated.txt'
            marker.write_text('synthetic installation boundary marker')
            app = destination / 'BMCPolinexo.app'
            subprocess.run(['ditto', str(mount / app.name), str(app)], check=True)
            subprocess.run(['hdiutil', 'detach', str(mount)], check=True)
            mount = None
            verify(app)
            import shutil
            shutil.rmtree(app)
            subprocess.run(['ditto', str(ROOT / 'dist/macos/BMCPolinexo.app'), str(app)], check=True)
            subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
            assert marker.read_text() == 'synthetic installation boundary marker'
            shutil.rmtree(app)
            assert marker.exists()
    finally:
        if mount:
            subprocess.run(['hdiutil', 'detach', str(mount)], check=True)
    (RELEASE / 'TEST-RESULTS.txt').write_text(
        'PASS on macOS ' + platform.mac_ver()[0] + ' arm64\n'
        'DMG checksum, mount, copy to Hebrew/space path, unmount, ad-hoc signature.\n'
        'Packaged startup without developer PATH/Python environment; single instance.\n'
        'Seven synthetic browser suites including import, export and merged summary.\n'
        'Normal shutdown, fresh restart, launcher crash, browser clearing, no orphan API.\n'
        'No installed-file changes; replacement and removal preserve unrelated files.\n'
        'Physical M4, Safari and first-launch Gatekeeper approval require user acceptance.\n', encoding='utf-8')
    print('PASS: DMG installation, replacement and removal', flush=True)


if __name__ == '__main__':
    main()
