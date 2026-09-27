"""Windows kernel objects coordinate launches without writing user data to disk."""
import ctypes
from ctypes import wintypes
import time
import os

kernel = ctypes.WinDLL('kernel32', use_last_error=True)
advapi = ctypes.WinDLL('advapi32', use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.LocalFree.argtypes = [ctypes.c_void_p]
advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
advapi.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel.CreateMutexW.restype = wintypes.HANDLE
kernel.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
kernel.CreateEventW.restype = wintypes.HANDLE
kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel.OpenEventW.restype = wintypes.HANDLE
kernel.SetEvent.argtypes = [wintypes.HANDLE]
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]


def user_sid() -> str:
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 8, ctypes.byref(token)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        size = wintypes.DWORD()
        advapi.GetTokenInformation(token, 1, None, 0, ctypes.byref(size))
        buffer = ctypes.create_string_buffer(size.value)
        if not advapi.GetTokenInformation(token, 1, buffer, size, ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
        sid = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_void_p))[0]
        value = wintypes.LPWSTR()
        if not advapi.ConvertSidToStringSidW(sid, ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return value.value
        finally:
            kernel.LocalFree(ctypes.cast(value, ctypes.c_void_p))
    finally:
        kernel.CloseHandle(token)


class UserInstance:
    def __init__(self):
        self.handles = []
        self.event = None
        self.name = 'Global\\BMCPolinexo-' + user_sid()
        mutex = kernel.CreateMutexW(None, False, self.name)
        existed = ctypes.get_last_error() == 183
        if not mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        self.handles.append(mutex)
        self.primary = not existed
        if self.primary:
            self.event = kernel.CreateEventW(None, False, False, self.name + '-open')
            if not self.event:
                self.close()
                raise ctypes.WinError(ctypes.get_last_error())
            self.handles.append(self.event)
            # Inno Setup checks this guard before upgrades and uninstalling.
            guard_name = 'Global\\BMCPolinexo-Setup-' + os.environ['USERDOMAIN'] + '-' + os.environ['USERNAME']
            guard = kernel.CreateMutexW(None, False, guard_name)
            if not guard:
                self.close()
                raise ctypes.WinError(ctypes.get_last_error())
            self.handles.append(guard)

    def notify(self):
        # The first process may still be creating its event.
        for _ in range(50):
            event = kernel.OpenEventW(2, False, self.name + '-open')
            if event:
                try:
                    if not kernel.SetEvent(event):
                        raise ctypes.WinError(ctypes.get_last_error())
                    return
                finally:
                    kernel.CloseHandle(event)
            time.sleep(0.1)
        raise RuntimeError('The running launcher is unavailable.')

    def requested(self) -> bool:
        return kernel.WaitForSingleObject(self.event, 0) == 0

    def close(self):
        for handle in reversed(self.handles):
            kernel.CloseHandle(handle)
        self.handles.clear()
