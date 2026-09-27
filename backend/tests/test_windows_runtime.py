"""Exercise actual loopback sockets and Windows per-user launch coordination."""
from pathlib import Path
import socket
import sys
import time

import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows runtime')
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'desktop'))


def test_single_instance_notification():
    from windows_instance import UserInstance
    first = UserInstance()
    try:
        assert first.primary
        second = UserInstance()
        try:
            assert not second.primary
            second.notify()
            assert first.requested()
            assert not first.requested()
        finally:
            second.close()
    finally:
        first.close()
    third = UserInstance()
    try:
        assert third.primary
    finally:
        third.close()


def test_server_readiness_and_shutdown(tmp_path, monkeypatch):
    from app import desktop
    from launcher import LocalServer
    (tmp_path / 'index.html').write_text('synthetic', encoding='utf-8')
    monkeypatch.setattr(desktop, 'web_directory', lambda: tmp_path)
    original = list(desktop.app.router.routes)
    local = LocalServer()
    port = local.socket.getsockname()[1]
    try:
        assert local.socket.getsockname()[0] == '127.0.0.1'
        assert not local.ready()
        local.start()
        deadline = time.monotonic() + 10
        while not local.ready() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert local.ready()
        local.stop()
        local.thread.join(timeout=6)
        assert not local.thread.is_alive()
        assert not local.ready()
        with socket.socket() as probe:
            assert probe.connect_ex(('127.0.0.1', port)) != 0
    finally:
        local.stop()
        local.thread.join(timeout=6)
        desktop.app.router.routes[:] = original
        desktop.app.state.desktop_mode = False
