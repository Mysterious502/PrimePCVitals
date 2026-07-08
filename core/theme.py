import os

# ============================================================
# BRANDING
# ============================================================
APP_NAME = "Prime PC Vitals"
BRAND_OWNER = "Product of Prime Evolution"
APP_TAGLINE = "Know Everything. Touch Nothing."
APP_VERSION = "1.0.0"

# ============================================================
# COLOR PALETTE
# ============================================================
BLOOD_RED = "#B00020"
BLACK = "#0D0D0D"
DARK_PANEL = "#151515"
MIDNIGHT_BLUE = "#1A1A40"
GOLD = "#D4AF37"
TEXT_LIGHT = "#E8E8E8"
TEXT_MUTED = "#9A9A9A"
GREEN = "#2ECC71"
YELLOW = "#F1C40F"
RED = "#E74C3C"

ICON_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")

DARK_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BLACK};
    color: {TEXT_LIGHT};
    font-family: 'Segoe UI';
    font-size: 10pt;
}}

QFrame#Card {{
    background-color: {DARK_PANEL};
    border: 1px solid {MIDNIGHT_BLUE};
    border-radius: 10px;
    padding: 10px;
}}

QLabel#HeaderTitle {{
    color: {GOLD};
    font-size: 18pt;
    font-weight: bold;
}}

QLabel#SectionTitle {{
    color: {GOLD};
    font-size: 13pt;
    font-weight: 600;
    margin-top: 10px;
}}

QLabel#Muted {{
    color: {TEXT_MUTED};
    font-size: 9pt;
}}

QPushButton {{
    background-color: {MIDNIGHT_BLUE};
    color: {TEXT_LIGHT};
    border: 1px solid {GOLD};
    border-radius: 6px;
    padding: 6px 14px;
}}

QPushButton:hover {{
    background-color: {BLOOD_RED};
    color: white;
}}

QPushButton:pressed {{
    background-color: {GOLD};
    color: {BLACK};
}}

QPushButton:checked {{
    background-color: {BLOOD_RED};
    color: white;
    font-weight: bold;
}}

QListWidget, QTableWidget {{
    background-color: {DARK_PANEL};
    border: 1px solid {MIDNIGHT_BLUE};
    gridline-color: {MIDNIGHT_BLUE};
    color: {TEXT_LIGHT};
}}

QHeaderView::section {{
    background-color: {MIDNIGHT_BLUE};
    color: {GOLD};
    padding: 4px;
    border: none;
}}

QScrollBar:vertical {{
    background: {BLACK};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {BLOOD_RED};
    border-radius: 5px;
}}

QProgressBar {{
    border: 1px solid {GOLD};
    border-radius: 6px;
    text-align: center;
    color: {TEXT_LIGHT};
    background-color: {DARK_PANEL};
}}

QProgressBar::chunk {{
    background-color: {BLOOD_RED};
    border-radius: 5px;
}}

QCheckBox, QRadioButton {{
    color: {TEXT_LIGHT};
}}

QLineEdit, QComboBox {{
    background-color: {DARK_PANEL};
    color: {TEXT_LIGHT};
    border: 1px solid {MIDNIGHT_BLUE};
    border-radius: 5px;
    padding: 4px;
}}
"""


def health_color(percent: float) -> str:
    """Higher percent = better health -> green/yellow/red"""
    if percent >= 70:
        return GREEN
    elif percent >= 40:
        return YELLOW
    return RED