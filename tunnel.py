"""Tunnel effect helper for the memz."""

import ctypes
from ctypes import wintypes
import threading
import time

# Win32 constants
SRCCOPY = 0x00CC0020

# Win32 bindings
GetDesktopWindow = ctypes.windll.user32.GetDesktopWindow
GetWindowDC = ctypes.windll.user32.GetWindowDC
ReleaseDC = ctypes.windll.user32.ReleaseDC
GetWindowRect = ctypes.windll.user32.GetWindowRect
StretchBlt = ctypes.windll.gdi32.StretchBlt

class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG)]


class TunnelEffect:
    """Runs the tunnel effect for the memz on a loop."""
    
    def __init__(self):
        self.running = False
        self.interval = 0.1  # Seconds between frames.
        self.thread = None
        self.times = 0
        
    def tunnel(self):
        """Run the tunnel effect once."""
        try:
            hwnd = GetDesktopWindow()
            hdc = GetWindowDC(hwnd)
            rekt = RECT()
            GetWindowRect(hwnd, ctypes.byref(rekt))
            
            # Copy the desktop back onto itself, smaller and centered.
            StretchBlt(
                hdc,
                50, 50,
                rekt.right - 100,
                rekt.bottom - 100,
                hdc,
                0, 0,
                rekt.right,
                rekt.bottom,
                SRCCOPY
            )
            
            ReleaseDC(hwnd, hdc)
            return True
        except Exception as e:
            print(f"Tunnel effect error in the memz: {e}")
            return False
    
    def start(self, interval=0.1):
        """Start the loop."""
        if self.running:
            return
        
        self.interval = interval
        self.running = True
        self.times = 0
        self.thread = threading.Thread(target=self._tunnel_loop, daemon=True)
        self.thread.start()
    
    def _tunnel_loop(self):
        """Run the effect until stopped."""
        while self.running:
            self.tunnel()
            self.times += 1
            time.sleep(self.interval)
    
    def stop(self):
        """Stop the loop."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.times = 0
    
    def setTime(self, seconds):
        """Set the loop delay."""
        if seconds < 0.001:
            seconds = 0.001 
        self.interval = seconds
    
    def get_animation_time(self):
        """Return the current animation timing value."""
        return 200.0 / (self.times / 5.0 + 1) + 4


# Shared instance
_tunnel_instance = TunnelEffect()


def tunnel():
    """Run the effect once."""
    return _tunnel_instance.tunnel()


def start(interval=0.1):
    """Start the effect loop."""
    _tunnel_instance.start(interval)


def stop():
    """Stop the effect loop."""
    _tunnel_instance.stop()


def setTime(seconds):
    """Set the loop delay."""
    _tunnel_instance.setTime(seconds)


def get_instance():
    """Return the shared instance."""
    return _tunnel_instance
