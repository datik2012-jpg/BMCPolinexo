"""Windowed local launcher. No customer data, ports or logs are persisted."""
import logging
import socket
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.request
import webbrowser

import uvicorn

from app.desktop import create_app
from windows_instance import UserInstance


class LocalServer:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            self.socket.bind(('127.0.0.1', 0))
            self.url = f'http://127.0.0.1:{self.socket.getsockname()[1]}'
            self.server = uvicorn.Server(uvicorn.Config(
                create_app(), host='127.0.0.1', log_config=None, access_log=False,
                loop='asyncio', http='h11', ws='none', lifespan='off',
                timeout_graceful_shutdown=3, server_header=False,
            ))
        except BaseException:
            self.socket.close()
            raise
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            self.server.run(sockets=[self.socket])
        except BaseException:
            # The launcher displays a fixed message, never request contents.
            pass
        finally:
            self.socket.close()

    def start(self):
        self.thread.start()

    def ready(self):
        if not self.server.started or not self.thread.is_alive():
            return False
        try:
            # Bypass machine proxy settings for the loopback readiness probe.
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                self.url + '/api/instance', timeout=0.25,
            ) as response:
                return response.status == 200
        except Exception:
            return False

    def stop(self):
        self.server.should_exit = True


def run():
    logging.disable(logging.CRITICAL)
    root = tk.Tk()
    root.withdraw()
    instance = None
    local = None
    try:
        instance = UserInstance()
        if not instance.primary:
            instance.notify()
            return
        root.title('BMCPolinexo')
        # Let Tk grow for Windows text/DPI scaling instead of clipping controls.
        root.minsize(470, 220)
        root.resizable(False, False)
        frame = ttk.Frame(root, padding=22)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='BMCPolinexo', font=('Segoe UI', 18), anchor='e').pack(fill='x')
        status = tk.StringVar(value='מפעיל את היישום…')
        ttk.Label(frame, textvariable=status, anchor='e').pack(fill='x', pady=12)
        ttk.Label(frame, text='סגירת חלון זה תפסיק את היישום.', anchor='e').pack(fill='x')
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=15)
        local = LocalServer()
        stopping = False
        opened = False
        started = time.monotonic()

        def open_browser():
            try:
                if not webbrowser.open(local.url):
                    raise RuntimeError()
            except Exception:
                messagebox.showinfo('BMCPolinexo', 'יש לפתוח בדפדפן את הכתובת:\n' + local.url, parent=root)

        open_button = ttk.Button(buttons, text='פתיחת היישום', command=open_browser, state='disabled')
        open_button.pack(side='right', padx=5)

        def stop():
            nonlocal stopping, started
            if stopping:
                return
            stopping = True
            started = time.monotonic()
            open_button.configure(state='disabled')
            status.set('סוגר את היישום…')
            local.stop()

        ttk.Button(buttons, text='יציאה', command=stop).pack(side='right', padx=5)
        root.protocol('WM_DELETE_WINDOW', stop)

        def poll():
            nonlocal opened
            if stopping:
                if not local.thread.is_alive() or time.monotonic() - started > 5:
                    root.quit()
                    return
            elif not opened:
                if local.ready():
                    opened = True
                    status.set('היישום פועל במחשב זה בלבד.')
                    open_button.configure(state='normal')
                    open_browser()
                elif not local.thread.is_alive() or time.monotonic() - started > 30:
                    messagebox.showerror('BMCPolinexo', 'לא ניתן להפעיל את היישום. יש לסגור ולנסות שוב.', parent=root)
                    stop()
            elif not local.thread.is_alive():
                messagebox.showerror('BMCPolinexo', 'היישום הפסיק לפעול. יש לסגור ולפתוח מחדש.', parent=root)
                stop()
            elif instance.requested():
                root.deiconify()
                root.lift()
                open_browser()
            root.after(150, poll)

        root.deiconify()
        local.start()
        root.after(150, poll)
        root.mainloop()
    except Exception:
        messagebox.showerror('BMCPolinexo', 'לא ניתן להפעיל את היישום. יש לסגור ולנסות שוב. אם התקלה נמשכת, יש להתקין מחדש.', parent=root)
    finally:
        if local:
            local.stop()
            if local.thread.ident:
                local.thread.join(timeout=4)
        if instance:
            instance.close()
        root.destroy()


if __name__ == '__main__':
    run()
