"""Write an ignored synthetic workbook for desktop Excel verification."""
from pathlib import Path
import sys
from copy import deepcopy
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests')]
from test_export import customer
from app.exporter import ExportRequest, create_export

a, b = customer(), customer('000000002', 'שני')
for c in [a, b]:
    for index, e in enumerate(c['report']['entries']):
        e['values']['category'] = 'ביטוח בריאות'
        e['values']['product_type'] = ['השתלות וטיפולים', 'ייעוץ ובדיקות', 'ניתוחים בישראל'][index]
        e['values']['insurer'] = 'הראל'
        e['values']['policy_number'] = '000123'
        e['baseline'] = deepcopy(e['values'])
        e['copied'] = True
a['report']['entries'][0]['values']['premium'] = '20.20'
a['report']['entries'][0]['values']['additional_details'] = 'הערה סינתטית לבדיקת ייצוא\nשורה נוספת לקריאה'
folder = ROOT / 'test-results'
folder.mkdir(exist_ok=True)
(folder / 'compact-export.xlsx').write_bytes(create_export(ExportRequest(customers=[a, b], agent={'firstName': 'סוכן', 'lastName': 'בדיקה', 'date': '2026-10-04'})))
print('Synthetic workbook generated')
