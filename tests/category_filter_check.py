"""Verify category selection with synthetic data in the running local app."""
from browser_check import fixture_module
from customer_helpers import fill_customer
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.goto('http://127.0.0.1:8080')
    expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    fill_customer(page.locator('.customer-card'))
    categories = ['ביטוח רכב', 'ביטוח סיעודי', 'ביטוח בריאות', 'ביטוח חיים']
    rows = [fixture_module.row(category=category, policy_number=str(800000 + i), premium=10)
            for i, category in enumerate(categories)]
    page.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
        'name': 'synthetic.xlsx',
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': fixture_module.fixture(rows)})
    expect(page.locator('.policy')).to_have_count(2)
    page.locator('.category-filter summary').click()
    options = page.get_by_role('group', name='בחירת ענפי ביטוח')
    for category in categories[:2]:
        expect(options.get_by_role('checkbox', name=category, exact=True)).not_to_be_checked()
    for category in categories[2:]:
        expect(options.get_by_role('checkbox', name=category, exact=True)).to_be_checked()
    options.get_by_role('checkbox', name='ביטוח רכב', exact=True).check()
    expect(page.locator('.policy')).to_have_count(3)
    for category in categories:
        options.get_by_role('checkbox', name=category, exact=True).uncheck()
    expect(page.locator('.policy')).to_have_count(0)
    expect(page.locator('.empty')).to_be_visible()
    page.locator('.category-filter summary').press('Escape')
    page.get_by_role('button', name='ניקוי סינון', exact=True).click()
    expect(page.locator('.policy')).to_have_count(4)
    page.locator('.category-filter summary').click()
    options.get_by_role('checkbox', name='ביטוח רכב', exact=True).uncheck()
    page.get_by_role('button', name='השוואה למקור', exact=True).click()
    expect(page.locator('.source-row')).to_have_count(3)
    for width in [1440, 390, 320]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), f'Overflow at {width}'
    browser.close()
print('Category checkbox defaults, toggles, clear, source view and responsive layout passed.')
