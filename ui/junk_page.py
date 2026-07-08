import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem
)
from PyQt6.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import junk_utils
from core.theme import BLOOD_RED, GOLD


class JunkScanThread(QThread):
    """
    Runs the junk report scan on a background thread so the UI never
    freezes — even if Temp/Prefetch/Browser cache folders contain
    thousands of files.
    """
    finished_scan = pyqtSignal(dict)

    def run(self):
        report = junk_utils.scan_junk_report()
        self.finished_scan.emit(report)


class JunkAnalyzerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Junk / Temp File Analyzer")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.scan_btn = QPushButton("🔍 Scan Junk (Report Only)")
        self.scan_btn.clicked.connect(self.scan)
        header_row.addWidget(self.scan_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("⚠ Advisory only — nothing gets deleted automatically. Open the folder manually to clean.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        self.status_label = QLabel(
            "Click 'Scan Junk' to begin. This runs in the background and will not freeze the app."
        )
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label)

        self.chart_container = QVBoxLayout()
        layout.addLayout(self.chart_container)

        table_title = QLabel("Breakdown")
        table_title.setObjectName("SectionTitle")
        layout.addWidget(table_title)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Category", "Size"])
        layout.addWidget(self.table)

        # IMPORTANT: No auto-scan on page creation anymore.
        # Scanning Temp/Prefetch folders can take a while on systems with
        # large amounts of junk — running it automatically on page load
        # used to freeze the UI thread and made the app look "hung".
        # Now the scan only runs when the user explicitly clicks the button.

    def scan(self):
        if self.thread and self.thread.isRunning():
            return  # Prevent duplicate scans if user clicks rapidly

        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("⏳ Scanning...")
        self.status_label.setText(
            "⏳ Scanning Temp / Prefetch / Recycle Bin / Browser cache — "
            "this may take a few seconds on drives with lots of junk. The app will stay responsive."
        )

        self.thread = JunkScanThread()
        self.thread.finished_scan.connect(self.show_results)
        self.thread.start()

    def show_results(self, report):
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("🔍 Scan Junk (Report Only)")
        self.status_label.setText("✅ Scan complete.")

        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if report:
            fig = Figure(figsize=(6, 3.2), facecolor="#0D0D0D")
            ax = fig.add_subplot(111)
            labels = list(report.keys())
            sizes_gb = [v / (1024 ** 3) for v in report.values()]
            ax.barh(labels, sizes_gb, color=BLOOD_RED)
            ax.set_xlabel("Size (GB)", color=GOLD)
            ax.tick_params(colors="#E8E8E8")
            fig.patch.set_facecolor("#0D0D0D")
            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(300)
            self.chart_container.addWidget(canvas)

        self.table.setRowCount(len(report))
        for r, (cat, size) in enumerate(report.items()):
            self.table.setItem(r, 0, QTableWidgetItem(cat))
            self.table.setItem(r, 1, QTableWidgetItem(junk_utils.bytes_to_human(size)))
        self.table.resizeColumnsToContents()
