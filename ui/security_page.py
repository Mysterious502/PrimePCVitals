from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QFrame, QFileDialog
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from core import security_utils
from core.theme import GREEN, RED, YELLOW, GOLD


class SecurityCenterPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Security Center")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("🔄 Run Security Scan")
        refresh_btn.clicked.connect(self.run_scan)
        header_row.addWidget(refresh_btn)

        battery_btn = QPushButton("🔋 Generate Battery Report")
        battery_btn.clicked.connect(self.generate_battery_report)
        header_row.addWidget(battery_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("Read-only Windows API checks — cached, refresh manually. No real-time monitoring.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        self.score_frame = QFrame()
        self.score_frame.setObjectName("Card")
        score_layout = QVBoxLayout(self.score_frame)
        self.score_label = QLabel("--")
        self.score_label.setStyleSheet("font-size:36pt; font-weight:bold;")
        score_caption = QLabel("SECURITY SCORE")
        score_caption.setObjectName("Muted")
        score_layout.addWidget(self.score_label)
        score_layout.addWidget(score_caption)
        layout.addWidget(self.score_frame)

        chart_title = QLabel("Checklist Status Overview")
        chart_title.setObjectName("SectionTitle")
        layout.addWidget(chart_title)
        self.chart_container = QVBoxLayout()
        layout.addLayout(self.chart_container)

        table_title = QLabel("Detailed Checklist")
        table_title.setObjectName("SectionTitle")
        layout.addWidget(table_title)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Check", "Status"])
        layout.addWidget(self.table)

        self.status_label = QLabel("")
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label)

        self.run_scan()

    def run_scan(self):
        results = security_utils.run_full_security_scan()
        score = security_utils.compute_security_score(results)

        self.score_label.setText(str(score))
        color = GREEN if score >= 70 else YELLOW if score >= 40 else RED
        self.score_label.setStyleSheet(f"font-size:36pt; font-weight:bold; color:{color};")

        self.render_chart(results)

        self.table.setRowCount(len(results))
        for r, (check, status) in enumerate(results.items()):
            self.table.setItem(r, 0, QTableWidgetItem(check))
            if status is True:
                text, color = "✅ Enabled", GREEN
            elif status is False:
                text, color = "❌ Disabled", RED
            else:
                text, color = "⚠ Unknown / N/A", YELLOW
            item = QTableWidgetItem(text)
            self.table.setItem(r, 1, item)
        self.table.resizeColumnsToContents()

    def render_chart(self, results):
        while self.chart_container.count():
            item = self.chart_container.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        enabled = sum(1 for v in results.values() if v is True)
        disabled = sum(1 for v in results.values() if v is False)
        unknown = sum(1 for v in results.values() if v is None)

        fig = Figure(figsize=(5, 3), facecolor="#0D0D0D")
        ax = fig.add_subplot(111)
        labels = ["Enabled", "Disabled", "Unknown"]
        values = [enabled, disabled, unknown]
        colors = [GREEN, RED, YELLOW]
        ax.bar(labels, values, color=colors)
        ax.set_ylabel("Count", color=GOLD)
        ax.tick_params(colors="#E8E8E8")
        fig.patch.set_facecolor("#0D0D0D")
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(220)
        self.chart_container.addWidget(canvas)

    def generate_battery_report(self):
        path = security_utils.get_battery_report_path()
        if path:
            self.status_label.setText(f"✅ Battery report saved: {path}")
        else:
            self.status_label.setText("⚠ Could not generate battery report (desktop PC without battery?)")