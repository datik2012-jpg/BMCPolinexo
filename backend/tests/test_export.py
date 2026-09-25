from copy import deepcopy
from io import BytesIO

from fastapi.testclient import TestClient
from openpyxl import load_workbook

from app.main import app, INSTANCE_ID
from app.parser import parse_workbook
from test_import import fixture, row


def customer(identity='000000001', first='בדיקה'):
    report = parse_workbook(fixture([row(insured_id=identity, premium='10.10'),
                                     row(insured_id=identity, premium='120', frequency='שנתית'),
                                     row(insured_id=identity, premium='0')]))
    report['instance_id'] = INSTANCE_ID
    return {'id': identity, 'details': {'firstName': first, 'lastName': 'סינתטי', 'identity': identity,
            'relationship': '', 'birthDate': '', 'gender': 'זכר', 'maritalStatus': '', 'smoking': ''}, 'report': report}


def test_export_preserves_notes_owners_source_and_totals():
    a, b = customer(), customer('000000002', 'שני')
    a['report']['entries'][0]['values']['additional_details'] = '=HYPERLINK("https://example.com")\nפרטים לכיסוי'
    a['report']['entries'][0]['values']['premium'] = '20.20'
    a['report']['entries'][1]['excluded'] = True
    snapshot = deepcopy([a, b])
    response = TestClient(app).post('/api/export', json={'customers': [a, b]})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-instance-id'] == INSTANCE_ID
    assert response.headers['content-disposition'].endswith('"insurance-portfolios.xlsx"')
    book = load_workbook(BytesIO(response.content), data_only=False)
    values = load_workbook(BytesIO(response.content), data_only=True)
    assert book.sheetnames == ['לקוחות', 'כיסויים מעודכנים', 'מקור ושינויים', 'סיכומים']
    sheet = book['כיסויים מעודכנים']
    assert sheet.max_row == 7
    assert sheet['D2'].value == '000000001'
    assert sheet['K2'].value == a['report']['entries'][0]['values']['additional_details']
    assert sheet['K2'].data_type == 's'
    assert sheet['K5'].value != sheet['K2'].value
    assert sheet['P3'].value == 'מוחרג'
    assert sheet['U4'].value == 0
    assert book['מקור ושינויים']['T2'].value == sheet['K2'].value
    assert book['מקור ושינויים']['U2'].value == '10.10'
    assert values['סיכומים']['D2'].value == 20.2
    assert values['סיכומים']['E2'].value == 0
    assert values['סיכומים']['D3'].value == 10.1
    assert values['סיכומים']['E3'].value == 120
    assert book['סיכומים']['D2'].data_type == 'f'
    assert all(s.sheet_view.rightToLeft and s.freeze_panes and s.auto_filter.ref for s in book)
    assert [a, b] == snapshot


def test_export_invalid_premium_is_partial_and_keeps_text():
    c = customer()
    c['report']['entries'][0]['values']['premium'] = 'bad'
    result = TestClient(app).post('/api/export', json={'customers': [c]})
    book = load_workbook(BytesIO(result.content), data_only=True)
    assert book['כיסויים מעודכנים']['L2'].value == 'bad'
    assert book['סיכומים']['D2'].value == 0
    assert 'חלקי' in book['סיכומים']['F2'].value


def test_export_rejects_bad_or_stale_payload_without_echoing_data():
    client = TestClient(app)
    for body in [{}, {'customers': []}, {'customers': [customer(), customer()]}]:
        assert client.post('/api/export', json=body).status_code == 400
    c = customer()
    c['report']['instance_id'] = 'old'
    assert client.post('/api/export', json={'customers': [c]}).status_code == 409
    c['report']['instance_id'] = INSTANCE_ID
    c['report']['entries'][0]['values']['additional_details'] = 'x' * 32768
    result = client.post('/api/export', json={'customers': [c]})
    assert result.status_code == 400
    assert 'xxx' not in result.text
