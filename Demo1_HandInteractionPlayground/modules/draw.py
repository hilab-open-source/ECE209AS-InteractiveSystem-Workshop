"""Step 2: draw a persistent stroke with the index fingertip."""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from modules.landmarks import draw_landmarks


class DrawCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 360)
        self.canvas = QImage(800, 600, QImage.Format.Format_RGB32)
        self.canvas.fill(QColor("white"))
        self.previous_point = None
        self.hands = []

    def update_landmarks(self, hands):
        self.hands = hands
        if len(hands) != 1:
            self.previous_point = None
            self.update()
            return

        index_tip = hands[0][8]
        point = QPoint(
            int(index_tip.x * self.canvas.width()),
            int(index_tip.y * self.canvas.height()),
        )

        if self.previous_point is not None:
            painter = QPainter(self.canvas)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#2563eb"), 7, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawLine(self.previous_point, point)
            painter.end()

        self.previous_point = point
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#e5e7eb"))
        scaled = self.canvas.scaled(
            self.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawImage(x, y, scaled)
        draw_landmarks(painter, self.hands, self.width(), self.height())
