import ctypes
import random
import threading
import time
from ctypes import wintypes

user32 = ctypes.windll.user32

SM_CXICON = 11
SM_CYICON = 12
SM_CXSCREEN = 0
SM_CYSCREEN = 1
IDI_ERROR = 32513
IDI_WARNING = 32515

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def _make_resource_id(res_id: int):
    return ctypes.cast(ctypes.c_void_p(res_id), wintypes.LPCWSTR)


class _DrawIconEffect:
    def __init__(self):
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._interval = 5.0
        self._times = 0

    def _draw_once(self):
        ix = user32.GetSystemMetrics(SM_CXICON) // 2
        iy = user32.GetSystemMetrics(SM_CYICON) // 2
        hwnd = user32.GetDesktopWindow()
        hdc = user32.GetWindowDC(hwnd)
        try:
            cursor = POINT()
            if user32.GetCursorPos(ctypes.byref(cursor)) == 0:
                return

            error_icon = user32.LoadIconW(None, _make_resource_id(IDI_ERROR))
            warning_icon = user32.LoadIconW(None, _make_resource_id(IDI_WARNING))

            user32.DrawIcon(hdc, cursor.x - ix, cursor.y - iy, error_icon)

            screen_width = user32.GetSystemMetrics(SM_CXSCREEN)
            screen_height = user32.GetSystemMetrics(SM_CYSCREEN)
            threshold = int(10 / (self._times / 500.0 + 1) + 1)
            if threshold < 1:
                threshold = 1

            if random.randrange(threshold) == 0:
                x = random.randrange(max(1, screen_width))
                y = random.randrange(max(1, screen_height))
                user32.DrawIcon(hdc, x, y, warning_icon)
        finally:
            user32.ReleaseDC(hwnd, hdc)

    def _loop(self):
        while not self._stop_event.wait(self._interval):
            self._times += 1
            self._draw_once()

    def set_interval(self, interval_ms: int):
        self._interval = max(interval_ms / 1000.0, 0.01)

    def start(self, interval_ms: int = 5000):
        if self._running:
            self.set_interval(interval_ms)
            return
        self.set_interval(interval_ms)
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._running = True
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._running = False
        self._thread = None


_effect = _DrawIconEffect()


def start(interval_ms: int = 5000):
    """Start the drawicon effect."""
    _effect.start(interval_ms)


def stop():
    """Stop the drawicon effect."""
    _effect.stop()


def setinterval(interval_ms: int):
    """Update the drawicon effect interval in milliseconds."""
    _effect.set_interval(interval_ms)
