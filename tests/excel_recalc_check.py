"""Native Excel regression. Requires local Excel and pywin32; synthetic files only."""
from pathlib import Path
import time
import threading
import win32com.client
import win32gui
import win32process
import win32con
import pythoncom

def call(action):
    for attempt in range(40):
        try:
            return action()
        except pythoncom.com_error as error:
            if error.hresult != -2147418111 or attempt == 39:
                raise
            time.sleep(.25)


ROOT = Path(__file__).resolve().parents[1]
app = win32com.client.DispatchEx('Excel.Application')
call(lambda: setattr(app, 'Visible', False))
call(lambda: setattr(app, 'AutomationSecurity', 3))
call(lambda: setattr(app, 'DisplayAlerts', False))
_, process_id = win32process.GetWindowThreadProcessId(call(lambda: app.Hwnd))
stop = threading.Event()


def close_startup_dialog():
    # Cancel Office's activation wizard in this newly created test instance only.
    # This does not activate Office or change its licensing settings.
    while not stop.wait(.2):
        def check(hwnd, unused):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == process_id and win32gui.GetWindowText(hwnd) == 'Microsoft Office Activation Wizard':
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        win32gui.EnumWindows(check, None)


thread = threading.Thread(target=close_startup_dialog, daemon=True)
thread.start()


book = None
try:
    book = call(lambda: app.Workbooks.Open(str(ROOT / 'test-results/compact-export.xlsx'), UpdateLinks=0, ReadOnly=True))
    sheet = call(lambda: book.Worksheets(1))
    calc = book.Worksheets(2)
    app.CalculateFullRebuild()
    selectors = [r for r in range(1, sheet.UsedRange.Rows.Count + 1) if sheet.Cells(r, 7).Value == 'כל המשפחה']
    family_rows = [r for r in range(1, sheet.UsedRange.Rows.Count + 1) if sheet.Cells(r, 1).Value == 'סה"כ בחודש למשפחה']
    assert len(selectors) == 2
    family = [sheet.Cells(r, 9).Value for r in family_rows]
    choices = 0
    for row in selectors:
        selector = sheet.Cells(row, 7)
        assert selector.Validation.Type == 3
        source = book.Names(selector.Validation.Formula1.lstrip('=')).RefersToRange
        for i in range(source.Rows.Count):
            sr = source.Row + i
            selector.Value = calc.Cells(sr, 2).Value
            app.CalculateFullRebuild()
            assert abs(sheet.Cells(row, 9).Value - calc.Cells(sr, 3).Value) < .000001
            assert [sheet.Cells(r, 9).Value for r in family_rows] == family
            choices += 1
        selector.Value = 'כל המשפחה'
    app.CalculateFullRebuild()
    coverage_choices = 0
    for row in selectors:
        coverage = sheet.Cells(row, 4)
        original_coverage = coverage.Value
        premium_before = sheet.Cells(row, 9).Value
        assert coverage.Validation.Type == 3
        assert coverage.Validation.InCellDropdown
        source = book.Names(coverage.Validation.Formula1.lstrip('=')).RefersToRange
        for i in range(1, source.Rows.Count + 1):
            coverage.Value = source.Cells(i, 1).Value
            assert coverage.Validation.Value  # Excel accepts the selected option.
            app.CalculateFullRebuild()
            assert sheet.Cells(row, 9).Value == premium_before
            assert [sheet.Cells(r, 9).Value for r in family_rows] == family
            coverage_choices += 1
        coverage.Value = original_coverage
    for tab in book.Worksheets:
        for cells in tab.UsedRange.Rows:
            for cell in cells.Cells:
                if cell.HasFormula:
                    assert not str(cell.Text).startswith(('#REF!', '#VALUE!', '#N/A', '#NAME?', '#DIV/0!', '#NUM!'))
    summary_row = next(r for r in range(1, sheet.UsedRange.Rows.Count + 1) if sheet.Cells(r, 1).Value == 'סיכום פגישה והמלצות')
    summary = sheet.Cells(summary_row + 1, 1)
    assert summary.Value is None
    assert summary.MergeArea.Columns.Count == 13 and summary.MergeArea.Rows.Count == 1
    assert summary.RowHeight == 120 and summary.WrapText
    summary_text = 'סיכום סינתטי למילוי הסוכן\nהמלצות סינתטיות בשורה נוספת באותה תיבה'
    summary.Value = summary_text
    app.CalculateFullRebuild()
    assert [sheet.Cells(r, 9).Value for r in family_rows] == family
    sheet.ExportAsFixedFormat(0, str(ROOT / 'test-results/compact-export-preview.pdf'))
    saved = ROOT / 'test-results/compact-export-recalculated.xlsx'
    call(lambda: book.SaveAs(str(saved), 51))
    book.Close(False)
    book = call(lambda: app.Workbooks.Open(str(saved), UpdateLinks=0, ReadOnly=True))
    assert call(lambda: book.Worksheets(1).Cells(selectors[0], 7).Validation.Type) == 3
    assert call(lambda: book.Worksheets(1).Cells(selectors[0], 4).Validation.Type) == 3
    assert call(lambda: book.Worksheets(1).Cells(summary_row + 1, 1).Value) == summary_text
    assert call(lambda: book.Worksheets(1).Cells(summary_row + 1, 1).MergeArea.Columns.Count) == 13
    print(f'PASS: {choices} insured choices, {coverage_choices} coverage choices, both states, stable family totals, formulas, save/reopen and PDF render')
finally:
    if book is not None:
        call(lambda: book.Close(False))
    call(lambda: app.Quit())
    stop.set()
    thread.join(timeout=1)
