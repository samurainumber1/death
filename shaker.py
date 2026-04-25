"""Screen shake effect helper."""

import ctypes
from ctypes import wintypes
import threading
import time
import random

# Win32 constants
SRCCOPY = 0x00CC0020

# Win32 bindings
GetDesktopWindow = ctypes.windll.user32.GetDesktopWindow
GetWindowDC = ctypes.windll.user32.GetWindowDC
ReleaseDC = ctypes.windll.user32.ReleaseDC
GetWindowRect = ctypes.windll.user32.GetWindowRect
BitBlt = ctypes.windll.gdi32.BitBlt


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG)]


class Shaker:
    """Runs a global screen shake effect on a loop."""

    def __init__(self):
        self.running = False
        self.thread = None
        self.interval = 1.0 / 60.0  # 60 FPS
        self.intensity = 0.0
        self.times = 0

    def shake(self):
        """Run one shake frame."""
        try:
            hwnd = GetDesktopWindow()
            hdc = GetWindowDC(hwnd)

            rect = RECT()
            GetWindowRect(hwnd, ctypes.byref(rect))

            strength = int(self.intensity * 30)

            x_offset = random.randint(-strength, strength)
            y_offset = random.randint(-strength, strength)

            # Copy screen back onto itself with offset (fake shake)
            BitBlt(
                hdc,
                x_offset,
                y_offset,
                rect.right,
                rect.bottom,
                hdc,
                0,
                0,
                SRCCOPY
            )

            ReleaseDC(hwnd, hdc)

            self.times += 1
            return True

        except Exception as e:
            print(f"Shaker error: {e}")
            return False

    def start(self):
        """Start shake loop at 60 FPS."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            start = time.time()

            self.shake()

            elapsed = time.time() - start
            sleep_time = self.interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        """Stop shaking."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.times = 0

    def setIntensity(self, value):
        """Set shake intensity (0.0 - 1.0)."""
        if value < 0:
            value = 0
        if value > 1:
            value = 1
        self.intensity = value

    def get_time(self):
        """Debug helper."""
        return self.times


# Shared instance
_shaker_instance = Shaker()


def start():
    """Start screen shake."""
    _shaker_instance.start()


def stop():
    """Stop screen shake."""
    _shaker_instance.stop()


def setIntensity(value):
    """Set shake intensity (0.0 - 1.0)."""
    _shaker_instance.setIntensity(value)


def get_instance():
    """Return shared instance."""
    return _shaker_instance