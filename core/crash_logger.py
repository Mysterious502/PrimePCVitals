import sys
import os
import traceback
from datetime import datetime

LOG_DIR = os.path.join(os.path.expanduser("~"), "PrimeVitalsData")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "crash_log.txt")


def install_global_exception_hook():
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n===== CRASH at {timestamp} =====\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        # Also print to console if running from source
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception