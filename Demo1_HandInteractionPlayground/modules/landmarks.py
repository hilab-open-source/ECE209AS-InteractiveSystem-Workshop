"""Step 1: display only the landmarks that MediaPipe senses."""

import mediapipe as mp
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


def draw_landmarks(painter, hands, width, height):
    """Draw every detected hand using normalized landmark coordinates."""
    connections = mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
    for hand in hands:
        points = [QPointF(point.x * width, point.y * height) for point in hand]
        painter.setPen(QPen(QColor("#4ade80"), 4))
        for connection in connections:
            painter.drawLine(points[connection.start], points[connection.end])

        painter.setPen(QPen(QColor("#f8fafc"), 2))
        painter.setBrush(QColor("#fb7185"))
        for point in points:
            painter.drawEllipse(point, 6, 6)


class LandmarksView(QWidget):
    """Draw the sensed hand skeleton without showing the camera image."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(720, 480)
        self.hands = []

    def update_landmarks(self, hands):
        self.hands = hands
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#111827"))

        draw_landmarks(painter, self.hands, self.width(), self.height())
