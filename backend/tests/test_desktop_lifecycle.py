"""Parent-pipe lifetime is enforced even before the server becomes ready."""
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('desktop_server', ROOT / 'desktop/server.py')
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)


def test_local_server_uses_loopback_and_ready_route(monkeypatch):
    from fastapi import FastAPI
    app = FastAPI()

    @app.get('/api/instance')
    def instance():
        return {'instance_id': 'synthetic', 'desktop_mode': True}

    monkeypatch.setattr(server_module, 'create_app', lambda: app)
    server = server_module.LocalServer()
    assert server.socket.getsockname()[0] == '127.0.0.1'
    server.start()
    deadline = time.monotonic() + 10
    record = None
    try:
        while time.monotonic() < deadline:
            record = server.ready()
            if record:
                break
            time.sleep(0.05)
        assert record == {'url': server.url, 'instance_id': 'synthetic'}
    finally:
        server.stop()
    assert not server.thread.is_alive()


@pytest.mark.parametrize('close_early', [False, True])
def test_parent_eof_stops_child(tmp_path, close_early):
    (tmp_path / 'index.html').write_text('<html dir="rtl">synthetic</html>', encoding='utf-8')
    code = (
        'import sys; from pathlib import Path; '
        f'sys.path[:0] = [{str(ROOT / "backend")!r}, {str(ROOT / "desktop")!r}]; '
        'from app import desktop; '
        f'desktop.web_directory = lambda: Path({str(tmp_path)!r}); '
        'import server; sys.exit(server.main())'
    )
    process = subprocess.Popen([sys.executable, '-c', code], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    url = None
    try:
        if not close_early:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(process.stdout.readline)
                try:
                    record = json.loads(future.result(timeout=15))
                except BaseException:
                    process.kill()
                    raise
            url = record['url']
            assert url.startswith('http://127.0.0.1:')
            assert urllib.request.urlopen(url + '/api/instance').status == 200
        process.stdin.close()
        assert process.wait(timeout=10) == 0
        assert process.stderr.read() == b''
        if url:
            port = int(url.rsplit(':', 1)[1])
            with socket.socket() as client:
                assert client.connect_ex(('127.0.0.1', port)) != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
