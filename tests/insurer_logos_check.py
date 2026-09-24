"""Check the insurer catalog against the running UI with synthetic data only."""
import re
from browser_check import ROOT, fixture_module
from playwright.sync_api import sync_playwright, expect
from customer_helpers import fill_customer

brands = re.findall(r'brand\("([^"]+)", "([^"]+)", "([^"]+)"', (ROOT / 'frontend/src/insurers.ts').read_text(encoding='utf-8'))
rows = [fixture_module.row(insurer=name, policy_number=f'LOGO-{key}') for key, name, _ in brands]
rows.append(fixture_module.row(insurer='מבטח חדש לבדיקה', policy_number='UNKNOWN'))
payload = fixture_module.fixture(rows)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8080')
    upload = page.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True)
    expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    fill_customer(page.locator('.customer-card').first)
    upload.set_input_files({'name': 'synthetic-logos.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer': payload})
    expect(page.locator('.policy')).to_have_count(len(rows))
    expect(page.locator('.insurer-logo img')).to_have_count(len(brands))
    page.wait_for_function('Array.from(document.querySelectorAll(".insurer-logo img")).every(i => i.complete && i.naturalWidth > 0)')
    for width in [1440, 768, 390, 320]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.locator('.policy').evaluate_all('(cards) => cards.every(c => c.scrollWidth <= c.clientWidth + 1)'), f'Card overflow at {width}'
        assert page.locator('.insurer-logo').evaluate_all('(logos) => logos.every(l => l.getBoundingClientRect().left >= l.closest("summary").querySelector(".policy-title").getBoundingClientRect().right - 1)'), 'Logo must be right of title'
    page.set_viewport_size({'width': 1440, 'height': 1000})
    first = page.locator('.policy').first
    first.scroll_into_view_if_needed()
    page.screenshot(path=str(ROOT / 'test-results/insurer-policy-logos.png'))
    first.locator('summary').click()
    expect(first.locator('tbody tr')).to_have_count(1)
    page.locator('.policy').filter(has_text='LOGO-bss').screenshot(path=str(ROOT / 'test-results/insurer-bss.png'))
    assert not errors, errors
    page.set_content('<html><body style="font-family:Arial;display:grid;grid-template-columns:repeat(5,1fr);gap:20px;background:#eee">' + ''.join(f'<div style="background:white;padding:20px;text-align:center"><img src="http://127.0.0.1:8080/insurers/{file}" style="width:130px;height:70px;object-fit:contain"><p>{name}</p></div>' for _,name,file in brands) + '</body></html>')
    page.wait_for_function('Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)')
    page.screenshot(path=str(ROOT / 'test-results/insurer-catalog.png'), full_page=True)
    browser.close()
print(f'PASS: {len(brands)} logos load; unknown insurer remains visible; RTL placement and four card widths verified.')
