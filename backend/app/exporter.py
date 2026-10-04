"""Generate portfolio snapshots entirely in memory; never interpret user text as formulas."""
from collections import Counter
from pathlib import Path
from openpyxl.drawing.image import Image
from openpyxl.worksheet.page import PageMargins
from decimal import Decimal
from io import BytesIO
from math import ceil
import re
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from pydantic import BaseModel, Field, field_validator, model_validator

from .parser import FIELDS, HEADERS as SOURCE_HEADERS, normalize

HEADERS = tuple("הוראות הסוכן" if key == "additional_details" else header
                for key, header in zip(FIELDS, SOURCE_HEADERS))


class ExportEntry(BaseModel):
    id: str = Field(max_length=200)
    source_sheet: str = Field(max_length=32767)
    source_row: int = Field(ge=1, le=10000)
    original: dict[str, str]
    values: dict[str, str]
    issues: list[str] = Field(default_factory=list, max_length=100)
    excluded: bool = False

    @field_validator('original', 'values')
    @classmethod
    def complete_fields(cls, value):
        if set(value) != set(FIELDS):
            raise ValueError('Invalid fields')
        return value


class ExportReport(BaseModel):
    instance_id: str
    report_date: str | None
    entries: list[ExportEntry] = Field(min_length=1, max_length=10000)
    warnings: list[str] = Field(default_factory=list, max_length=1000)


DETAILS = {'firstName': 'שם פרטי', 'lastName': 'שם משפחה', 'identity': 'תעודת זהות',
           'relationship': 'קרבה משפחתית', 'birthDate': 'תאריך לידה', 'gender': 'מין',
           'maritalStatus': 'מצב משפחתי', 'smoking': 'עישון'}


class ExportCustomer(BaseModel):
    id: str = Field(max_length=200)
    details: dict[str, str]
    report: ExportReport

    @field_validator('details')
    @classmethod
    def complete_details(cls, value):
        if set(value) != set(DETAILS):
            raise ValueError('Invalid details')
        return value


class ExportAgent(BaseModel):
    firstName: str = Field(default="", max_length=100)
    lastName: str = Field(default="", max_length=100)
    date: str = Field(default="", max_length=10)


class ExportRequest(BaseModel):
    agent: ExportAgent = Field(default_factory=ExportAgent)
    customers: list[ExportCustomer] = Field(min_length=1, max_length=50)

    @model_validator(mode='after')
    def bounded(self):
        if len({c.id for c in self.customers}) != len(self.customers):
            raise ValueError('Duplicate customer')
        if sum(len(c.report.entries) for c in self.customers) > 20000:
            raise ValueError('Too many entries')
        # Excel truncates long text silently; reject instead of losing notes.
        def validate(value):
            if isinstance(value, str) and (len(value) > 32767 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]', value)):
                raise ValueError('Unsupported text')
            if isinstance(value, dict):
                for item in value.values():
                    validate(item)
            if isinstance(value, list):
                for item in value:
                    validate(item)
        validate(self.model_dump())
        return self


def append_text_safe(sheet, values):
    if any(isinstance(value, str) and len(value) > 32767 for value in values):
        raise ValueError('Text exceeds Excel cell limit')
    sheet.append(values)
    for cell in sheet[sheet.max_row]:
        if isinstance(cell.value, str):
            cell.data_type = 's'
            cell.number_format = '@'


def create_export(request: ExportRequest) -> bytes:
    book = Workbook()
    book.remove(book.active)
    customers = book.create_sheet('לקוחות')
    current = book.create_sheet('כיסויים מעודכנים')
    original = book.create_sheet('מקור ושינויים')
    summary = book.create_sheet('סיכומים')
    append_text_safe(customers, ['מספר לקוח בייצוא', *DETAILS.values(), 'תאריך הדוח', 'הערות ייבוא'])
    append_text_safe(current, ['מספר לקוח בייצוא', 'שם פרטי', 'שם משפחה', 'תעודת זהות לקוח',
                                *HEADERS, 'מצב', 'שדות שתוקנו', 'בדיקה', 'גיליון מקור', 'שורת מקור',
                                'פרמיה חודשית לחישוב (₪)', 'פרמיה שנתית לחישוב (₪)'])
    audit_headers = ['מספר לקוח בייצוא', 'שם פרטי', 'שם משפחה', 'מזהה שורה', 'גיליון מקור', 'שורת מקור']
    for header in HEADERS:
        audit_headers.extend([f'{header} — מקור', f'{header} — מעודכן'])
    append_text_safe(original, [*audit_headers, 'מצב', 'הערות המקור'])
    append_text_safe(summary, ['מספר לקוח בייצוא', 'שם פרטי', 'שם משפחה', 'סה״כ חודשי (₪)', 'סה״כ שנתי (₪)', 'שלמות הסכומים'])
    cached = {}
    for index, customer in enumerate(request.customers, 1):
        d, report = customer.details, customer.report
        append_text_safe(customers, [index, *(d[k] for k in DETAILS), report.report_date or '', '\n'.join(report.warnings)])
        monthly, annual = Decimal(0), Decimal(0)
        incomplete = False
        signatures = Counter(tuple(e.values[k] for k in FIELDS) for e in report.entries if not e.excluded)
        for entry in report.entries:
            normalized, problems = normalize(entry.values)
            valid_amount = not any('הפרמיה' in problem for problem in problems)
            freq = normalized['frequency']
            month = Decimal(normalized['premium']) if valid_amount and freq == 'monthly' else None
            year = Decimal(normalized['premium']) if valid_amount and freq == 'annual' else None
            if not entry.excluded:
                monthly += month or Decimal(0)
                annual += year or Decimal(0)
                incomplete |= not valid_amount or freq not in ('monthly', 'annual')
            status = 'מוחרג' if entry.excluded else 'נכלל'
            changed = ' · '.join(header for key, header in zip(FIELDS, HEADERS) if entry.values[key] != entry.original[key])
            if signatures[tuple(entry.values[k] for k in FIELDS)] > 1:
                problems.append('חשד לשורה כפולה — נכללת בחישוב עד להחרגה')
            problems.extend(i for i in entry.issues if 'אפסים מובילים' in i or 'נוסח' in i)
            append_text_safe(current, [index, d['firstName'], d['lastName'], d['identity'],
                                      *(entry.values[k] for k in FIELDS), status, changed, '\n'.join(problems),
                                      entry.source_sheet, entry.source_row, month, year])
            values = [index, d['firstName'], d['lastName'], entry.id, entry.source_sheet, entry.source_row]
            for key in FIELDS:
                values.extend([entry.original[key], entry.values[key]])
            append_text_safe(original, [*values, status, '\n'.join(entry.issues)])
        append_text_safe(summary, [index, d['firstName'], d['lastName'], None, None,
                                   'חלקי — יש פרמיות או תדירויות לא תקינות' if incomplete else 'מלא'])
        row = summary.max_row
        for col, amount, source_col in [('D', monthly, 'U'), ('E', annual, 'V')]:
            # Match stable customer numbers so sorting coverage rows remains safe.
            end = 1 + sum(len(c.report.entries) for c in request.customers)
            summary[f'{col}{row}'] = f'=SUMIFS(\'כיסויים מעודכנים\'!{source_col}$2:{source_col}${end},\'כיסויים מעודכנים\'!A$2:A${end},A{row},\'כיסויים מעודכנים\'!P$2:P${end},"נכלל")'
            cached[f'{col}{row}'] = amount
    summary.append([])
    append_text_safe(summary, ['סכומים לפי התיקונים וההחרגות בזמן הייצוא. הסכומים השנתיים אינם תשלומים חודשיים.'])
    append_text_safe(summary, ['כל הכיסויים מיוצאים, גם אם הוסתרו בסינון. כפילויות אינן נמחקות אוטומטית.'])
    append_text_safe(summary, ['זהו צילום מצב של העבודה; שינוי פרטי כיסוי בקובץ אינו מעדכן את האפליקציה.'])
    # Stack all existing information on one worksheet, preserving source history.
    combined = book.create_sheet('תיק ביטוח')
    append_text_safe(combined, ['', 'שם פרטי של הסוכן', 'שם משפחה של הסוכן', 'תאריך'])
    append_text_safe(combined, ['', request.agent.firstName, request.agent.lastName, request.agent.date])
    logo = Image(Path(__file__).parent / 'assets' / 'bmc-select.jpg')
    logo.width, logo.height = 100, 40
    combined.add_image(logo, 'A1')
    offsets = {}
    header_rows = {1}
    for source in [customers, current, original, summary]:
        title_row = combined.max_row + 2
        combined.cell(title_row, 1, source.title)
        header_rows.update([title_row, title_row + 1])
        offsets[source.title] = title_row
        for row in source:
            for cell in row:
                target = combined.cell(cell.row + title_row, cell.column, cell.value)
                target.data_type = cell.data_type
                target.number_format = cell.number_format
    coverage_start = offsets[current.title] + 2
    coverage_end = offsets[current.title] + current.max_row
    new_cached = {}
    for index in range(len(request.customers)):
        row = offsets[summary.title] + index + 2
        for col, source_col in [('D', 'U'), ('E', 'V')]:
            combined[f'{col}{row}'] = f'=SUMIFS({source_col}${coverage_start}:{source_col}${coverage_end},A${coverage_start}:A${coverage_end},A{row},P${coverage_start}:P${coverage_end},"נכלל")'
            combined[f'{col}{row}'].number_format = '#,##0.00 "₪"'
            new_cached[f'{col}{row}'] = cached[f'{col}{index + 2}']
    cached = new_cached
    for source in [customers, current, original, summary]:
        book.remove(source)
    combined.sheet_view.rightToLeft = True
    combined.freeze_panes = f'E{coverage_start}'
    combined.auto_filter.ref = f'A{coverage_start - 1}:V{coverage_end}'
    for col in range(1, combined.max_column + 1):
        combined.column_dimensions[get_column_letter(col)].width = 18
    for col in ['K', 'S', 'T']:
        combined.column_dimensions[col].width = 32
    for row in combined:
        for cell in row:
            heading = cell.row in header_rows
            cell.font = Font(name='Arial', size=9, color='FFFFFF' if heading else '183D42', bold=heading)
            cell.alignment = Alignment(vertical='center', horizontal='right', wrap_text=True)
            if heading or cell.row % 2 == 0:
                cell.fill = PatternFill('solid', fgColor='216B60' if heading else 'EFF6F5')
        lines = max((sum(max(1, ceil(len(line) / max(1, combined.column_dimensions[cell.column_letter].width - 2)))
                         for line in str(cell.value or '').split('\n')) for cell in row if cell.data_type != 'f'), default=1)
        combined.row_dimensions[row[0].row].height = min(409, max(15, lines * 12))
    combined.row_dimensions[1].height = 21
    combined.row_dimensions[2].height = 21
    for row in range(coverage_start, coverage_end + 1):
        for col in ['U', 'V']:
            combined[f'{col}{row}'].number_format = '#,##0.00 "₪"'
    combined.sheet_properties.pageSetUpPr.fitToPage = True
    combined.page_setup.orientation = 'landscape'
    combined.page_setup.paperSize = combined.PAPERSIZE_A4
    combined.page_setup.fitToWidth = 1
    combined.page_setup.fitToHeight = 1
    combined.print_options.horizontalCentered = True
    combined.page_margins = PageMargins(left=0.2, right=0.2, top=0.2, bottom=0.2, header=0, footer=0)
    combined.print_area = combined.dimensions
    output = BytesIO()
    book.save(output)
    # Cache Decimal-computed formula results for previewers; Excel recalculates on open.
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    result = BytesIO()
    with ZipFile(output) as source, ZipFile(result, 'w', ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = source.read(item.filename)
            if item.filename == 'xl/worksheets/sheet1.xml':
                root = ET.fromstring(data)
                for cell in root.findall('.//s:c', ns):
                    if cell.attrib['r'] in cached:
                        cell.find('s:v', ns).text = str(cached[cell.attrib['r']])
                data = ET.tostring(root, encoding='utf-8')
            target.writestr(item, data)
    return result.getvalue()
