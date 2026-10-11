"""Private child of the native launcher. EOF on stdin ends the session.

The only stdout message is a readiness record. No customer data, access logs,
port files, sockets on disk, or application state are written to disk.
"""
import json
import logging
import socket
import sys
import threading
import time
import urllib.request

import uvicorn

from app.desktop import create_app


class LocalServer:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind(('127.0.0.1', 0))
            self.url = f'http://127.0.0.1:{self.socket.getsockname()[1]}'
            self.server = uvicorn.Server(uvicorn.Config(
                create_app(), host='127.0.0.1', log_config=None,
                access_log=False, loop='asyncio', http='h11', ws='none',
                lifespan='off', timeout_graceful_shutdown=3, server_header=False,
            ))
        except BaseException:
            self.socket.close()
            raise
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            self.server.run(sockets=[self.socket])
        except BaseException:
            pass  # The parent reports failure without logging request contents.
        finally:
            self.socket.close()

    def start(self):
        self.thread.start()

    def ready(self):
        if not self.server.started or not self.thread.is_alive():
            return None
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(self.url + '/api/instance', timeout=0.25) as response:
                record = json.load(response)
            if record.get('desktop_mode') is True and isinstance(record.get('instance_id'), str):
                return {'url': self.url, 'instance_id': record['instance_id']}
        except (OSError, ValueError):
            pass
        return None

    def stop(self):
        self.server.should_exit = True
        self.thread.join(timeout=5)
        self.socket.close()


def main():
    logging.disable(logging.CRITICAL)
    parent_closed = threading.Event()

    def watch_parent():
        try:
            # The launcher keeps its anonymous pipe open. Normal quit and a
            # launcher crash both close it, including during backend startup.
            while sys.stdin.buffer.read(1):
                pass
        finally:
            parent_closed.set()

    threading.Thread(target=watch_parent, daemon=True).start()
    server = None
    try:
        server = LocalServer()
        server.start()
        deadline = time.monotonic() + 25
        while not parent_closed.is_set():
            if not server.thread.is_alive() or time.monotonic() >= deadline:
                return 1
            record = server.ready()
            if record:
                print(json.dumps(record), flush=True)
                break
            parent_closed.wait(0.05)
        while not parent_closed.wait(0.1):
            if not server.thread.is_alive():
                return 1
        return 0
    except BaseException:
        return 1
    finally:
        if server:
            server.stop()


if __name__ == '__main__':
    sys.exit(main())
