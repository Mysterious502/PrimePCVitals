import os
from collections import Counter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QProgressBar, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import image_utils
from core.theme import BLOOD_RED, GOLD, MIDNIGHT_BLUE


class ImageScanThread(QThread):
    progress = pyqtSignal(int)
    finished_scan = pyqtSignal(list, dict)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        results, duplicates = image_utils.scan_images(self.path, self.progress.emit)
        self.finished_scan.emit(results, duplicates)


class ImageManagerPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Image Manager")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        choose_btn = QPushButton("📁 Choose Folder & Scan")
        choose_btn.clicked.connect(self.choose_folder)
        header_row.addWidget(choose_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("Manual one-time scan (hash-based duplicates) — not a continuous background process.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        chart_title = QLabel("Category Breakdown")
        chart_title.setObjectName("SectionTitle")
        layout.addWidget(chart_title)
        self.chart_container = QVBoxLayout()
        layout.addLayout(self.chart_container)

        dup_title = QLabel("Duplicate Images Found (Exact Hash Match)")
        dup_title.setObjectName("SectionTitle")
        layout.addWidget(dup_title)
        self.dup_table = QTableWidget()
        self.dup_table.setColumnCount(2)
        self.dup_table.setHorizontalHeaderLabels(["Hash Group", "Duplicate File Paths"])
        layout.addWidget(self.dup_table)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.progress_bar.setValue(0)
            self.thread = ImageScanThread(folder)
            self.thread.progress.connect(self.progress_bar.setValue)
            self.thread.finished_scan.connect(self.show_results)
            self.thread.start()

    def show_results(self, results, duplicates):
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        categories = Counter(r["category"] for r in results)
        if categories:
            fig = Figure(figsize=(6, 3), facecolor="#0D0D0D")
            ax = fig.add_subplot(111)
            ax.bar(categories.keys(), categories.values(), color=BLOOD_RED)
            ax.set_ylabel("Image Count", color=GOLD)
            ax.tick_params(colors="#E8E8E8")
            fig.patch.set_facecolor("#0D0D0D")
            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(260)
            self.chart_container.addWidget(canvas)

        self.dup_table.setRowCount(len(duplicates))
        for r, (h, paths) in enumerate(duplicates.items()):
            self.dup_table.setItem(r, 0, QTableWidgetItem(h[:10] + "..."))
            self.dup_table.setItem(r, 1, QTableWidgetItem("\n".join(paths)))
        self.dup_table.resizeColumnsToContents()
        self.dup_table.resizeRowsToContents()