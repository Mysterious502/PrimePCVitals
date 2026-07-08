import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QProgressBar, QStackedWidget,
    QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import system_utils, fast_scan_utils, disk_history_utils
from core.theme import GOLD, BLOOD_RED, MIDNIGHT_BLUE, GREEN
from ui.treemap_widget import TreemapWidget


class FolderScanThread(QThread):
    progress = pyqtSignal(int)
    finished_scan = pyqtSignal(list)

    def __init__(self, path, fast_mode=False):
        super().__init__()
        self.path = path
        self.fast_mode = fast_mode

    def run(self):
        if self.fast_mode:
            result = fast_scan_utils.fast_scan_top_folders(
                self.path, top_n=10, progress_callback=self.progress.emit
            )
        else:
            result = system_utils.scan_top_folders(
                self.path, top_n=10, progress_callback=self.progress.emit
            )
        self.finished_scan.emit(result)


class DiskManagerPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header = QLabel("Local Disk Manager")
        header.setObjectName("HeaderTitle")
        layout.addWidget(header)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        self.list_page = QWidget()
        self.list_layout = QVBoxLayout(self.list_page)
        self.stack.addWidget(self.list_page)

        self.detail_pages = {}
        self.refresh_disks()

    def refresh_disks(self):
        for i in reversed(range(self.list_layout.count())):
            w = self.list_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        for disk in system_utils.get_all_disks():
            self.list_layout.addWidget(self.build_disk_card(disk))
            disk_history_utils.save_daily_snapshot(disk)  # cheap, one row/day
        self.list_layout.addStretch()
        self.stack.setCurrentWidget(self.list_page)

    def build_disk_card(self, disk):
        card = QFrame()
        card.setObjectName("Card")
        layout = QHBoxLayout(card)

        info_layout = QVBoxLayout()
        name = QLabel(disk["device"])
        name.setStyleSheet("font-size:14pt; font-weight:bold;")
        info_layout.addWidget(name)

        detail = QLabel(
            f"{system_utils.bytes_to_human(disk['used'])} used of "
            f"{system_utils.bytes_to_human(disk['total'])} ({disk['percent_used']:.1f}%)"
        )
        detail.setObjectName("Muted")
        info_layout.addWidget(detail)

        bar = QProgressBar()
        bar.setValue(int(disk["percent_used"]))
        info_layout.addWidget(bar)
        layout.addLayout(info_layout, stretch=3)

        open_btn = QPushButton("Open Details ➜")
        open_btn.clicked.connect(lambda: self.open_disk_detail(disk))
        layout.addWidget(open_btn, stretch=1)
        return card

    def open_disk_detail(self, disk):
        key = disk["device"]
        if key not in self.detail_pages:
            page = DiskDetailPage(disk, back_callback=self.back_to_list)
            self.detail_pages[key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.detail_pages[key])

    def back_to_list(self):
        self.stack.setCurrentWidget(self.list_page)


class DiskDetailPage(QWidget):
    def __init__(self, disk, back_callback):
        super().__init__()
        self.disk = disk
        self.back_callback = back_callback
        self.last_scan_result = []

        outer_layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Disks")
        back_btn.clicked.connect(self.back_callback)
        top_row.addWidget(back_btn)
        top_row.addStretch()
        outer_layout.addLayout(top_row)

        title = QLabel(f"{disk['device']} — Detailed Analysis")
        title.setObjectName("HeaderTitle")
        outer_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        # ---- Donut Chart: Used vs Free ----
        self.content_layout.addWidget(self._section_title("Storage Usage (Used vs Free)"))
        self.content_layout.addWidget(self.make_donut_chart(disk))
        self.content_layout.addWidget(self.make_data_table(
            ["Type", "Size"],
            [
                ["Used", system_utils.bytes_to_human(disk["used"])],
                ["Free", system_utils.bytes_to_human(disk["free"])],
                ["Total", system_utils.bytes_to_human(disk["total"])],
            ]
        ))

        # ---- Disk History Trend Graph (daily snapshot based) ----
        self.content_layout.addWidget(self._section_title("Disk Usage Trend (Daily Snapshots)"))
        self.history_container = QVBoxLayout()
        self.content_layout.addLayout(self.history_container)
        self.render_history()

        # ---- On-demand Top Folder Scan ----
        scan_row = QHBoxLayout()
        scan_btn = QPushButton("🔍 Scan Top 10 Folders")
        scan_btn.clicked.connect(self.start_scan)
        scan_row.addWidget(scan_btn)

        self.fast_mode_toggle = QCheckBox("⚡ Fast Scan Mode (multithreaded)")
        self.fast_mode_toggle.setChecked(True)
        scan_row.addWidget(self.fast_mode_toggle)

        self.scan_progress = QProgressBar()
        scan_row.addWidget(self.scan_progress)
        self.content_layout.addLayout(scan_row)

        self.content_layout.addWidget(self._section_title("Top 10 Largest Folders"))
        self.bar_result_layout = QVBoxLayout()
        self.content_layout.addLayout(self.bar_result_layout)

        self.treemap_btn = QPushButton("🧩 Expand Treemap View")
        self.treemap_btn.clicked.connect(self.expand_treemap)
        self.treemap_btn.setEnabled(False)
        self.content_layout.addWidget(self.treemap_btn)

        self.treemap_container = QVBoxLayout()
        self.content_layout.addLayout(self.treemap_container)

        self.content_layout.addStretch()

    def _section_title(self, text):
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def make_donut_chart(self, disk):
        fig = Figure(figsize=(4, 3), facecolor="#0D0D0D")
        ax = fig.add_subplot(111)
        wedges, _ = ax.pie(
            [disk["used"], disk["free"]],
            colors=[BLOOD_RED, MIDNIGHT_BLUE],
            startangle=90,
            wedgeprops=dict(width=0.4, edgecolor="#0D0D0D")
        )
        ax.legend(wedges, ["Used", "Free"], loc="center", frameon=False, labelcolor=GOLD)
        fig.patch.set_facecolor("#0D0D0D")
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(280)
        return canvas

    def make_data_table(self, headers, rows):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(str(val)))
        table.resizeColumnsToContents()
        table.setFixedHeight(min(35 * (len(rows) + 1), 200))
        return table

    def render_history(self):
        while self.history_container.count():
            item = self.history_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        history = disk_history_utils.load_history(self.disk["device"])

        if len(history) < 2:
            note = QLabel("Not enough daily snapshots yet — trend will build up over days (one snapshot/day, near-zero cost).")
            note.setObjectName("Muted")
            self.history_container.addWidget(note)
            return

        fig = Figure(figsize=(6, 3), facecolor="#0D0D0D")
        ax = fig.add_subplot(111)
        dates = [h["date"][5:] for h in history]  # MM-DD
        percents = [h["percent_used"] for h in history]
        ax.plot(dates, percents, color=BLOOD_RED, marker="o", linewidth=2)
        ax.set_ylabel("Used %", color=GOLD)
        ax.tick_params(colors="#E8E8E8", rotation=45)
        fig.patch.set_facecolor("#0D0D0D")
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(260)
        self.history_container.addWidget(canvas)

        self.history_container.addWidget(self.make_data_table(
            ["Date", "Used %", "Used (GB)", "Free (GB)"],
            [[h["date"], f"{h['percent_used']:.1f}%", h["used_gb"], h["free_gb"]] for h in history[-10:]]
        ))

    def start_scan(self):
        self.scan_progress.setValue(0)
        self.treemap_btn.setEnabled(False)
        fast_mode = self.fast_mode_toggle.isChecked()
        self.thread = FolderScanThread(self.disk["mountpoint"], fast_mode=fast_mode)
        self.thread.progress.connect(self.scan_progress.setValue)
        self.thread.finished_scan.connect(self.show_scan_results)
        self.thread.start()

    def show_scan_results(self, folders):
        self.last_scan_result = folders
        while self.bar_result_layout.count():
            item = self.bar_result_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if not folders:
            self.bar_result_layout.addWidget(QLabel("No accessible folders found (permission denied)."))
            return

        fig = Figure(figsize=(6, 3.5), facecolor="#0D0D0D")
        ax = fig.add_subplot(111)
        names = [os.path.basename(f) or f for f, _ in folders]
        sizes = [s / (1024 ** 3) for _, s in folders]
        ax.barh(names[::-1], sizes[::-1], color=BLOOD_RED)
        ax.set_xlabel("Size (GB)", color=GOLD)
        ax.tick_params(colors="#E8E8E8")
        fig.patch.set_facecolor("#0D0D0D")
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(320)
        self.bar_result_layout.addWidget(canvas)

        self.bar_result_layout.addWidget(self.make_data_table(
            ["Folder Path", "Size"],
            [[f, system_utils.bytes_to_human(s)] for f, s in folders]
        ))

        self.treemap_btn.setEnabled(True)

    def expand_treemap(self):
        """Rendered only on click — never on default view (CPU-heavy otherwise)."""
        while self.treemap_container.count():
            item = self.treemap_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if self.last_scan_result:
            self.treemap_container.addWidget(TreemapWidget(self.last_scan_result))