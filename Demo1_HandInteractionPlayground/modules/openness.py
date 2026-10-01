"""Step 4: map thumb-index distance continuously to cat size."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from modules.landmarks import draw_landmarks
from modules.pinch import thumb_index_distance


MIN_DISTANCE = 0.03
MAX_DISTANCE = 0.30
MIN_CAT_SCALE = 0.25
MAX_CAT_SCALE = 0.90


class OpennessCanvas(QWidget):
    def __init__(self, cat_path: Path):
        super().__init__()
        self.setMinimumSize(480, 360)
        self.cat = QPixmap(str(cat_path))
        self.cat_scale = MIN_CAT_SCALE
        self.distance = None
        self.hands = []

    def update_landmarks(self, hands):
        self.hands = hands
        if len(hands) != 1:
            self.distance = None
            self.update()
            return

        self.distance = thumb_index_distance(hands[0])
        amount = (self.distance - MIN_DISTANCE) / (MAX_DISTANCE - MIN_DISTANCE)
        amount = max(0.0, min(1.0, amount))
        self.cat_scale = MIN_CAT_SCALE + amount * (MAX_CAT_SCALE - MIN_CAT_SCALE)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("white"))

        maximum_size = min(self.width(), self.height())
        cat_size = int(maximum_size * self.cat_scale)
        scaled_cat = self.cat.scaled(
            cat_size, cat_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = (self.width() - scaled_cat.width()) // 2
        y = (self.height() - scaled_cat.height()) // 2
        painter.drawPixmap(x, y, scaled_cat)

        draw_landmarks(painter, self.hands, self.width(), self.height())

        if self.distance is not None:
            painter.setPen(QColor("#334155"))
            painter.drawText(18, 28, f"Thumb-index distance: {self.distance:.3f}")
