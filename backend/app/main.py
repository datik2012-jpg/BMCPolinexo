"""Local pilot API. Requests and workbook contents are never persisted."""
from email.parser import BytesParser
from email.policy import default
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from .parser import ImportProblem, parse_workbook

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
INSTANCE_ID = str(uuid4())
MAX_BODY = 5 * 1024 * 1024

@app.middleware('http')
async def no_cache(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/api/instance')
async def instance():
    return {'instance_id': INSTANCE_ID}

@app.post('/api/import')
async def import_file(request: Request):
    content_type = request.headers.get('content-type', '')
    if not content_type.lower().startswith('multipart/form-data;') or '\r' in content_type or '\n' in content_type:
        raise HTTPException(400, 'יש לבחור קובץ Excel מסוג ‎.xlsx')
    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > MAX_BODY:
            raise HTTPException(413, 'הקובץ גדול מדי. הגודל המרבי הוא 5 מגה־בייט')
        payload.extend(chunk)
    try:
        message = BytesParser(policy=default).parsebytes(b'Content-Type: ' + content_type.encode('ascii') + b'\r\nMIME-Version: 1.0\r\n\r\n' + payload)
        parts = list(message.iter_parts())
        if message.defects or len(parts) != 1 or parts[0].get_param('name', header='content-disposition') != 'file':
            raise ValueError
        part = parts[0]
        filename = part.get_filename() or ''
        if not filename.lower().endswith('.xlsx') or part.defects:
            raise ValueError
        data = part.get_payload(decode=True)
        if not data:
            raise ValueError
    except Exception:
        raise HTTPException(400, 'יש להעלות קובץ אחד מסוג ‎.xlsx') from None
    try:
        result = await run_in_threadpool(parse_workbook, data)
    except ImportProblem as problem:
        raise HTTPException(400, str(problem)) from None
    return {'instance_id': INSTANCE_ID, **result}
