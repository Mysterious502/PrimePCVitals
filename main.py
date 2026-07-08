import sys
import os
import gc
import socket

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle, QSplashScreen, QMessageBox
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QTimer

from core.theme import (
    DARK_STYLESHEET, ICON_PATH, GOLD, BLACK, BLOOD_RED,
    APP_NAME, BRAND_OWNER, APP_TAGLINE
)
from core.crash_logger import install_global_exception_hook
from ui.dashboard import DashboardWindow

# Install crash-safe global exception hook FIRST — offline app should
# never silently vanish; crashes get logged to PrimeVitalsData/crash_log.txt
install_global_exception_hook()

SINGLE_INSTANCE_PORT = 51477   # arbitrary local-only port for lock
_lock_socket = None


def already_running():
    """Prevents multiple tray instances eating extra RAM."""
    global _lock_socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
        s.listen(1)
        _lock_socket = s
        return False
    except OSError:
        return True


def build_splash():
    pixmap = QPixmap(460, 300)
    pixmap.fill(QColor(BLACK))
    painter = QPainter(pixmap)

    painter.setPen(QColor(BLOOD_RED))
    painter.drawRect(8, 8, 444, 284)

    painter.setPen(QColor(GOLD))
    painter.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
    painter.drawText(pixmap.rect().adjusted(0, -40, 0, 0), Qt.AlignmentFlag.AlignCenter, APP_NAME)

    painter.setFont(QFont("Segoe UI", 10))
    painter.setPen(QColor("#E8E8E8"))
    painter.drawText(pixmap.rect().adjusted(0, 20, 0, 0), Qt.AlignmentFlag.AlignCenter, APP_TAGLINE)

    painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
    painter.setPen(QColor(GOLD))
    painter.drawText(
        pixmap.rect().adjusted(0, 0, 0, -20),
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        BRAND_OWNER
    )

    painter.end()
    splash = QSplashScreen(pixmap)
    return splash


class PrimeVitalsApp:
    """
    Idle Mode  -> tray icon only  (~30-80MB RAM)
    Active Mode -> Dashboard loaded on demand, unloaded on close
    """

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setStyleSheet(DARK_STYLESHEET)

        self.dashboard = None

        icon = QIcon(ICON_PATH) if os.path.exists(ICON_PATH) else \
            self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        self.tray_icon = QSystemTrayIcon(icon, self.app)
        self.tray_icon.setToolTip(f"{APP_NAME} — Idle Mode")

        menu = QMenu()
        open_action = QAction("Open Dashboard", self.app)
        open_action.triggered.connect(self.open_dashboard)
        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.open_dashboard()

    def open_dashboard(self):
        if self.dashboard is None:
            self.dashboard = DashboardWindow(on_close_callback=self.unload_dashboard)
            self.dashboard.show()
            self.tray_icon.setToolTip(f"{APP_NAME} — Active Mode")
        else:
            self.dashboard.show()
            self.dashboard.activateWindow()

    def unload_dashboard(self):
        if self.dashboard is not None:
            self.dashboard.deleteLater()
            self.dashboard = None
            gc.collect()
            self.tray_icon.setToolTip(f"{APP_NAME} — Idle Mode")

    def exit_app(self):
        self.unload_dashboard()
        self.tray_icon.hide()
        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    if already_running():
        temp_app = QApplication(sys.argv)
        QMessageBox.warning(None, APP_NAME,
                             f"{APP_NAME} is already running in the system tray.")
        sys.exit(0)

    controller = PrimeVitalsApp()

    # Splash shown once on first Active Mode open (Idle Mode itself stays lightweight)
    splash = build_splash()
    splash.show()
    QTimer.singleShot(1200, splash.close)
    QTimer.singleShot(1200, controller.open_dashboard)

    controller.run()