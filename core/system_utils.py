import os
import platform
from datetime import datetime
import psutil


def get_all_disks():
    disks = []
    for part in psutil.disk_partitions(all=False):
        if os.name == "nt" and ("cdrom" in part.opts or part.fstype == ""):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent_used": usage.percent,
        })
    return disks


def bytes_to_human(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def scan_top_folders(root_path: str, top_n: int = 10, progress_callback=None):
    """
    On-demand scan only (not continuous). Future upgrade: NTFS MFT parsing
    (WizTree-style) for 10-20x speed on C: drive.
    """
    folder_sizes = {}
    try:
        top_level = [
            os.path.join(root_path, d) for d in os.listdir(root_path)
            if os.path.isdir(os.path.join(root_path, d))
        ]
    except (PermissionError, FileNotFoundError):
        return []

    for idx, folder in enumerate(top_level):
        total_size = 0
        for dirpath, _, filenames in os.walk(folder, onerror=lambda e: None):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except (OSError, FileNotFoundError):
                    continue
        folder_sizes[folder] = total_size
        if progress_callback:
            progress_callback(int((idx + 1) / max(len(top_level), 1) * 100))

    return sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)[:top_n]


def compute_prime_health_score(disks):
    if not disks:
        return 100
    avg_free_percent = sum(100 - d["percent_used"] for d in disks) / len(disks)
    return round(avg_free_percent)


def get_system_summary():
    return {
        "os": platform.system() + " " + platform.release(),
        "cpu": platform.processor(),
        "ram_total": bytes_to_human(psutil.virtual_memory().total),
        "ram_used_percent": psutil.virtual_memory().percent,
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
    }