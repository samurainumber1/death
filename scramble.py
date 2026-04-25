import random
import threading
import time

import win32com.client


class _ScrambleEffect:
    def __init__(self):
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._saved_positions = {}
        self._delay_seconds = 0.005
        self._times = 0

    def _get_desktop(self):
        shell = win32com.client.Dispatch("Shell.Application")
        desktop = shell.Namespace(0)
        return desktop, desktop.Items()

    def _save_layout(self):
        desktop, items = self._get_desktop()
        saved_positions = {}
        for item in items:
            pos = item.Position
            saved_positions[item.Name] = (pos.x, pos.y)
        self._saved_positions = saved_positions
        return desktop, items

    def _ensure_layout_saved(self):
        desktop, items = self._get_desktop()
        if not self._saved_positions:
            self._save_layout()
            desktop, items = self._get_desktop()
        return desktop, items

    def _scramble_worker(self):
        try:
            desktop, items = self._ensure_layout_saved()
            for _ in range(self._times):
                with self._lock:
                    if not self._running:
                        break
                    delay_seconds = self._delay_seconds

                for item in items:
                    x = random.randint(0, 1200)
                    y = random.randint(0, 700)
                    desktop.View.SetItemPosition(item, x, y)

                time.sleep(delay_seconds)
        finally:
            with self._lock:
                self._running = False
                self._thread = None

    def start(self, times: int, delay_ms: int = 5):
        with self._lock:
            self._times = max(1, int(times))
            self._delay_seconds = max(1, int(delay_ms)) / 1000.0
            if self._running:
                return
            self._running = True

        self._thread = threading.Thread(target=self._scramble_worker, daemon=True)
        self._thread.start()

    def restore(self):
        with self._lock:
            self._running = False
            thread = self._thread

        if thread is not None:
            thread.join(timeout=2.0)

        if not self._saved_positions:
            return

        desktop, items = self._get_desktop()
        for item in items:
            if item.Name in self._saved_positions:
                x, y = self._saved_positions[item.Name]
                desktop.View.SetItemPosition(item, x, y)

    def setdelay(self, delay_ms: int):
        with self._lock:
            self._delay_seconds = max(1, int(delay_ms)) / 1000.0


_effect = _ScrambleEffect()


def start(times: int, delay_ms: int = 5):
    """Scramble desktop icons a fixed number of times."""
    _effect.start(times, delay_ms)


def restore():
    """Restore the saved desktop icon layout."""
    _effect.restore()


def setdelay(delay_ms: int):
    """Update the scramble delay in milliseconds."""
    _effect.setdelay(delay_ms)
