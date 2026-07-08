import os
import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from core.theme import GOLD


def _squarify(sizes, x, y, width, height):
    """Minimal squarified treemap layout algorithm."""
    if not sizes:
        return []
    total = sum(sizes)
    if total <= 0:
        return []

    rects = []
    sizes = sorted(sizes, reverse=True)

    def layout_row(row, x, y, width, height, horizontal):
        row_total = sum(s for _, s in row)
        if row_total <= 0:
            return
        if horizontal:
            row_height = row_total / width
            cx = x
            for name, s in row:
                w = s / row_height if row_height else 0
                rects.append((name, cx, y, w, row_height))
                cx += w
        else:
            row_width = row_total / height
            cy = y
            for name, s in row:
                h = s / row_width if row_width else 0
                rects.append((name, x, cy, row_width, h))
                cy += h

    remaining = list(sizes)
    cx, cy, cw, ch = x, y, width, height

    while remaining:
        horizontal = cw >= ch
        row = [remaining.pop(0)]
        # simple greedy grouping (fast, good-enough for visualization)
        while remaining and len(row) < 4:
            row.append(remaining.pop(0))
        layout_row(row, cx, cy, cw, ch, horizontal)
        consumed_ratio = sum(s for _, s in row) / total
        if horizontal:
            new_h = ch * consumed_ratio
            cy += new_h
            ch -= new_h
        else:
            new_w = cw * consumed_ratio
            cx += new_w
            cw -= new_w
        if ch <= 0 or cw <= 0:
            break

    return rects


class TreemapWidget(QWidget):
    """
    Rendered ONLY when user clicks 'Expand Treemap' — never on home/list view.
    Treemap rendering with thousands of files is CPU-heavy, so this stays
    fully on-demand as per design philosophy.
    """

    def __init__(self, folder_data):
        super().__init__()
        layout = QVBoxLayout(self)

        note = QLabel("Treemap View (rendered on-demand only)")
        note.setObjectName("Muted")
        layout.addWidget(note)

        fig = Figure(figsize=(7, 4.5), facecolor="#0D0D0D")
        ax = fig.add_subplot(111)
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.axis("off")
        fig.patch.set_facecolor("#0D0D0D")

        names = [os.path.basename(f) or f for f, _ in folder_data]
        sizes = [s for _, s in folder_data]

        rects = _squarify(sizes, 0, 0, 100, 100)
        palette = ["#B00020", "#D4AF37", "#1A1A40", "#8B0000", "#3B3B98", "#7A0C0C"]

        for i, (label, rx, ry, rw, rh) in enumerate(rects):
            color = palette[i % len(palette)]
            ax.add_patch(Rectangle((rx, ry), rw, rh, facecolor=color, edgecolor="#0D0D0D", linewidth=1.5))
            if rw > 8 and rh > 5:
                display_name = names[i] if i < len(names) else label
                ax.text(rx + rw / 2, ry + rh / 2, display_name[:14],
                         ha="center", va="center", fontsize=7, color="white", wrap=True)

        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(420)
        layout.addWidget(canvas)