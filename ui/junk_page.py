import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import junk_utils
from core.theme import BLOOD_RED, GOLD


class JunkAnalyzerPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Junk / Temp File Analyzer")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        scan_btn = QPushButton("🔍 Scan Junk (Report Only)")
        scan_btn.clicked.connect(self.scan)
        header_row.addWidget(scan_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("⚠ Advisory only — nothing gets deleted automatically. Open the folder manually to clean.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        self.chart_container = QVBoxLayout()
        layout.addLayout(self.chart_container)

        table_title = QLabel("Breakdown")
        table_title.setObjectName("SectionTitle")
        layout.addWidget(table_title)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Category", "Size"])
        layout.addWidget(self.table)

        self.scan()

    def scan(self):
        report = junk_utils.scan_junk_report()

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