from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit
from datetime import datetime

from core import system_utils, apps_utils, security_utils, junk_utils, reports_utils


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Reports & Export")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        export_json_btn = QPushButton("💾 Save JSON Snapshot")
        export_json_btn.clicked.connect(self.export_json)
        header_row.addWidget(export_json_btn)

        export_html_btn = QPushButton("📄 Export Full HTML Report")
        export_html_btn.clicked.connect(self.export_html)
        header_row.addWidget(export_html_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("All data stored locally — plain file I/O, negligible resource cost.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def gather_all_data(self):
        return {
            "System Summary": system_utils.get_system_summary(),
            "Disks": system_utils.get_all_disks(),
            "Installed Apps": apps_utils.get_installed_apps(),
            "Startup Items": apps_utils.get_startup_items(),
            "Security Checklist": security_utils.run_full_security_scan(),
            "Junk Report (bytes)": junk_utils.scan_junk_report(),
        }

    def export_json(self):
        data = self.gather_all_data()
        path = reports_utils.save_json_report("FullSystem", data)
        self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ JSON snapshot saved: {path}")

    def export_html(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save HTML Report", "PrimeVitalsReport.html", "HTML Files (*.html)")
        if save_path:
            data = self.gather_all_data()
            reports_utils.export_html_report(data, save_path)
            self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ HTML report exported: {save_path}")