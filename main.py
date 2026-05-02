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
from ctypes import wintypes
import pieces
import tunnel
import drawicon
import invert
import shaker

pygame.mixer.init()

# Tk setup
root = tk.Tk()
root.withdraw()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Main settings
window_width, window_height = 340, 120

MAX_ERROR_WINDOWS = 1400  # Soft cap so death does not bog down the PC.

last_beep_time = 0
stage = 1  # Current stage, from 1 to 15.
running = True
start_time = None

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

# Assets
script_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(script_dir, "assets")
icon_files = {
    "error": os.path.join(assets_dir, "error.png"),
    "warning": os.path.join(assets_dir, "warning.png"),
    "info": os.path.join(assets_dir, "info.png"),
    "death": os.path.join(assets_dir, "death.png"),
}

loaded_icons = {}
for key, path in icon_files.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f"Icon file not found: {path}")
    img = Image.open(path).resize((32, 32), Image.Resampling.LANCZOS)
    loaded_icons[key] = ImageTk.PhotoImage(img)

cursor_icon_path = os.path.join(assets_dir, "error.png")
cursor_img = Image.open(cursor_icon_path).resize((32, 32))
cursor_icon_photo = ImageTk.PhotoImage(cursor_img)

errors_path = os.path.join(assets_dir, "errors.json")
with open(errors_path, "r", encoding="utf-8") as errors_file:
    errors = [tuple(item) for item in json.load(errors_file)]

all_windows = []

# Sounds
sound_folder = assets_dir
sound_files = [os.path.join(sound_folder, f"error ({i}).wav") for i in range(1, 9)]
sounds = [pygame.mixer.Sound(f) for f in sound_files]

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
    if pieces.is_running():
        pieces.stop()
        return
    pieces_interval = PIECES_TIMER_SETTINGS.get(stage, 5000)
    pieces.timer(pieces_interval)
    pieces.start(pieces_interval)


def toggle_invert_debug():
    global invert_active
    invert_interval = INVERT_INTERVALS.get(stage, 5000)
    if invert_active:
        invert.stop()
        invert_active = False
        return
    try:
        invert.setinterval(invert_interval)
    except Exception:
        pass
    try:
        invert.start(invert_interval)
        invert_active = True
    except Exception:
        pass


def toggle_tunnel_debug():
    global tunnel_active
    tunnel_interval = TUNNEL_EFFECT_INTERVALS.get(stage, 1.0)
    if tunnel_active:
        try:
            tunnel.stop()
        except Exception:
            pass
        tunnel_active = False
        return
    try:
        tunnel.start(tunnel_interval)
        tunnel_active = True
    except Exception:
        pass


def toggle_drawicon_debug():
    global drawicon_active
    drawicon_interval = DRAWICON_INTERVALS.get(stage, 1000)
    if drawicon_active:
        drawicon.stop()
        drawicon_active = False
        return
    try:
        drawicon.start(drawicon_interval)
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
        shaker.stop()
        shaker_active = False
        return
    shaker.setIntensity(SHAKER_INTENSITIES.get(stage, 0.25))
    shaker.start()
    shaker_active = True

# Exit hotkeys

def f4_emergency_kill():
    """F4 stops everything immediately."""
    global drawicon_active, invert_active, tunnel_active, shaker_active
    try:
        pieces.stop()
    except Exception:
        pass
    try:
        tunnel.stop()
    except Exception:
        pass
    tunnel_active = False
    try:
        drawicon.stop()
    except Exception:
        pass
    drawicon_active = False
    try:
        invert.stop()
    except Exception:
        pass
    invert_active = False
    try:
        shaker.stop()
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
        pieces.stop()
    except Exception:
        pass
    try:
        tunnel.stop()
    except Exception:
        pass
    tunnel_active = False
    try:
        drawicon.stop()
    except Exception:
        pass
    drawicon_active = False
    try:
        invert.stop()
    except Exception:
        pass
    invert_active = False
    try:
        shaker.stop()
    except Exception:
        pass
    shaker_active = False

keyboard.add_hotkey("F7", f7_remove_immediately)
keyboard.add_hotkey("F4", f4_emergency_kill)

def set_stage(new_stage):
    """Move to a new stage."""
    global stage, drawicon_active, invert_active, tunnel_active, shaker_active
    if 1 <= new_stage <= 15 and new_stage != stage:
        stage = new_stage
        print(f"Stage {stage} enabled - Chaos level: {stage}/15")

        # Pieces effect
        if stage >= 3:
            pieces_interval = PIECES_TIMER_SETTINGS[stage]
            pieces.timer(pieces_interval)
            if not pieces.is_running():
                pieces.start(pieces_interval)
        elif stage < 3:
            try:
                pieces.stop()
            except Exception:
                pass

        # Invert starts at stage 4.
        if stage >= 4:
            invert_interval = INVERT_INTERVALS[stage]
            try:
                invert.setinterval(invert_interval)
            except Exception:
                pass
            try:
                invert.start(invert_interval)
                invert_active = True
            except Exception:
                pass
        elif stage < 4:
            try:
                invert.stop()
            except Exception:
                pass
            invert_active = False

        # Shaker runs from stage 3 through stage 13.
        if 3 <= stage < 14:
            shaker.setIntensity(SHAKER_INTENSITIES[stage])
            shaker.start()
            shaker_active = True
        else:
            try:
                shaker.stop()
            except Exception:
                pass
            shaker_active = False
        
        # Tunnel runs only from stage 5 through stage 15.
        if 5 <= stage <= 15:
            # Restart it with the new speed.
            try:
                tunnel.stop()
            except Exception:
                pass
            tunnel.start(TUNNEL_EFFECT_INTERVALS[stage])
            tunnel_active = True
        else:
            try:
                tunnel.stop()
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
                drawicon.start(drawicon_interval)
                drawicon_active = True
            except Exception:
                pass
        elif stage < 5:
            try:
                drawicon.stop()
            except Exception:
                pass
            drawicon_active = False


def start_scripted_timeline():
    """Start the normal staged timeline."""
    print("your time has come.")
    enable_floating_icons()
    root.after(10000, spawn_window_loop)
    root.after(10000, play_error_sound_loop)
    root.after(10000, lambda: set_stage(2))
    root.after(20000, lambda: set_stage(3))
    root.after(30000, lambda: set_stage(4))
    root.after(40000, lambda: set_stage(5))
    root.after(50000, lambda: set_stage(6))
    root.after(60000, lambda: set_stage(7))
    root.after(70000, lambda: set_stage(8))
    clearallerrors()
    root.after(80000, lambda: set_stage(9))
    root.after(90000, lambda: set_stage(10))
    root.after(100000, lambda: set_stage(11))
    root.after(110000, lambda: set_stage(12))
    root.after(120000, lambda: set_stage(13))
    clearallerrors()
    root.after(130000, lambda: set_stage(14))
    root.after(140000, lambda: set_stage(15))

# Warning dialog before death starts.
def start_confirmation():
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
        root.destroy()

    def open_debug():
        selection["mode"] = "debug"
        win.destroy()

    def maybe_reveal_debug(event):
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

# Main entry point
startup_mode = start_confirmation()

if startup_mode == "normal":
    start_scripted_timeline()
    root.mainloop()
elif startup_mode == "debug":
    open_debug_menu()
    root.mainloop()
else:
    print("death has been declined")
