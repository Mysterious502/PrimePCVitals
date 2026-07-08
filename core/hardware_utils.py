import subprocess
import os
import psutil


def is_low_ram():
    return psutil.virtual_memory().total < 8 * (1024 ** 3)


def has_integrated_gpu_only():
    """Heuristic GPU check via WMIC — cheap, one-time call."""
    if os.name != "nt":
        return False
    try:
        result = subprocess.run(
            ["wmic", "path", "win32_VideoController", "get", "name"],
            capture_output=True, text=True, timeout=6,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = result.stdout.lower()
        integrated_signatures = ["intel(r) hd", "intel(r) uhd", "intel iris", "vega graphics", "radeon graphics"]
        dedicated_signatures = ["nvidia", "geforce", "rtx", "gtx", "radeon rx", "arc a"]

        has_integrated = any(sig in output for sig in integrated_signatures)
        has_dedicated = any(sig in output for sig in dedicated_signatures)

        return has_integrated and not has_dedicated
    except Exception:
        return False


def is_low_end_pc():
    """
    Combined heuristic: RAM < 8GB OR integrated-only GPU.
    Used to auto-suggest static wallpaper instead of animated.
    """
    return is_low_ram() or has_integrated_gpu_only()