"""Desktop static serving does not change API behavior or expose source files."""
from fastapi.testclient import TestClient
import pytest

from app import desktop


def test_packaged_web_and_headers(tmp_path, monkeypatch):
    (tmp_path / 'index.html').write_text('<html dir="rtl">synthetic</html>', encoding='utf-8')
    (tmp_path / 'app.js').write_text('console.log("synthetic")', encoding='utf-8')
    monkeypatch.setattr(desktop, 'web_directory', lambda: tmp_path)
    original = list(desktop.app.router.routes)
    try:
        with TestClient(desktop.create_app()) as client:
            assert client.get('/').status_code == 200
            assert client.get('/app.js').status_code == 200
            assert 'instance_id' in client.get('/api/instance').json()
            assert client.get('/api/instance').json()['desktop_mode'] is True
            assert client.get('/api/missing').status_code == 404
            assert client.get('/../requirements.txt').status_code == 404
            assert client.post('/api/import', content=b'invalid').status_code == 400
            for path in ['/', '/app.js', '/missing', '/api/instance', '/api/missing']:
                response = client.get(path)
                assert response.headers['cache-control'] == 'no-store'
                assert response.headers['x-content-type-options'] == 'nosniff'
                assert response.headers['referrer-policy'] == 'no-referrer'
                assert response.headers['x-frame-options'] == 'DENY'
            desktop.create_app()
            assert sum(r.name == 'desktop-web' for r in desktop.app.routes) == 1
    finally:
        desktop.app.router.routes[:] = original
        desktop.app.state.desktop_mode = False


def test_missing_ui_fails_before_start(tmp_path, monkeypatch):
    monkeypatch.setattr(desktop, 'web_directory', lambda: tmp_path)
    with pytest.raises(RuntimeError, match='missing'):
        desktop.create_app()
