from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QStackedWidget, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt

from core import system_utils
from core.theme import health_color, APP_NAME, BRAND_OWNER, APP_TAGLINE, APP_VERSION
from ui.disk_manager import DiskManagerPage
from ui.recommendation_page import RecommendationPage
from ui.apps_page import AppsIntelligencePage
from ui.security_page import SecurityCenterPage
from ui.junk_page import JunkAnalyzerPage
from ui.image_manager_page import ImageManagerPage
from ui.timeline_page import ActivityTimelinePage
from ui.reports_page import ReportsPage
from ui.wallpaper_page import WallpaperPage


class DashboardWindow(QMainWindow):
    def __init__(self, on_close_callback=None):
        super().__init__()
        self.on_close_callback = on_close_callback
        self.setWindowTitle(f"{APP_NAME} — {BRAND_OWNER}")

        # Dynamically fit window to available screen space
        screen = QGuiApplication.primaryScreen().availableGeometry()
        default_width = min(1250, screen.width() - 40)
        default_height = min(780, screen.height() - 40)
        self.resize(default_width, default_height)
        self.setMinimumSize(900, 600)
        self.move(
            screen.x() + (screen.width() - default_width) // 2,
            screen.y() + (screen.height() - default_height) // 2
        )

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- Sidebar ----------
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color:#101018; border-right:2px solid #D4AF37;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)

        title = QLabel("PRIME\nPC VITALS")
        title.setStyleSheet("font-size:16pt; font-weight:bold; color:#D4AF37;")
        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(20)

        self.nav_buttons = {}
        nav_items = [
            "Dashboard", "Disk Manager", "Junk Analyzer", "Recommendations",
            "Apps Intelligence", "Security Center", "Image Manager",
            "Activity Timeline", "Reports", "Wallpaper (Optional)"
        ]
        for item in nav_items:
            btn = QPushButton(item)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, name=item: self.switch_page(name))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[item] = btn

        sidebar_layout.addStretch()

        tagline_label = QLabel(APP_TAGLINE)
        tagline_label.setObjectName("Muted")
        tagline_label.setWordWrap(True)
        tagline_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(tagline_label)

        brand_label = QLabel(BRAND_OWNER)
        brand_label.setStyleSheet("color:#D4AF37; font-size:8pt; font-style:italic;")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(brand_label)
        sidebar_layout.addSpacing(10)

        about_btn = QPushButton("ℹ About")
        about_btn.clicked.connect(self.show_about)
        sidebar_layout.addWidget(about_btn)

        minimize_btn = QPushButton("Minimize to Tray")
        minimize_btn.clicked.connect(self.close)
        sidebar_layout.addWidget(minimize_btn)

        main_layout.addWidget(sidebar)

        # ---------- Pages (LAZY LOADED) ----------
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Factories — pages are NOT created here, only registered.
        # They get instantiated the first time the user navigates to them.
        # This fixes the startup freeze caused by every page's __init__
        # running blocking scans (Junk/Apps/Security) before the window
        # even appears on screen.
        self.page_factories = {
            "Disk Manager": DiskManagerPage,
            "Junk Analyzer": JunkAnalyzerPage,
            "Recommendations": RecommendationPage,
            "Apps Intelligence": AppsIntelligencePage,
            "Security Center": SecurityCenterPage,
            "Image Manager": ImageManagerPage,
            "Activity Timeline": ActivityTimelinePage,
            "Reports": ReportsPage,
            "Wallpaper (Optional)": WallpaperPage,
        }
        self.page_instances = {}
        self.page_index = {}

        # Only the Dashboard home page is built immediately (it's lightweight —
        # just disk usage % and a health score, no heavy scans).
        self.home_page = self.build_home_page()
        self.page_instances["Dashboard"] = self.home_page
        self.page_index["Dashboard"] = self.stack.addWidget(self.home_page)

        self.nav_buttons["Dashboard"].setChecked(True)

    def show_about(self):
        QMessageBox.information(
            self, f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n{APP_TAGLINE}\n\n{BRAND_OWNER}\n\n"
            "100% Offline • Read-Only • RAM-Conscious"
        )

    def build_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        header = QLabel("Prime Health Overview")
        header.setObjectName("HeaderTitle")
        header_row.addWidget(header)
        header_row.addStretch()

        refresh_btn = QPushButton("🔄 Refresh Snapshot")
        refresh_btn.clicked.connect(self.refresh_home)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        self.score_card = QFrame()
        self.score_card.setObjectName("Card")
        score_layout = QVBoxLayout(self.score_card)
        self.score_label = QLabel("--")
        self.score_label.setStyleSheet("font-size:42pt; font-weight:bold;")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_caption = QLabel("PRIME HEALTH SCORE (0-100)")
        score_caption.setObjectName("Muted")
        score_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_layout.addWidget(self.score_label)
        score_layout.addWidget(score_caption)
        layout.addWidget(self.score_card)

        disks_title = QLabel("Disks Overview")
        disks_title.setObjectName("SectionTitle")
        layout.addWidget(disks_title)
        self.disk_grid = QGridLayout()
        layout.addLayout(self.disk_grid)

        alerts_title = QLabel("Top Alerts & Recommendations")
        alerts_title.setObjectName("SectionTitle")
        layout.addWidget(alerts_title)
        self.alerts_list = QListWidget()
        layout.addWidget(self.alerts_list)

        layout.addStretch()
        self.refresh_home()
        return page

    def refresh_home(self):
        disks = system_utils.get_all_disks()
        score = system_utils.compute_prime_health_score(disks)
        self.score_label.setText(str(score))
        self.score_label.setStyleSheet(
            f"font-size:42pt; font-weight:bold; color:{health_color(score)};"
        )

        for i in reversed(range(self.disk_grid.count())):
            w = self.disk_grid.itemAt(i).widget()
            if w:
                w.setParent(None)

        for i, disk in enumerate(disks):
            card = self.build_disk_mini_card(disk)
            self.disk_grid.addWidget(card, i // 3, i % 3)

        self.alerts_list.clear()
        for alert in self.generate_alerts(disks)[:3]:
            self.alerts_list.addItem(QListWidgetItem(alert))

    def build_disk_mini_card(self, disk):
        card = QFrame()
        card.setObjectName("Card")
        card.setFixedHeight(110)
        layout = QVBoxLayout(card)

        name_label = QLabel(disk["device"])
        name_label.setStyleSheet("font-weight:bold; font-size:12pt;")
        layout.addWidget(name_label)

        percent = disk["percent_used"]
        used_label = QLabel(
            f"Used: {percent:.1f}%  |  {system_utils.bytes_to_human(disk['used'])} / "
            f"{system_utils.bytes_to_human(disk['total'])}"
        )
        used_label.setObjectName("Muted")
        layout.addWidget(used_label)

        color = health_color(100 - percent)
        bar = QFrame()
        bar.setFixedHeight(8)
        bar.setStyleSheet(f"background-color:{color}; border-radius:4px;")
        layout.addWidget(bar)
        return card

    def generate_alerts(self, disks):
        alerts = []
        for disk in disks:
            if disk["percent_used"] > 90:
                alerts.append(f"⚠ {disk['device']} is {disk['percent_used']:.0f}% full — cleanup recommended.")
            elif disk["percent_used"] > 75:
                alerts.append(f"⚠ {disk['device']} usage high ({disk['percent_used']:.0f}%) — monitor soon.")
        if not alerts:
            alerts.append("✅ All disks healthy. No urgent action needed.")
        return alerts

    def switch_page(self, name):
        for key, btn in self.nav_buttons.items():
            btn.setChecked(key == name)

        # Lazy-create the page on first visit only
        if name not in self.page_instances:
            page_class = self.page_factories[name]
            page = page_class()
            self.page_instances[name] = page
            self.page_index[name] = self.stack.addWidget(page)

        self.stack.setCurrentIndex(self.page_index[name])

        if name == "Dashboard":
            self.refresh_home()
        elif name == "Disk Manager":
            self.page_instances["Disk Manager"].refresh_disks()

    def closeEvent(self, event):
        """Active Mode -> Idle Mode: memory unload"""
        event.ignore()

        timeline_page = self.page_instances.get("Activity Timeline")
        if timeline_page and getattr(timeline_page, "tracker_thread", None):
            timeline_page.tracker_thread.stop()

        wallpaper_page = self.page_instances.get("Wallpaper (Optional)")
        if wallpaper_page:
            wallpaper_page._teardown_canvas()

        self.hide()
        if self.on_close_callback:
            self.on_close_callback()
