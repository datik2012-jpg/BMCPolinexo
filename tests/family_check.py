"""Synthetic browser acceptance for separate family portfolios and lifecycle."""
from browser_check import fixture_module, ROOT
from customer_helpers import fill_customer
from playwright.sync_api import sync_playwright, expect

def upload(card, identity, premium=10):
    card.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
        'name': 'synthetic.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': fixture_module.fixture([fixture_module.row(insured_id=identity, premium=premium)])})

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    failures = []
    page.on('pageerror', lambda error: failures.append(str(error)))
    page.goto('http://127.0.0.1:8080')
    cards = page.locator('.customer-card')
    sections = page.locator('.customer-section')
    expect(cards).to_have_count(1)
    expect(cards.first.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    expect(cards.first.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True)).to_be_disabled()
    fill_customer(cards.first)
    upload(cards.first, 999999999)
    expect(page.locator('.policy')).to_have_count(1)
    page.locator('.policy summary').click()
    page.get_by_role('button', name='עריכה', exact=True).click()
    page.get_by_role('dialog').get_by_label('פרמיה', exact=True).fill('15')
    page.get_by_role('button', name='שמירת תיקונים', exact=True).click()
    expect(page.locator('.totals').first).to_contain_text('15.00')
    page.get_by_role('button', name='+ הוסף לקוח נוסף', exact=True).click()
    expect(cards).to_have_count(2)
    expect(sections.first.locator('.policy')).to_have_count(1)
    expect(sections.first.locator('.policy')).to_have_attribute('open', '')
    expect(sections.nth(1).locator('.policy')).to_have_count(0)
    assert sections.nth(1).bounding_box()['y'] > sections.first.locator('.policy').bounding_box()['y']
    fill_customer(cards.nth(1), '999999999')
    expect(cards.nth(1).get_by_label('העלאת קובץ Excel הר ביטוח', exact=True)).to_be_disabled()
    cards.nth(1).get_by_label('תעודת זהות', exact=True).fill('888888888')
    upload(cards.nth(1), 999999999)
    expect(page.get_by_role('alert')).to_contain_text('אינה תואמת')
    expect(sections.nth(1).locator('.policy')).to_have_count(0)
    upload(cards.nth(1), 888888888, 20)
    expect(sections.nth(1).locator('.totals').first).to_contain_text('20.00')
    expect(page.locator('.totals').first).to_contain_text('15.00')
    upload(cards.nth(1), 888888888, 30)
    expect(sections.nth(1).locator('.totals').first).to_contain_text('30.00')
    upload(cards.nth(1), 999999999, 99)
    expect(page.get_by_role('alert')).to_contain_text('אינה תואמת')
    expect(sections.nth(1).locator('.totals').first).to_contain_text('30.00')
    expect(sections.first.locator('.totals').first).to_contain_text('15.00')
    sections.first.get_by_role('button', name='השוואה למקור', exact=True).click()
    expect(sections.first.locator('.source-row')).to_have_count(1)
    expect(sections.nth(1).locator('.policy')).to_have_count(1)
    sections.first.get_by_role('button', name='חזרה לפוליסות', exact=True).click()
    for width in [1440, 768, 390, 320]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert cards.evaluate_all('(cards) => cards.every(c => c.scrollWidth <= c.clientWidth + 1)'), f'Customer overflow at {width}'
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.screenshot(path=str(ROOT / 'test-results/family-customers.png'), full_page=True)
    assert page.evaluate('localStorage.length + sessionStorage.length') == 0
    page.route('**/api/instance', lambda route: route.fulfill(json={'instance_id': 'family-restart'}))
    expect(cards).to_have_count(1, timeout=10000)
    expect(cards.first.get_by_label('שם פרטי', exact=True)).to_have_value('')
    expect(page.locator('.policy')).to_have_count(0)
    page.unroute('**/api/instance')
    page.reload()
    expect(cards.first.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    fill_customer(cards.first)
    upload(cards.first, 999999999)
    expect(page.locator('.policy')).to_have_count(1)
    page.reload()
    expect(cards).to_have_count(1)
    expect(cards.first.get_by_label('שם פרטי', exact=True)).to_have_value('')
    expect(page.locator('.policy')).to_have_count(0)
    assert not failures, failures
    browser.close()
print('PASS: required fields, separate family imports/edits/replacement, duplicate and mismatched IDs, responsive forms, refresh and restart clearing.')
