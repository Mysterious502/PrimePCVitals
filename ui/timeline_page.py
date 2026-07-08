from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QCheckBox
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import timeline_utils
from core.theme import BLOOD_RED, GOLD


class ActivityTimelinePage(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker_thread = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Activity Timeline — Kis Time Kya Chala")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self.toggle = QCheckBox("Track App Usage Timeline (Opt-in)")
        self.toggle.stateChanged.connect(self.toggle_tracking)
        header_row.addWidget(self.toggle)
        layout.addLayout(header_row)

        subtitle = QLabel(
            "Default OFF. When ON: lightweight 30-sec psutil poll (no persistent hook/driver). "
            "When OFF: Prefetch-based 'last opened' fallback shown below (zero cost)."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        refresh_btn = QPushButton("🔄 Refresh View")
        refresh_btn.clicked.connect(self.refresh_view)
        layout.addWidget(refresh_btn)

        chart_title = QLabel("Timeline Graph")
        chart_title.setObjectName("SectionTitle")
        layout.addWidget(chart_title)
        self.chart_container = QVBoxLayout()
        layout.addLayout(self.chart_container)

        table_title = QLabel("App | Start | End | Duration")
        table_title.setObjectName("SectionTitle")
        layout.addWidget(table_title)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["App", "Start", "End", "Duration (min)"])
        layout.addWidget(self.table)

        self.refresh_view()

    def toggle_tracking(self, state):
        if state:
            self.tracker_thread = timeline_utils.TimelineTrackerThread(poll_seconds=30)
            self.tracker_thread.updated.connect(self.render_entries)
            self.tracker_thread.start()
        else:
            if self.tracker_thread:
                self.tracker_thread.stop()
                self.tracker_thread.wait(2000)
                self.tracker_thread = None
            self.refresh_view()

    def refresh_view(self):
        if self.toggle.isChecked():
            entries = timeline_utils.load_today_timeline()
            self.render_entries(entries)
        else:
            fallback = timeline_utils.get_prefetch_fallback()
            self.render_fallback(fallback)

    def render_entries(self, entries):
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if entries:
            fig = Figure(figsize=(7, 3.5), facecolor="#0D0D0D")
            ax = fig.add_subplot(111)

            for i, e in enumerate(entries[-15:]):  # last 15 for readability
                try:
                    start = datetime.strptime(e["start"], "%H:%M:%S")
                    end = datetime.strptime(e["end"], "%H:%M:%S")
                    start_num = start.hour + start.minute / 60
                    duration_num = max((end - start).total_seconds() / 3600, 0.02)
                    ax.broken_barh([(start_num, duration_num)], (i - 0.4, 0.8), facecolors=BLOOD_RED)
                except Exception:
                    continue

            ax.set_yticks(range(len(entries[-15:])))
            ax.set_yticklabels([e["app"] for e in entries[-15:]], color="#E8E8E8", fontsize=7)
            ax.set_xlabel("Time of Day (hour)", color=GOLD)
            ax.tick_params(colors="#E8E8E8")
            fig.patch.set_facecolor("#0D0D0D")
            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(320)
            self.chart_container.addWidget(canvas)

        self.table.setRowCount(len(entries))
        for r, e in enumerate(entries):
            self.table.setItem(r, 0, QTableWidgetItem(e["app"]))
            self.table.setItem(r, 1, QTableWidgetItem(e["start"]))
            self.table.setItem(r, 2, QTableWidgetItem(e["end"]))
            self.table.setItem(r, 3, QTableWidgetItem(str(e["duration_min"])))
        self.table.resizeColumnsToContents()

    def render_fallback(self, fallback):
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        info = QLabel("Tracking is OFF — showing Prefetch-based approximation (zero background cost).")
        info.setObjectName("Muted")
        self.chart_container.addWidget(info)

        self.table.setRowCount(len(fallback))
        self.table.setHorizontalHeaderLabels(["App", "Last Used (approx)", "-", "-"])
        for r, item in enumerate(fallback):
            self.table.setItem(r, 0, QTableWidgetItem(item["app"]))
            self.table.setItem(r, 1, QTableWidgetItem(item["last_used"]))
        self.table.resizeColumnsToContents()

    def closeEvent(self, event):
        if self.tracker_thread:
            self.tracker_thread.stop()
        super().closeEvent(event)