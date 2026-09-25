"""Shared-view acceptance using synthetic in-memory workbooks only."""
from browser_check import fixture_module
from customer_helpers import fill_customer
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8080')
    expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    for index, identity in enumerate(['999999999', '888888888', '777777777']):
        if index:
            page.get_by_role('button', name='+ הוסף לקוח נוסף', exact=True).click()
        card = page.locator('.customer-card').nth(0 if index == 0 else 1)
        fill_customer(card, identity)
        card.get_by_label('שם פרטי', exact=True).fill(f'בדיקה{index}')
        card.get_by_label('שם משפחה', exact=True).fill(f'משפחה{index}')
        card.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
            'name': 'synthetic.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'buffer': fixture_module.fixture([
                fixture_module.row(insured_id=int(identity), insurer='חברת בדיקה', policy_number='12345', premium=10 + index),
                fixture_module.row(insured_id=int(identity), insurer='חברת בדיקה', policy_number=str(90000 + index), premium=0),
            ])})
        expect(card.locator('.upload-success')).to_be_visible()
    selection = page.get_by_role('region', name='בחירת לקוחות לתצוגה משותפת')
    combine = selection.get_by_role('button', name='הצגת הלקוחות יחד')
    expect(combine).to_be_disabled()
    for checkbox in selection.get_by_role('checkbox').all():
        checkbox.check()
    combine.click()
    shared = page.locator('.shared-portfolio')
    expect(shared.locator('.policy')).to_have_count(4)
    expect(shared.locator('.totals')).to_have_count(3)
    policy = shared.locator('.policy').filter(has_text='12345')
    expect(policy.locator('.shared-monthly-total')).to_contain_text('33.00')
    policy.locator('summary').click()
    expect(policy.locator('tbody tr')).to_have_count(3)
    row = policy.get_by_role('row').filter(has=page.get_by_role('cell', name='בדיקה1 משפחה1', exact=True))
    row.get_by_role('button', name='עריכה', exact=True).click()
    dialog = page.get_by_role('dialog')
    expect(dialog).to_contain_text('בדיקה1 משפחה1')
    dialog.get_by_label('פרמיה', exact=True).fill('25')
    dialog.get_by_label('פרטים נוספים', exact=True).fill('בדיקה משותפת')
    dialog.get_by_role('button', name='שמירת תיקונים', exact=True).click()
    expect(policy.locator('.policy-details')).to_contain_text('בדיקה1 משפחה1')
    expect(policy.locator('.shared-monthly-total')).to_contain_text('47.00')
    expect(shared.get_by_role('region', name='בדיקה1 משפחה1 · כל התיק · אחרי תיקונים')).to_contain_text('25.00')
    row.get_by_role('button', name='החרגה', exact=True).click()
    expect(policy.locator('.shared-monthly-total')).to_contain_text('22.00')
    expect(shared.get_by_role('region', name='בדיקה1 משפחה1 · כל התיק · אחרי תיקונים')).to_contain_text('0.00')
    row.get_by_role('button', name='שחזור', exact=True).click()
    expect(policy.locator('.shared-monthly-total')).to_contain_text('47.00')
    row.get_by_role('button', name='מקור', exact=True).click()
    expect(shared.locator('.source-row[open]')).to_contain_text('בדיקה1 משפחה1')
    expect(shared.locator('.source-row[open]')).to_contain_text('11')
    shared.get_by_role('button', name='חזרה לפוליסות', exact=True).click()
    for width in [1440, 768, 390, 320]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    selection.get_by_role('button', name='חזרה לתצוגה נפרדת').click()
    expect(shared).to_have_count(0)
    own = page.get_by_role('region', name='תיק לקוח בדיקה1 משפחה1', exact=True)
    expect(own.locator('.totals').first).to_contain_text('25.00')
    expect(page.get_by_role('region', name='תיק לקוח בדיקה0 משפחה0', exact=True).locator('.totals').first).to_contain_text('10.00')
    combine.click()
    # Replacing a selected report must discard its old entries and corrections.
    replacement = page.locator('.customer-card').filter(has=page.locator('input[value="בדיקה1"]'))
    replacement.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
        'name': 'replacement.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'buffer': fixture_module.fixture([fixture_module.row(insured_id=888888888, insurer='חברת בדיקה', policy_number='12345', premium=31)])})
    expect(shared.get_by_role('region', name='בדיקה1 משפחה1 · כל התיק · אחרי תיקונים')).to_contain_text('31.00')
    expect(shared.locator('.policy')).to_have_count(3)
    expect(shared.locator('.policy-details')).to_have_count(0)
    page.on('dialog', lambda dialog: dialog.accept())
    page.locator('.customer-card').filter(has=page.get_by_label('שם פרטי', exact=True).and_(page.locator('input[value="בדיקה2"]'))).get_by_role('button', name='הסרת לקוח', exact=True).click()
    expect(shared.locator('.policy')).to_have_count(2)
    page.route('**/api/instance', lambda route: route.fulfill(json={'instance_id': 'shared-restart'}))
    expect(shared).to_have_count(0, timeout=10000)
    expect(page.locator('.customer-card')).to_have_count(1)
    expect(page.get_by_label('שם פרטי', exact=True)).to_have_value('')
    assert page.evaluate('localStorage.length + sessionStorage.length') == 0
    page.reload()
    expect(selection).to_have_count(0)
    assert not errors, errors
    browser.close()
print('PASS: shared grouping, three owners, edits, exclusion/restore, source, separate totals, RTL widths, removal, lifecycle')
