from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QLineEdit
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import apps_utils
from core.theme import GOLD, BLOOD_RED, MIDNIGHT_BLUE, GREEN, YELLOW, RED


class AppsIntelligencePage(QWidget):
    def __init__(self):
        super().__init__()
        self.all_apps = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Apps & Software Intelligence")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        refresh_btn = QPushButton("🔄 Scan Installed Apps")
        refresh_btn.clicked.connect(self.load_apps)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search app name...")
        self.search_box.textChanged.connect(self.apply_filter)
        filter_row.addWidget(self.search_box)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Critical", "Daily Use", "Bloatware", "Uncategorized"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        filter_row.addWidget(self.filter_combo)
        layout.addLayout(filter_row)

        chart_title = QLabel("Importance Score Distribution")
        chart_title.setObjectName("SectionTitle")
        layout.addWidget(chart_title)
        self.chart_container = QVBoxLayout()
        layout.addLayout(self.chart_container)

        table_title = QLabel("Installed Applications")
        table_title.setObjectName("SectionTitle")
        layout.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["App Name", "Size (MB)", "Install Date", "Importance"])
        layout.addWidget(self.table)

        startup_title = QLabel("Startup Impact List (Windows Run Registry)")
        startup_title.setObjectName("SectionTitle")
        layout.addWidget(startup_title)
        self.startup_table = QTableWidget()
        self.startup_table.setColumnCount(2)
        self.startup_table.setHorizontalHeaderLabels(["Startup Item", "Command Path"])
        self.startup_table.setFixedHeight(160)
        layout.addWidget(self.startup_table)

        self.load_apps()

    def load_apps(self):
        self.all_apps = apps_utils.get_installed_apps()
        for app in self.all_apps:
            app["importance"] = apps_utils.classify_importance(app["name"])
        self.render_chart()
        self.apply_filter()
        self.load_startup()

    def render_chart(self):
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        counts = {"Critical": 0, "Daily Use": 0, "Bloatware": 0, "Uncategorized": 0}
        for app in self.all_apps:
            counts[app["importance"]] += 1

        fig = Figure(figsize=(6, 3), facecolor="#0D0D0D")
        ax = fig.add_subplot(111)
        colors = [RED, GREEN, BLOOD_RED, MIDNIGHT_BLUE]
        ax.bar(counts.keys(), counts.values(), color=colors)
        ax.tick_params(colors="#E8E8E8")
        ax.set_ylabel("App Count", color=GOLD)
        fig.patch.set_facecolor("#0D0D0D")
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(260)
        self.chart_container.addWidget(canvas)

    def apply_filter(self):
        search_text = self.search_box.text().lower()
        importance_filter = self.filter_combo.currentText()

        filtered = [
            a for a in self.all_apps
            if search_text in a["name"].lower()
            and (importance_filter == "All" or a["importance"] == importance_filter)
        ]

        self.table.setRowCount(len(filtered))
        for r, app in enumerate(filtered):
            self.table.setItem(r, 0, QTableWidgetItem(app["name"]))
            self.table.setItem(r, 1, QTableWidgetItem(str(app["size_mb"] or "N/A")))
            self.table.setItem(r, 2, QTableWidgetItem(app["install_date"]))
            imp_item = QTableWidgetItem(app["importance"])
            self.table.setItem(r, 3, imp_item)
        self.table.resizeColumnsToContents()

    def load_startup(self):
        items = apps_utils.get_startup_items()
        self.startup_table.setRowCount(len(items))
        for r, item in enumerate(items):
            self.startup_table.setItem(r, 0, QTableWidgetItem(item["name"]))
            self.startup_table.setItem(r, 1, QTableWidgetItem(item["command"]))
        self.startup_table.resizeColumnsToContents()