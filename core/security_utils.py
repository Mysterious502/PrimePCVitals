import subprocess
import json
import os


def _run_powershell(command, timeout=8):
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        return result.stdout.strip()
    except Exception:
        return ""


def check_defender():
    out = _run_powershell(
        "Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled | ConvertTo-Json"
    )
    try:
        data = json.loads(out)
        return bool(data.get("AntivirusEnabled")) and bool(data.get("RealTimeProtectionEnabled"))
    except Exception:
        return None


def check_firewall():
    out = _run_powershell(
        "Get-NetFirewallProfile | Select-Object Name,Enabled | ConvertTo-Json"
    )
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        return all(profile.get("Enabled") for profile in data)
    except Exception:
        return None


def check_windows_update():
    out = _run_powershell(
        "(Get-Service -Name wuauserv).Status"
    )
    return out.strip().lower() == "running" if out else None


def check_bitlocker():
    out = _run_powershell(
        "Get-BitLockerVolume -MountPoint C: | Select-Object -ExpandProperty ProtectionStatus"
    )
    if not out:
        return None
    return "1" in out


def check_uac():
    out = _run_powershell(
        r"(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System').EnableLUA"
    )
    return out.strip() == "1" if out else None


def check_controlled_folder_access():
    out = _run_powershell(
        "(Get-MpPreference).EnableControlledFolderAccess"
    )
    return out.strip() == "1" if out else None


def check_core_isolation():
    out = _run_powershell(
        r"(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -ErrorAction SilentlyContinue).Enabled"
    )
    return out.strip() == "1" if out else None


def check_windows_hello():
    out = _run_powershell(
        r"Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI' -ErrorAction SilentlyContinue"
    )
    return bool(out)


def check_restore_point_status():
    out = _run_powershell(
        "Get-ComputerRestorePoint | Measure-Object | Select-Object -ExpandProperty Count"
    )
    try:
        return int(out.strip())
    except Exception:
        return None


def get_battery_report_path():
    """Generates Windows built-in battery report — read-only, one click."""
    report_path = os.path.join(os.path.expanduser("~"), "PrimeVitalsData", "battery_report.html")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    try:
        subprocess.run(
            ["powercfg", "/batteryreport", "/output", report_path],
            capture_output=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        return report_path if os.path.exists(report_path) else None
    except Exception:
        return None


def run_full_security_scan():
    """One-time check-and-cache pattern — no continuous monitoring."""
    return {
        "Windows Defender": check_defender(),
        "Firewall (All Profiles)": check_firewall(),
        "Windows Update Service": check_windows_update(),
        "BitLocker (C:)": check_bitlocker(),
        "UAC Enabled": check_uac(),
        "Ransomware Protection (Controlled Folder Access)": check_controlled_folder_access(),
        "Core Isolation / Memory Integrity": check_core_isolation(),
        "Windows Hello Configured": check_windows_hello(),
    }


def compute_security_score(results: dict) -> int:
    valid = [v for v in results.values() if isinstance(v, bool)]
    if not valid:
        return 0
    return round((sum(1 for v in valid if v) / len(valid)) * 100)