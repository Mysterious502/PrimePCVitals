import os
import platform
from datetime import datetime

try:
    import winreg
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False

# Rule-based importance classification (no AI, near-zero cost)
CRITICAL_KEYWORDS = [
    "windows", "microsoft visual c++", "microsoft .net", "directx",
    "nvidia", "amd", "intel", "realtek", "chipset", "driver", "defender"
]
DAILY_KEYWORDS = [
    "chrome", "firefox", "edge", "office", "word", "excel", "powerpoint",
    "teams", "zoom", "discord", "whatsapp", "vlc", "spotify", "photoshop",
    "visual studio code", "notepad++", "steam"
]
BLOATWARE_KEYWORDS = [
    "toolbar", "coupon", "trial", "mcafee livesafe", "offer", "promo",
    "candy crush", "bing bar", "yahoo", "ask toolbar"
]


def _registry_apps(hive, path):
    apps = []
    if not IS_WINDOWS:
        return apps
    try:
        reg_key = winreg.OpenKey(hive, path)
    except FileNotFoundError:
        return apps

    for i in range(winreg.QueryInfoKey(reg_key)[0]):
        try:
            sub_key_name = winreg.EnumKey(reg_key, i)
            sub_key = winreg.OpenKey(reg_key, sub_key_name)
            name = winreg.QueryValueEx(sub_key, "DisplayName")[0]

            try:
                size_kb = winreg.QueryValueEx(sub_key, "EstimatedSize")[0]
                size_mb = round(size_kb / 1024, 1)
            except FileNotFoundError:
                size_mb = None

            try:
                install_date_raw = winreg.QueryValueEx(sub_key, "InstallDate")[0]
                install_date = f"{install_date_raw[:4]}-{install_date_raw[4:6]}-{install_date_raw[6:]}"
            except (FileNotFoundError, IndexError):
                install_date = "Unknown"

            apps.append({
                "name": name,
                "size_mb": size_mb,
                "install_date": install_date,
            })
        except (FileNotFoundError, OSError):
            continue
    return apps


def get_installed_apps():
    """Cheap registry reads — no filesystem scanning needed."""
    if not IS_WINDOWS:
        return []

    apps = []
    apps += _registry_apps(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    apps += _registry_apps(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    apps += _registry_apps(winreg.HKEY_CURRENT_USER,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")

    seen = set()
    unique_apps = []
    for app in apps:
        if app["name"] not in seen:
            seen.add(app["name"])
            unique_apps.append(app)

    return sorted(unique_apps, key=lambda x: x["name"].lower())


def classify_importance(app_name: str) -> str:
    lowered = app_name.lower()
    if any(k in lowered for k in BLOATWARE_KEYWORDS):
        return "Bloatware"
    if any(k in lowered for k in CRITICAL_KEYWORDS):
        return "Critical"
    if any(k in lowered for k in DAILY_KEYWORDS):
        return "Daily Use"
    return "Uncategorized"


def get_startup_items():
    """Very cheap registry read — Windows startup entries."""
    items = []
    if not IS_WINDOWS:
        return items

    locations = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ]

    for hive, path in locations:
        try:
            key = winreg.OpenKey(hive, path)
        except FileNotFoundError:
            continue
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                items.append({"name": name, "command": value})
                i += 1
            except OSError:
                break

    return items


def get_last_used_approx(file_path: str) -> str:
    """Zero-cost approximation using file metadata instead of persistent hooks."""
    try:
        ts = os.path.getatime(file_path)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (OSError, FileNotFoundError):
        return "Unknown"