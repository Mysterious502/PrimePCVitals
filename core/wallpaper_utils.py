import os
import ctypes
from ctypes import wintypes

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "wallpapers", "static")
os.makedirs(STATIC_DIR, exist_ok=True)

SPI_SETDESKWALLPAPER = 20
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDCHANGE = 0x02

# ============================================================
# Animation Preset Catalog (code-based, zero video decoding cost)
# ============================================================
ANIMATION_PRESETS = {
    "Particles (Blood Drift)": "particles",
    "Matrix Rain (Gold Code)": "matrix",
    "Wave Lines (Midnight Pulse)": "waves",
    "Starfield (Deep Space)": "starfield",
}


def list_static_wallpapers():
    """Returns list of full paths to bundled/user-added static wallpaper images."""
    if not os.path.exists(STATIC_DIR):
        return []
    valid_ext = (".jpg", ".jpeg", ".png", ".bmp")
    return sorted([
        os.path.join(STATIC_DIR, f) for f in os.listdir(STATIC_DIR)
        if f.lower().endswith(valid_ext)
    ])


def list_animation_presets():
    return list(ANIMATION_PRESETS.keys())


def apply_static_wallpaper(image_path):
    """
    Sets the actual Windows desktop wallpaper — user-triggered, reversible
    OS setting (not a delete/install action, stays within advisory philosophy).
    """
    if os.name != "nt" or not os.path.exists(image_path):
        return False
    try:
        abs_path = os.path.abspath(image_path)
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, abs_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        return bool(result)
    except Exception:
        return False


# ============================================================
# EXPERIMENTAL: Real Desktop Animated Overlay (WorkerW technique)
# Off by default. If it fails for any reason (OS version mismatch,
# shell changes, etc.) it fails SILENTLY and falls back to in-app
# animation only — app never crashes because of this.
# ============================================================

def find_workerw_handle():
    """Locates the hidden WorkerW window behind desktop icons."""
    try:
        user32 = ctypes.windll.user32
        progman = user32.FindWindowW("Progman", None)
        user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0x0, 1000, None)

        result = []

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

        def enum_windows_proc(hwnd, lParam):
            shell_view = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
            if shell_view:
                workerw = user32.FindWindowExW(0, hwnd, "WorkerW", None)
                if workerw:
                    result.append(workerw)
            return True

        user32.EnumWindows(WNDENUMPROC(enum_windows_proc), 0)
        return result[0] if result else None
    except Exception:
        return None


def attach_widget_to_desktop(qwidget):
    """
    Reparents a QWidget behind desktop icons (true animated wallpaper).
    Returns True on success, False if unsupported — caller must handle
    fallback gracefully (this NEVER raises to keep app crash-safe).
    """
    try:
        workerw = find_workerw_handle()
        if not workerw:
            return False
        hwnd = int(qwidget.winId())
        ctypes.windll.user32.SetParent(hwnd, workerw)
        return True
    except Exception:
        return False


def detach_widget_from_desktop(qwidget):
    """Reverts widget back to a normal top-level window (safe cleanup)."""
    try:
        ctypes.windll.user32.SetParent(int(qwidget.winId()), 0)
        return True
    except Exception:
        return False