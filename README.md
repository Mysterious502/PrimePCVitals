<div align="center">

# 🛡️ Prime PC Vitals

### *Know Everything. Touch Nothing.*

**A 100% Offline, Read-Only, RAM-Conscious Windows PC Health & Intelligence Suite**

*Product of **Prime Evolution***

---

[![Platform](https://img.shields.io/badge/Platform-Windows-0D0D0D?style=for-the-badge&logo=windows&logoColor=D4AF37)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.11+-B00020?style=for-the-badge&logo=python&logoColor=D4AF37)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-1A1A40?style=for-the-badge&logoColor=D4AF37)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-OFFLINE-B00020?style=for-the-badge&logoColor=D4AF37)](#)

[![Join Discord](https://img.shields.io/badge/Join%20our-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/zHdGrw7etB)

</div>

---

## 📌 What is Prime PC Vitals?

**Prime PC Vitals** is an offline Windows utility that **scans, analyzes, and visualizes** your PC's health, and provides **recommendations** — without automatically deleting, installing, or uninstalling anything. It's your PC's complete health dashboard: disk usage, security status, installed apps, junk files, duplicate images, activity timeline — all in one place, with graphs, and with **zero internet dependency**.

> ⚠️ **Important Philosophy:** This app only **Scans → Analyzes → Visualizes → Recommends**. Any destructive action (delete/install/uninstall) is always performed manually by the user, at their own discretion. The app is purely advisory.

---

## 🎯 Core Philosophy

| Principle | Description |
|---|---|
| **100% Offline** | No internet connection, no cloud sync, no telemetry — nothing at all. Everything runs entirely on the local machine. |
| **Read-Only / Advisory** | The app never deletes files, installs/uninstalls apps, or changes settings on its own (except for the user-triggered wallpaper apply, which is a reversible OS setting). |
| **RAM-Conscious by Design** | Built on a **Two-Mode Architecture** — Idle Mode (~30-80MB RAM, tray icon only) and Active Mode (heavy features load on-demand when the dashboard opens, and unload the moment it's closed). |

---

## ✨ Features

### 🏠 Dashboard (Home)
- Prime Health Score (0-100) — a combined score of Storage + Security + Performance
- Per-disk mini cards with color-coded health (green/yellow/red)
- Top 3 alerts & recommendations
- Manual refresh (no 24/7 background polling)

### 💽 Local Disk Manager
- Per-disk detailed page with donut chart (Used vs Free)
- Top 10 largest folders — Bar chart + data table
- **Fast Scan Mode** — multithreaded scanning (3-5x faster)
- **Experimental USN Journal enumeration** (Admin mode, instant file listing)
- **Treemap view** — renders only on-demand (not on default view)
- Daily snapshot disk history + trend graph (near-zero storage cost)

### 🧹 Junk / Temp File Analyzer
- Windows Temp, Prefetch cache, Recycle Bin size report
- Browser cache/cookies size report (Chrome, Edge, Firefox)
- **Report-only** — nothing auto-deletes, manual cleanup advised

### 💡 Recommendation Engine
- 100% offline curated database (bundled JSON)
- Detects missing tool categories (PDF reader, archive tool, media player, etc.)
- Suggests 1-2 free alternatives — zero AI, zero internet, instant results

### 📦 Apps & Software Intelligence
- Full installed apps list with size & install date
- Rule-based **Importance Score**: Critical / Daily Use / Bloatware / Uncategorized
- Startup impact list (Windows Run registry — cheap read)
- Filter & search by name/category

### 🔒 Security Center
- Windows Defender, Firewall, Windows Update, BitLocker, UAC status
- Extended checklist: Ransomware Protection, Core Isolation, Windows Hello
- Security Score gauge
- One-click Battery Health Report (`powercfg /batteryreport`)
- Manual refresh — no continuous background monitoring

### 🖼️ Image Manager
- Hash-based exact duplicate detector (lightweight, fast)
- Category sort: Screenshots / Camera / Downloaded / Wallpapers / Others
- Resolution + size stats
- Per-file EXIF metadata viewer
- Manual folder-select scan with progress bar

### ⏱️ Activity Timeline
- **Opt-in only** (default OFF)
- Lightweight 30-second `psutil` poll — no persistent driver/hook
- Gantt-style timeline graph (App | Start | End | Duration)
- OFF mode fallback: Prefetch-based "last opened" approximation (zero cost)

### 📤 Reports & Export
- Save full JSON snapshot locally
- Export complete HTML report (branded, styled)
- Simple file I/O — negligible resource cost

### 🎨 Wallpaper Gallery (Optional Module)
- **150 built-in static wallpapers included in the build** — ready to use out of the box, no downloads needed
- Static wallpaper gallery — apply directly to real Windows desktop
- 4 lightweight animated styles (Particles, Matrix Rain, Wave Lines, Starfield) — canvas-based, zero video decoding
- Experimental "Desktop Overlay Mode" — real animated wallpaper (auto-fallback if unsupported)
- Auto-pause on high CPU/RAM/low battery
- Auto-warns on low-end PCs (RAM < 8GB or integrated GPU only)

---

## 🖥️ System Requirements

- **OS:** Windows 10 / 11 (some features like BitLocker/Defender checks are Windows-only)
- **RAM:** Works on 4GB+ systems (Idle Mode uses ~30-80MB)
- **Python:** 3.11 or higher (only needed if running from source or building)
- **Disk Space:** ~150-250MB (app + dependencies + 150 bundled wallpapers)

---

## 🚀 Installation & Setup

### Option A: Run from Source (Developers)

```bash
# 1. Clone the repository
git clone https://github.com/Mysterious502/PrimePCVitals.git
cd PrimePCVitals

# 2. Create a virtual environment (STRONGLY recommended)
python -m venv venv

# 3. Activate the virtual environment
venv\Scripts\activate
# You should now see (venv) at the start of your terminal prompt

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
python main.py
```

---

## 🏗️ How to Build the `.exe` (Create a New Application Build)

If you've made changes to the code, or you're building your own `.exe` for the first time, follow these steps **exactly in order**:

### Step 1: Activate the Virtual Environment
```powershell
cd "path\to\PrimePCVitals"
venv\Scripts\activate
```
⚠️ **Make sure** you see `(venv)` at the start of your terminal prompt:
```
(venv) PS D:\PrimePCVitals>
```
If `(venv)` is not showing, the build will fail or produce a broken `.exe` (because PyInstaller won't be able to find PyQt6/matplotlib).

### Step 2: Confirm Dependencies (if building for the first time)
```powershell
pip install -r requirements.txt
```

### Step 3: Install PyInstaller (inside the venv)
```powershell
pip install pyinstaller
```

### Step 4: Clean Up Old Build Files (if rebuilding)
```powershell
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
```

### Step 5: Run the Build Command
```powershell
pyinstaller PrimePCVitals.spec
```

### Step 6: Find Your Final `.exe` Here
```
dist/PrimePCVitals.exe
```
Double-click it to test — if it runs correctly, this file is ready to be distributed.

> 💡 **Note:** The build includes 150 bundled static wallpapers (`assets/wallpapers/static/`), so the packaged `.exe` will be slightly larger than a minimal build — this is expected and by design.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

### Made by **Prime Evolution**

*"Know Everything. Touch Nothing."*

</div>