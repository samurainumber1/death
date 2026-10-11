import sys
import math
import urllib.request
from collections import deque
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw, ImageOps
from winotify import Notification, audio


# -------------------- SETTINGS --------------------

APP_NAME = "Desktop Alerts"

ICON_URL = (
    "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/microsoft-defender.png"
    ""
)

FOLDER = Path(__file__).resolve().parent
SOURCE_FILE = FOLDER / "notification_source.img"
TRANSPARENT_ICON = FOLDER / "notification_icon_transparent.png"

# Background-removal tolerance. Increase slightly for a grey background.
BACKGROUND_TOLERANCE = 75


# -------------------- DOWNLOAD ICON --------------------

def download_icon():
    if SOURCE_FILE.exists():
        return

    request = urllib.request.Request(
        ICON_URL,
        headers={"User-Agent": "Mozilla/5.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()

        if not data:
            raise ValueError("The image download was empty.")

        SOURCE_FILE.write_bytes(data)

    except Exception as exc:
        raise RuntimeError(
            "Couldn't download the icon. Check your internet connection "
            "or save your image beside this script as "
            "'notification_source.img'."
        ) from exc


# -------------------- REMOVE BACKGROUND --------------------

def make_background_transparent(image):
    image = ImageOps.exif_transpose(image).convert("RGBA")
    image.thumbnail((512, 512), Image.Resampling.LANCZOS)

    width, height = image.size
    pixels = image.load()

    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]

    opaque_corners = [p for p in corners if p[3] > 200]

    # Already transparent around the edges; preserve the existing alpha.
    if not opaque_corners:
        return image

    background = tuple(
        int(median(p[channel] for p in opaque_corners))
        for channel in range(3)
    )

    def distance(x, y):
        pixel = pixels[x, y]
        return math.sqrt(
            sum((pixel[i] - background[i]) ** 2 for i in range(3))
        )

    # Flood-fill similar-coloured pixels connected to the image edges.
    visited = bytearray(width * height)
    queue = deque()

    def add_pixel(x, y):
        index = y * width + x

        if visited[index]:
            return

        pixel = pixels[x, y]

        if pixel[3] == 0:
            visited[index] = 1
            return

        if distance(x, y) <= BACKGROUND_TOLERANCE:
            visited[index] = 1
            queue.append((x, y))

    for x in range(width):
        add_pixel(x, 0)
        add_pixel(x, height - 1)

    for y in range(height):
        add_pixel(0, y)
        add_pixel(width - 1, y)

    while queue:
        x, y = queue.popleft()

        pixel = pixels[x, y]
        dist = distance(x, y)

        # Soften the edge rather than leaving a hard white outline.
        alpha_factor = min(1.0, dist / BACKGROUND_TOLERANCE)
        new_alpha = round(pixel[3] * alpha_factor)

        pixels[x, y] = (pixel[0], pixel[1], pixel[2], new_alpha)

        for nx, ny in (
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ):
            if 0 <= nx < width and 0 <= ny < height:
                add_pixel(nx, ny)

    return image


def get_transparent_icon():
    if TRANSPARENT_ICON.exists():
        return Image.open(TRANSPARENT_ICON).convert("RGBA")

    download_icon()

    try:
        with Image.open(SOURCE_FILE) as image:
            icon = make_background_transparent(image)
            icon.save(TRANSPARENT_ICON, "PNG")
    except Exception as exc:
        raise RuntimeError(
            "The downloaded image couldn't be processed. "
            "Try saving it as a PNG and using that image instead."
        ) from exc

    return icon


# -------------------- CREATE STATUS ICON --------------------

def create_status_icon(kind):
    base = get_transparent_icon()

    # Put the logo on a transparent 256 x 256 canvas.
    canvas = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    logo = ImageOps.contain(base, (210, 210), Image.Resampling.LANCZOS)

    # Keep padding around the logo for a clean appearance.
    canvas.alpha_composite(
        logo,
        ((256 - logo.width) // 2 - 5, (256 - logo.height) // 2 - 5),
    )

    draw = ImageDraw.Draw(canvas)

    # Official-looking status badge.
    center_x, center_y = 202, 202
    radius = 39

    colours = {
        "info": (0, 120, 212, 255),       # Windows-style blue
        "warning": (255, 185, 0, 255),   # Amber
        "error": (196, 43, 28, 255),     # Red
    }

    badge_colour = colours[kind]

    draw.ellipse(
        (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        ),
        fill=badge_colour,
        outline=(255, 255, 255, 255),
        width=6,
    )

    if kind == "info":
        # White "i"
        draw.ellipse(
            (center_x - 4, center_y - 23, center_x + 4, center_y - 15),
            fill="white",
        )
        draw.rounded_rectangle(
            (center_x - 4, center_y - 10, center_x + 4, center_y + 19),
            radius=3,
            fill="white",
        )

    elif kind == "warning":
        # Dark exclamation mark on an amber badge.
        draw.rounded_rectangle(
            (center_x - 4, center_y - 19, center_x + 4, center_y + 7),
            radius=3,
            fill=(45, 45, 45, 255),
        )
        draw.ellipse(
            (center_x - 4, center_y + 12, center_x + 4, center_y + 20),
            fill=(45, 45, 45, 255),
        )

    elif kind == "error":
        # White cross.
        draw.line(
            (
                center_x - 13, center_y - 13,
                center_x + 13, center_y + 13,
            ),
            fill="white",
            width=7,
        )
        draw.line(
            (
                center_x + 13, center_y - 13,
                center_x - 13, center_y + 13,
            ),
            fill="white",
            width=7,
        )

    icon_path = FOLDER / f"notification_{kind}.png"
    canvas.save(icon_path, "PNG")

    return icon_path


# -------------------- SHOW NOTIFICATION --------------------

def main():
    if len(sys.argv) != 4:
        print('Usage: py notify.py "title" "message" "info|warning|error"')
        raise SystemExit(1)

    title, message, kind = sys.argv[1:]
    kind = kind.lower()

    if kind not in {"info", "warning", "error"}:
        print("Type must be info, warning, or error.")
        raise SystemExit(1)

    try:
        icon_path = create_status_icon(kind)

        notification = Notification(
            app_id=APP_NAME,
            title=title,
            msg=message,
            icon=str(icon_path),
            duration="long",
        )

        notification.set_audio(audio.Default, loop=False)
        notification.show()

    except Exception as exc:
        print(f"Notification failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()