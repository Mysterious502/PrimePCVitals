import os
import glob


def get_dir_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path, onerror=lambda e: None):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except (OSError, FileNotFoundError):
                continue
    return total


def scan_junk_report():
    """Report only — no delete. User acts manually."""
    report = {}

    temp_path = os.environ.get("TEMP", "")
    if temp_path and os.path.exists(temp_path):
        report["Windows Temp"] = get_dir_size(temp_path)

    prefetch_path = r"C:\Windows\Prefetch"
    if os.path.exists(prefetch_path):
        report["Prefetch Cache"] = get_dir_size(prefetch_path)

    recycle_bin = r"C:\$Recycle.Bin"
    if os.path.exists(recycle_bin):
        try:
            report["Recycle Bin"] = get_dir_size(recycle_bin)
        except PermissionError:
            report["Recycle Bin"] = 0

    report.update(scan_browser_data())
    return report


def scan_browser_data():
    """Read-only size report for browser cache/cookies/history."""
    user_home = os.path.expanduser("~")
    browsers = {
        "Chrome Cache": os.path.join(user_home, r"AppData\Local\Google\Chrome\User Data\Default\Cache"),
        "Edge Cache": os.path.join(user_home, r"AppData\Local\Microsoft\Edge\User Data\Default\Cache"),
        "Firefox Cache": os.path.join(user_home, r"AppData\Local\Mozilla\Firefox\Profiles"),
    }
    result = {}
    for name, path in browsers.items():
        if os.path.exists(path):
            result[name] = get_dir_size(path)
    return result


def bytes_to_human(n):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"