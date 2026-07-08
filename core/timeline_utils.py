import os
import json
import psutil
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

DATA_DIR = os.path.join(os.path.expanduser("~"), "PrimeVitalsData", "timeline")
os.makedirs(DATA_DIR, exist_ok=True)


def _today_file():
    return os.path.join(DATA_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.json")


def load_today_timeline():
    path = _today_file()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_today_timeline(entries):
    with open(_today_file(), "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


class TimelineTrackerThread(QThread):
    """
    Opt-in only. Default OFF.
    Polls psutil.process_iter() every 30s — very cheap call, NO persistent
    hook/driver, NO continuous CPU/RAM graph rendering.
    """
    updated = pyqtSignal(list)

    def __init__(self, poll_seconds=30):
        super().__init__()
        self.poll_seconds = poll_seconds
        self._running = False
        self.active_sessions = {}   # {process_name: start_time}
        self.entries = load_today_timeline()

    def run(self):
        self._running = True
        while self._running:
            self._poll_once()
            self.updated.emit(self.entries)
            self.msleep(self.poll_seconds * 1000)

    def _poll_once(self):
        current_names = set()
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name:
                    current_names.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        now = datetime.now()

        # New processes started
        for name in current_names:
            if name not in self.active_sessions:
                self.active_sessions[name] = now

        # Processes that ended -> log to timeline
        ended = [name for name in self.active_sessions if name not in current_names]
        for name in ended:
            start = self.active_sessions.pop(name)
            duration_min = round((now - start).total_seconds() / 60, 1)
            if duration_min >= 0.5:  # ignore negligible blips
                self.entries.append({
                    "app": name,
                    "start": start.strftime("%H:%M:%S"),
                    "end": now.strftime("%H:%M:%S"),
                    "duration_min": duration_min,
                })
        if ended:
            save_today_timeline(self.entries)

    def stop(self):
        self._running = False
        # Flush any active sessions as "still running" on stop
        save_today_timeline(self.entries)


def get_prefetch_fallback():
    """
    OFF-mode fallback: Windows Prefetch folder mtimes approximate
    'last opened' — zero background cost.
    """
    prefetch_path = r"C:\Windows\Prefetch"
    results = []
    if not os.path.exists(prefetch_path):
        return results
    try:
        for f in os.listdir(prefetch_path):
            if f.endswith(".pf"):
                full_path = os.path.join(prefetch_path, f)
                mtime = os.path.getmtime(full_path)
                results.append({
                    "app": f.split("-")[0].replace(".pf", ""),
                    "last_used": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                })
    except PermissionError:
        pass
    return sorted(results, key=lambda x: x["last_used"], reverse=True)