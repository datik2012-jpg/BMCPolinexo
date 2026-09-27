"""Exercise actual loopback sockets and Windows per-user launch coordination."""
from pathlib import Path
import socket
import sys
import time
import logging

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


@pytest.fixture
def hidden_launcher(monkeypatch):
    """Run the real Tk event loop without displaying dialogs or opening a browser."""
    import gc
    # Tk interpreters must be collected on their owning thread. Pytest keeps
    # fixture references until teardown; collect the preceding test's cycles
    # here before a new server worker can trigger Python's cyclic collector.
    gc.collect()
    import launcher
    root = launcher.tk.Tk()
    root.withdraw()
    monkeypatch.setattr(launcher.tk, 'Tk', lambda: root)
    monkeypatch.setattr(root, 'deiconify', lambda: None)
    root.after(10000, root.quit)
    prior_logging = logging.root.manager.disable
    yield launcher, root
    logging.disable(prior_logging)


def test_startup_failure_is_safe_and_releases_instance(hidden_launcher, monkeypatch):
    launcher, _ = hidden_launcher
    errors = []

    def fail_startup():
        raise RuntimeError('SYNTHETIC-PRIVATE-DETAIL-DO-NOT-DISPLAY')

    monkeypatch.setattr(launcher, 'create_app', fail_startup)
    monkeypatch.setattr(launcher.messagebox, 'showerror', lambda title, text, **kwargs: errors.append(text))
    launcher.run()
    assert len(errors) == 1
    assert 'לא ניתן להפעיל' in errors[0]
    assert 'להתקין מחדש' in errors[0]
    assert 'SYNTHETIC' not in errors[0]
    instance = launcher.UserInstance()
    try:
        assert instance.primary, 'A failed startup must not block the next launch'
    finally:
        instance.close()


@pytest.mark.parametrize('browser_raises', [False, True])
def test_browser_failure_offers_ready_local_url_and_shutdown(hidden_launcher, tmp_path, monkeypatch, browser_raises):
    from app import desktop
    import urllib.request
    launcher, root = hidden_launcher
    (tmp_path / 'index.html').write_text('synthetic', encoding='utf-8')
    monkeypatch.setattr(desktop, 'web_directory', lambda: tmp_path)
    original = list(desktop.app.router.routes)
    offers, ready_urls, errors = [], [], []

    def unavailable_browser(url):
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=2) as response:
            ready_urls.append((url, response.status))
        if browser_raises:
            raise OSError('SYNTHETIC-PRIVATE-BROWSER-ERROR')
        return False

    def offer_url(title, text, **kwargs):
        offers.append(text)
        root.after(0, root.quit)

    monkeypatch.setattr(launcher.webbrowser, 'open', unavailable_browser)
    monkeypatch.setattr(launcher.messagebox, 'showinfo', offer_url)
    monkeypatch.setattr(launcher.messagebox, 'showerror', lambda title, text, **kwargs: errors.append(text))
    try:
        launcher.run()
        assert not errors
        assert len(ready_urls) == len(offers) == 1
        url, status = ready_urls[0]
        assert status == 200
        assert offers[0].endswith(url)
        assert 'SYNTHETIC' not in offers[0]
        with socket.socket() as probe:
            assert probe.connect_ex(('127.0.0.1', int(url.rsplit(':', 1)[1]))) != 0
    finally:
        desktop.app.router.routes[:] = original
        desktop.app.state.desktop_mode = False
