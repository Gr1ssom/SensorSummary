# range_bar.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QBrush, QColor

class RangeBar(QWidget):
    """
    A custom horizontal bar showing:
      - a total range [min_val, max_val]
      - a hashed "good" sub-range
      - a bright marker for the current_value
    All sized a bit larger for visibility on a dark theme.
    """

    def __init__(self,
                 min_val=0.0,
                 max_val=100.0,
                 good_min=40.0,
                 good_max=60.0,
                 current_value=50.0,
                 parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.good_min = good_min
        self.good_max = good_max
        self.current_value = current_value

        # Increase height so it’s more visible
        self.setMinimumHeight(28)
        self.setMaximumHeight(36)

    def setRange(self, min_val, max_val):
        self.min_val = min_val
        self.max_val = max_val
        self.update()

    def setGoodRange(self, good_min, good_max):
        self.good_min = good_min
        self.good_max = good_max
        self.update()

    def setValue(self, value):
        self.current_value = value
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        bar_rect = self.rect().adjusted(2, 2, -2, -2)

        # Dark background for the bar
        painter.setBrush(QColor("#2A2A2A"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(bar_rect)

        def clamp(x, a, b):
            return max(a, min(b, x))

        total_range = self.max_val - self.min_val
        if total_range <= 0:
            total_range = 1e-6

        # Hashed "good" region
        gmin = clamp(self.good_min, self.min_val, self.max_val)
        gmax = clamp(self.good_max, self.min_val, self.max_val)
        frac_gmin = (gmin - self.min_val) / total_range
        frac_gmax = (gmax - self.min_val) / total_range

        gxmin = bar_rect.left() + frac_gmin * bar_rect.width()
        gxmax = bar_rect.left() + frac_gmax * bar_rect.width()

        hashed_rect = QRectF(gxmin, bar_rect.top(),
                             gxmax - gxmin, bar_rect.height())

        hashed_brush = QBrush(QColor("#666666"), Qt.BrushStyle.Dense4Pattern)
        painter.setBrush(hashed_brush)
        painter.drawRect(hashed_rect)

        # Marker for current_value
        val = clamp(self.current_value, self.min_val, self.max_val)
        frac_val = (val - self.min_val) / total_range
        cur_x = bar_rect.left() + frac_val * bar_rect.width()

        marker_width = 8
        marker_height = bar_rect.height() + 4
        marker_rect = QRectF(cur_x - (marker_width/2),
                             bar_rect.center().y() - (marker_height/2),
                             marker_width,
                             marker_height)

        painter.setBrush(QColor("#00FF00"))  # bright green marker
        painter.drawRoundedRect(marker_rect, 3, 3)

        painter.end()
