import os
import random
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QScrollArea, QGridLayout, QFrame, QButtonGroup, QRadioButton, QMessageBox
)
from PyQt6.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt6.QtCore import Qt, QTimer, QPointF, QSize
import psutil

from core.theme import BLOOD_RED, GOLD, MIDNIGHT_BLUE, BLACK
from core import wallpaper_utils, hardware_utils


# ============================================================
# Animation Canvases (lightweight, code-based — no video files)
# ============================================================

class BaseAnimatedCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(280)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.running = False

    def start(self):
        if not self.running:
            self.timer.start(50)  # ~20 FPS — low CPU by design
            self.running = True

    def stop(self):
        self.timer.stop()
        self.running = False

    def animate(self):
        self.update()


class ParticlesCanvas(BaseAnimatedCanvas):
    def __init__(self):
        super().__init__()
        self.particles = [
            {"pos": QPointF(random.randint(0, 700), random.randint(0, 300)),
             "vel": QPointF(random.uniform(-1, 1), random.uniform(-1, 1))}
            for _ in range(45)
        ]

    def animate(self):
        w, h = self.width() or 700, self.height() or 300
        for p in self.particles:
            p["pos"] += p["vel"]
            if p["pos"].x() <= 0 or p["pos"].x() >= w:
                p["vel"].setX(-p["vel"].x())
            if p["pos"].y() <= 0 or p["pos"].y() >= h:
                p["vel"].setY(-p["vel"].y())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(MIDNIGHT_BLUE))
        painter.setBrush(QColor(BLOOD_RED))
        painter.setPen(Qt.PenStyle.NoPen)
        for p in self.particles:
            painter.drawEllipse(p["pos"], 3, 3)


class MatrixRainCanvas(BaseAnimatedCanvas):
    def __init__(self):
        super().__init__()
        self.columns = 40
        self.drops = [random.randint(0, 20) for _ in range(self.columns)]

    def animate(self):
        self.drops = [(d + 1) % 25 for d in self.drops]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BLACK))
        w = self.width() or 700
        col_width = w / self.columns
        painter.setPen(QColor(GOLD))
        for i, drop in enumerate(self.drops):
            x = int(i * col_width)
            y = int(drop * 14)
            painter.drawText(x, y, "1" if random.random() > 0.5 else "0")


class WaveLinesCanvas(BaseAnimatedCanvas):
    def __init__(self):
        super().__init__()
        self.phase = 0

    def animate(self):
        self.phase += 0.15
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(BLACK))
        w, h = self.width() or 700, self.height() or 280
        painter.setPen(QColor(BLOOD_RED))
        points = []
        for x in range(0, w, 4):
            y = h / 2 + math.sin((x * 0.02) + self.phase) * 40
            points.append(QPointF(x, y))
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])


class StarfieldCanvas(BaseAnimatedCanvas):
    def __init__(self):
        super().__init__()
        self.stars = [
            {"pos": QPointF(random.randint(0, 700), random.randint(0, 300)),
             "speed": random.uniform(0.5, 2.5)}
            for _ in range(80)
        ]

    def animate(self):
        h = self.height() or 300
        for s in self.stars:
            s["pos"].setY(s["pos"].y() + s["speed"])
            if s["pos"].y() > h:
                s["pos"].setY(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BLACK))
        painter.setBrush(QColor(GOLD))
        painter.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:
            painter.drawEllipse(s["pos"], 1.5, 1.5)


ANIMATION_CLASS_MAP = {
    "particles": ParticlesCanvas,
    "matrix": MatrixRainCanvas,
    "waves": WaveLinesCanvas,
    "starfield": StarfieldCanvas,
}


# ============================================================
# Main Wallpaper Gallery Page
# ============================================================

class WallpaperPage(QWidget):
    def __init__(self):
        super().__init__()
        self.current_canvas = None
        self.overlay_active = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        title = QLabel("Wallpaper Gallery (Optional Module)")
        title.setObjectName("HeaderTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Choose a static image OR a lightweight animated style. Static wallpapers apply "
            "directly to your real Windows desktop. Animated styles run inside Prime PC Vitals "
            "by default (zero desktop-level cost) — 'Desktop Overlay Mode' is experimental."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # ---------------- Static Wallpaper Gallery ----------------
        static_title = QLabel("🖼 Static Wallpapers — Apply to Desktop")
        static_title.setObjectName("SectionTitle")
        layout.addWidget(static_title)

        static_scroll = QScrollArea()
        static_scroll.setWidgetResizable(True)
        static_scroll.setFixedHeight(220)
        static_content = QWidget()
        self.static_grid = QGridLayout(static_content)
        static_scroll.setWidget(static_content)
        layout.addWidget(static_scroll)

        self.load_static_gallery()

        # ---------------- Animated Wallpaper Selector ----------------
        anim_title = QLabel("🎞 Animated Styles (Lightweight, Canvas-Based)")
        anim_title.setObjectName("SectionTitle")
        layout.addWidget(anim_title)

        anim_row = QHBoxLayout()
        self.anim_group = QButtonGroup(self)
        presets = wallpaper_utils.list_animation_presets()
        for i, name in enumerate(presets):
            radio = QRadioButton(name)
            radio.setStyleSheet("color:#E8E8E8;")
            if i == 0:
                radio.setChecked(True)
            self.anim_group.addButton(radio, i)
            anim_row.addWidget(radio)
        self.anim_presets = presets
        layout.addLayout(anim_row)

        control_row = QHBoxLayout()
        self.enable_toggle = QCheckBox("Enable In-App Animation Preview")
        self.enable_toggle.stateChanged.connect(self.toggle_animation)
        control_row.addWidget(self.enable_toggle)

        self.overlay_toggle = QCheckBox("⚠ Experimental: Run on Real Desktop (Overlay Mode)")
        self.overlay_toggle.stateChanged.connect(self.toggle_overlay)
        control_row.addWidget(self.overlay_toggle)
        layout.addLayout(control_row)

        self.status_label = QLabel("Status: OFF")
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label)

        self.canvas_frame = QFrame()
        self.canvas_layout = QVBoxLayout(self.canvas_frame)
        layout.addWidget(self.canvas_frame)

        # Cheap periodic system-pressure check (not continuous heavy monitoring)
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_system_pressure)
        self.check_timer.start(10000)

        layout.addStretch()

    # ---------------- Static Gallery ----------------
    def load_static_gallery(self):
        images = wallpaper_utils.list_static_wallpapers()
        if not images:
            empty_label = QLabel(
                "No images found in assets/wallpapers/static/. Add your own .jpg/.png files there."
            )
            empty_label.setObjectName("Muted")
            self.static_grid.addWidget(empty_label, 0, 0)
            return

        for idx, path in enumerate(images):
            thumb_btn = QPushButton()
            thumb_btn.setFixedSize(150, 100)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                thumb_btn.setIcon(QIcon(pixmap))
                thumb_btn.setIconSize(QSize(140, 90))
            else:
                thumb_btn.setText(os.path.basename(path))
            thumb_btn.setToolTip(os.path.basename(path))
            thumb_btn.clicked.connect(lambda checked, p=path: self.apply_static(p))
            self.static_grid.addWidget(thumb_btn, idx // 4, idx % 4)

    def apply_static(self, path):
        success = wallpaper_utils.apply_static_wallpaper(path)
        if success:
            self.status_label.setText(f"✅ Desktop wallpaper set: {os.path.basename(path)}")
        else:
            self.status_label.setText("⚠ Could not set wallpaper (non-Windows OS or permission issue).")

    # ---------------- Animated Preview ----------------
    def get_selected_preset_key(self):
        checked_id = self.anim_group.checkedId()
        if checked_id < 0:
            return "particles"
        name = self.anim_presets[checked_id]
        return wallpaper_utils.ANIMATION_PRESETS[name]

    def toggle_animation(self, state):
        if state:
            if hardware_utils.is_low_end_pc():
                reply = QMessageBox.question(
                    self, "Low-End PC Detected",
                    "RAM < 8GB or integrated GPU detected.\n\n"
                    "Prime PC Vitals recommends a STATIC wallpaper for best performance.\n\n"
                    "Enable lightweight animation anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.enable_toggle.setChecked(False)
                    return

            self._spawn_canvas()
            self.status_label.setText("Status: ON (in-app preview)")
        else:
            self._teardown_canvas()
            self.status_label.setText("Status: OFF")

    def _spawn_canvas(self):
        self._teardown_canvas()
        preset_key = self.get_selected_preset_key()
        canvas_class = ANIMATION_CLASS_MAP.get(preset_key, ParticlesCanvas)
        self.current_canvas = canvas_class()
        self.canvas_layout.addWidget(self.current_canvas)
        self.current_canvas.start()

    def _teardown_canvas(self):
        if self.current_canvas:
            self.current_canvas.stop()
            if self.overlay_active:
                wallpaper_utils.detach_widget_from_desktop(self.current_canvas)
                self.overlay_active = False
            self.canvas_layout.removeWidget(self.current_canvas)
            self.current_canvas.deleteLater()
            self.current_canvas = None

    # ---------------- Experimental Desktop Overlay ----------------
    def toggle_overlay(self, state):
        if state:
            if not self.enable_toggle.isChecked():
                self.enable_toggle.setChecked(True)
                self.toggle_animation(True)

            confirm = QMessageBox.warning(
                self, "Experimental Feature",
                "Desktop Overlay Mode reparents the animation window behind your desktop icons "
                "(true animated wallpaper). This is EXPERIMENTAL and depends on your Windows "
                "shell version. It will safely fall back to in-app preview if unsupported.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm == QMessageBox.StandardButton.No:
                self.overlay_toggle.setChecked(False)
                return

            success = False
            if self.current_canvas:
                success = wallpaper_utils.attach_widget_to_desktop(self.current_canvas)

            if success:
                self.overlay_active = True
                self.status_label.setText("✅ Status: ON — Running on real desktop (Experimental Overlay)")
            else:
                self.overlay_toggle.setChecked(False)
                self.status_label.setText("⚠ Overlay not supported on this system — using in-app preview instead.")
        else:
            if self.current_canvas and self.overlay_active:
                wallpaper_utils.detach_widget_from_desktop(self.current_canvas)
            self.overlay_active = False
            self.status_label.setText("Status: ON (in-app preview)" if self.enable_toggle.isChecked() else "Status: OFF")

    # ---------------- RAM/Battery Pressure Auto-Pause ----------------
    def check_system_pressure(self):
        if not self.enable_toggle.isChecked() or not self.current_canvas:
            return
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        battery = psutil.sensors_battery()

        if cpu > 85 or ram > 85 or (battery and not battery.power_plugged and battery.percent < 20):
            self.current_canvas.stop()
            self.status_label.setText("⏸ Auto-paused (high system load / low battery)")
        elif not self.current_canvas.running:
            self.current_canvas.start()
            self.status_label.setText("Status: ON")

    def closeEvent(self, event):
        self._teardown_canvas()
        super().closeEvent(event)