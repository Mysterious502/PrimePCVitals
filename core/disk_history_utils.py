import os
import json
from datetime import datetime, date

HISTORY_DIR = os.path.join(os.path.expanduser("~"), "PrimeVitalsData", "disk_history")
os.makedirs(HISTORY_DIR, exist_ok=True)


def _history_file(drive_name):
    safe_name = drive_name.strip(":\\/")
    return os.path.join(HISTORY_DIR, f"{safe_name}_history.json")


def load_history(drive_name):
    path = _history_file(drive_name)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_daily_snapshot(disk_info):
    """
    Only saves ONE snapshot per day (few KB JSON). No continuous logging —
    this gives trend graphs almost for free, resource-wise.
    """
    drive_name = disk_info["device"]
    history = load_history(drive_name)
    today_str = date.today().isoformat()

    if history and history[-1]["date"] == today_str:
        # Already logged today — update it instead of duplicating
        history[-1] = {
            "date": today_str,
            "used_gb": round(disk_info["used"] / (1024 ** 3), 2),
            "free_gb": round(disk_info["free"] / (1024 ** 3), 2),
            "percent_used": disk_info["percent_used"],
        }
    else:
        history.append({
            "date": today_str,
            "used_gb": round(disk_info["used"] / (1024 ** 3), 2),
            "free_gb": round(disk_info["free"] / (1024 ** 3), 2),
            "percent_used": disk_info["percent_used"],
        })

    # Keep last 90 days only — bounded file size
    history = history[-90:]

    with open(_history_file(drive_name), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    return history