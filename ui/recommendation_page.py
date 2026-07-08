from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from core import apps_utils, recommendation_engine


class RecommendationPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        header_row = QHBoxLayout()
        title = QLabel("Recommendation Engine — Kya Missing Hai?")
        title.setObjectName("HeaderTitle")
        header_row.addWidget(title)
        header_row.addStretch()
        scan_btn = QPushButton("🔍 Analyze My PC")
        scan_btn.clicked.connect(self.run_analysis)
        header_row.addWidget(scan_btn)
        layout.addLayout(header_row)

        subtitle = QLabel("100% Offline curated database — no internet, no AI model, zero RAM cost.")
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        scroll.setWidget(self.result_container)
        layout.addWidget(scroll)

        self.run_analysis()

    def run_analysis(self):
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        installed = [app["name"] for app in apps_utils.get_installed_apps()]
        missing = recommendation_engine.analyze_missing_tools(installed)

        if not missing:
            ok_label = QLabel("✅ Great! All common tool categories are covered on this PC.")
            ok_label.setObjectName("SectionTitle")
            self.result_layout.addWidget(ok_label)
            return

        for rec in missing:
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)

            cat_label = QLabel(f"⚠ Missing: {rec['category']}")
            cat_label.setStyleSheet("font-size:13pt; font-weight:bold; color:#D4AF37;")
            card_layout.addWidget(cat_label)

            msg_label = QLabel(rec["message"])
            msg_label.setObjectName("Muted")
            card_layout.addWidget(msg_label)

            suggestion_label = QLabel("Suggested: " + " | ".join(rec["suggestions"]))
            suggestion_label.setStyleSheet("color:#E8E8E8;")
            card_layout.addWidget(suggestion_label)

            self.result_layout.addWidget(card)

        self.result_layout.addStretch()