"""Browser-to-XLSX regression with synthetic data only."""
from io import BytesIO
from pathlib import Path
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright, expect
from browser_check import fixture_module
from customer_helpers import fill_customer


def totals(book, label):
    return [book.active.cell(c.row, 8).value for row in book.active for c in row if c.value == label]


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:8080')
    expect(page.get_by_label('שם פרטי', exact=True)).to_be_enabled(timeout=15000)
    for index, identity in enumerate(['999999999', '888888888', '777777777']):
        if index:
            page.get_by_role('button', name='+ הוסף לקוח נוסף', exact=True).click()
        card = page.get_by_role('region', name='פרטי לקוח', exact=True).nth(index)
        fill_customer(card, identity)
        card.get_by_label('שם פרטי', exact=True).fill(f'בדיקה{index}')
        if index < 2:
            card.get_by_label('העלאת קובץ Excel הר ביטוח', exact=True).set_input_files({
                'name': 'synthetic.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'buffer': fixture_module.fixture([
                    fixture_module.row(insured_id=int(identity), insurer='הראל', policy_number='000123', premium=10 + index, category='ביטוח בריאות'),
                    fixture_module.row(insured_id=int(identity), insurer='הראל', policy_number='000456', premium=120, frequency='שנתית', category='ביטוח רכב'),
                ])})
            expect(card.locator('.upload-success')).to_be_visible()
    section = page.get_by_role('region', name='תיק לקוח בדיקה0 סינתטי', exact=True)
    existing = section.locator('.existing-section')
    existing.get_by_role('button', name='העתקה למצב החדש', exact=True).first.click()
    section.get_by_role('tab', name='מצב חדש').click()
    proposal = section.locator('.proposed-section')
    proposal.get_by_role('button', name='עריכה', exact=True).click()
    dialog = page.get_by_role('dialog')
    dialog.get_by_label('פרמיה', exact=True).fill('25.25')
    dialog.get_by_label('הוראות הסוכן', exact=True).fill('הערה סינתטית\n=1+1')
    dialog.get_by_role('button', name='שמירת תיקונים', exact=True).click()

    def download(scope):
        with page.expect_download() as event:
            scope.get_by_role('button', name='ייצוא ל־Excel', exact=True).click()
        item = event.value
        assert item.failure() is None
        data = Path(item.path()).read_bytes()
        item.delete()
        book = load_workbook(BytesIO(data), data_only=True)
        assert book.sheetnames == ['תיק ביטוח', 'נתוני חישוב', 'מקור ושינויים']
        assert [book.active.cell(r, 2).value for r in (6, 7, 8)] == ['בדיקה0', 'בדיקה1', 'בדיקה2']
        coverage_lists = [v for v in book.active.data_validations.dataValidation if v.formula1.startswith('=Coverages_')]
        assert len(coverage_lists) == 3
        assert all(book.active[str(v.sqref)].column == 4 for v in coverage_lists)
        assert all(v.showDropDown is False for v in coverage_lists)
        assert totals(book, 'סה"כ בחודש למשפחה') == [21, 25.25]
        assert totals(book, 'סה"כ פרמיות שנתיות למשפחה (לא תשלום חודשי)') == [240, 0]
        assert any('הערה סינתטית' in str(c.value) for row in book.active for c in row)
        return book

    book = download(proposal)
    assert totals(book, 'סה"כ חודשי לפי הבחירה') == [10, 25.25]
    assert len(book.active._images) == 4  # Brand plus three policy groups.
    selection = page.get_by_role('region', name='בחירת לקוחות לתצוגה משותפת')
    selection.get_by_role('checkbox', name='בדיקה0 סינתטי').check()
    selection.get_by_role('checkbox', name='בדיקה1 סינתטי').check()
    selection.get_by_role('button', name='הצגת הלקוחות יחד').click()
    shared = page.locator('.shared-portfolio .existing-section')
    expect(shared.locator('.totals').get_by_text('פרמיות שנתיות', exact=True)).to_have_count(2)
    for summary in shared.locator('.shared-policy-totals').all():
        expect(summary).not_to_contain_text('שנתי')
    book = download(shared)
    assert totals(book, 'סה"כ חודשי לפי הבחירה') == [21, 25.25]
    page.locator('.shared-portfolio').get_by_role('tab', name='מצב חדש').click()
    proposed_shared = page.locator('.shared-portfolio .proposed-section')
    book = download(proposed_shared)
    assert totals(book, 'סה"כ חודשי לפי הבחירה') == [21, 25.25]
    page.locator('.shared-portfolio').get_by_role('tab', name='מצב קיים').click()
    for width in [1440, 390, 320]:
        page.set_viewport_size({'width': width, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.route('**/api/export', lambda route: route.fulfill(status=500, json={'detail': 'הייצוא נכשל'}))
    shared.get_by_role('button', name='ייצוא ל־Excel', exact=True).click()
    expect(shared.get_by_role('alert')).to_contain_text('הייצוא נכשל')
    assert page.evaluate('localStorage.length + sessionStorage.length') == 0
    page.reload()
    expect(page.locator('.comparison-section')).to_have_count(0)
    assert not errors, errors
    browser.close()
print('PASS: complete family export, both states, notes, selectors, annual separation, logos, errors, RTL and refresh clearing')
