"""End-to-end checks against a running pilot, using an in-memory synthetic XLSX.

Run with a Python environment containing backend test requirements and Playwright.
No real workbook, browser trace, or uploaded file is saved.
"""
import importlib.util
import os
import subprocess
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright, expect
from customer_helpers import fill_customer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
spec = importlib.util.spec_from_file_location('synthetic_fixture', ROOT / 'backend/tests/test_import.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)


def run():
    payload = fixture_module.fixture()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        failures = []
        page.on('pageerror', lambda error: failures.append(str(error)))
        page.goto(os.environ.get('BMC_URL', 'http://127.0.0.1:8080'))
        upload = page.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True)
        expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)

        def import_sample():
            fill_customer(page.locator('.customer-card').first)
            upload.set_input_files({'name': 'synthetic.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer': payload})
            expect(page.locator('.policy')).to_have_count(8)
            expect(page.locator('.totals').first).to_contain_text('763.32')
            expect(page.locator('.totals').first).to_contain_text('5,642.00')

        import_sample()
        assert page.locator('html').get_attribute('dir') == 'rtl'
        expect(page.locator('.policy').nth(1).locator('summary bdi').filter(has_text='01/01/2025 - 31/12/2030')).to_have_attribute('dir', 'ltr')
        policy = page.locator('.policy').first
        policy.locator('summary').click()
        expect(policy.locator('tbody tr')).to_have_count(6)
        policy.get_by_role('button', name='עריכה', exact=True).first.click()
        dialog = page.get_by_role('dialog')
        dialog.get_by_label('פרמיה', exact=True).fill('1600')
        dialog.get_by_role('button', name='שמירת תיקונים').click()
        expect(page.locator('.totals').first).to_contain_text('5,655.00')
        policy.get_by_role('button', name='החרגה', exact=True).first.click()
        expect(page.locator('.totals').first).to_contain_text('4,055.00')
        policy.get_by_role('button', name='שחזור', exact=True).first.click()
        expect(page.locator('.totals').first).to_contain_text('5,655.00')
        page.get_by_role('button', name='השוואה למקור', exact=True).click()
        expect(page.locator('.delta')).to_contain_text('13.00')
        expect(page.locator('.source-row')).to_have_count(20)
        page.get_by_role('button', name='חזרה לפוליסות', exact=True).click()
        page.get_by_label('תדירות תשלום', exact=True).select_option('annual')
        expect(page.locator('.policy')).to_have_count(1)
        page.get_by_role('button', name='ניקוי סינון').click()
        expect(page.locator('.policy')).to_have_count(8)
        first = page.locator('.policy').first
        if first.get_attribute('open') is None:
            first.locator('summary').click()
        first.get_by_role('button', name='עריכה', exact=True).first.click()
        dialog.get_by_label('מספר פוליסה', exact=True).fill('SYNTHETIC-NEW-GROUP')
        dialog.get_by_label('פרמיה', exact=True).fill('invalid')
        dialog.get_by_role('button', name='שמירת תיקונים').click()
        expect(page.locator('.policy')).to_have_count(9)
        expect(page.locator('.totals').first).to_contain_text('חלקי')
        changed = page.locator('.policy').filter(has_text='SYNTHETIC-NEW-GROUP')
        if changed.get_attribute('open') is None:
            changed.locator('summary').click()
        changed.get_by_role('button', name='עריכה', exact=True).click()
        dialog.get_by_role('button', name='איפוס לערכי המקור').click()
        dialog.get_by_role('button', name='שמירת תיקונים').click()
        expect(page.locator('.policy')).to_have_count(8)
        expect(page.locator('.totals').first).to_contain_text('5,642.00')
        assert page.evaluate('localStorage.length + sessionStorage.length') == 0
        assert page.evaluate('navigator.serviceWorker.getRegistrations().then(x => x.length)') == 0
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile document overflows'
        page.set_viewport_size({'width': 1440, 'height': 1000})
        output = ROOT / 'test-results'
        output.mkdir(exist_ok=True)
        page.screenshot(path=str(output / 'portfolio.png'), full_page=True)
        page.reload()
        expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
        expect(page.locator('.policy')).to_have_count(0)
        import_sample()
        page.route('**/api/instance', lambda route: route.abort())
        expect(upload).to_be_disabled(timeout=10000)
        page.unroute('**/api/instance')
        expect(upload).to_be_enabled(timeout=10000)
        expect(page.locator('.policy')).to_have_count(8)
        page.route('**/api/instance', lambda route: route.fulfill(json={'instance_id': 'test-new-server-instance'}))
        expect(page.locator('.policy')).to_have_count(0, timeout=10000)
        expect(page.get_by_role('status')).to_contain_text('השרת הופעל מחדש')
        if os.environ.get('BMC_TEST_DOCKER_RESTART') == '1':
            page.unroute('**/api/instance')
            page.reload()
            expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
            import_sample()
            subprocess.run(['docker', 'compose', 'restart', 'api'], cwd=ROOT, check=True, timeout=60)
            expect(page.locator('.policy')).to_have_count(0, timeout=30000)
            expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=30000)
            expect(page.get_by_role('status')).to_contain_text('השרת הופעל מחדש')
            print('PASS: actual Docker API restart clears the open portfolio')
        assert not failures, failures
        browser.close()
    print('PASS: real import, grouping, edit, exclude/restore, comparison, filters, RTL/mobile, storage, refresh, offline lock, restart detection')


if __name__ == '__main__':
    run()
