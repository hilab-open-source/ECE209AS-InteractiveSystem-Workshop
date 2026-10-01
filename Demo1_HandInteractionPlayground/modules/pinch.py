"""Step 3: interpret thumb-index distance as a pinch for dragging cubes."""

import math

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from modules.landmarks import draw_landmarks


# Change this value to make pinching more or less sensitive.
PINCH_THRESHOLD = 0.065


def thumb_index_distance(hand):
    thumb_tip = hand[4]
    index_tip = hand[8]
    return math.sqrt(
        (thumb_tip.x - index_tip.x) ** 2
        + (thumb_tip.y - index_tip.y) ** 2
        + (thumb_tip.z - index_tip.z) ** 2
    )


class PinchCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(480, 360)
        self.cubes = [
            {"x": 0.25, "y": 0.32, "size": 0.18, "color": "#ef4444"},
            {"x": 0.62, "y": 0.28, "size": 0.16, "color": "#3b82f6"},
            {"x": 0.48, "y": 0.68, "size": 0.20, "color": "#22c55e"},
        ]
        self.selected_cube = None
        self.was_pinching = False
        self.distance = None
        self.hands = []

    def update_landmarks(self, hands):
        self.hands = hands
        if len(hands) != 1:
            self.selected_cube = None
            self.was_pinching = False
            self.distance = None
            self.update()
            return

        hand = hands[0]
        index_tip = hand[8]
        self.distance = thumb_index_distance(hand)
        pinching = self.distance < PINCH_THRESHOLD

        if pinching and not self.was_pinching:  # IDLE -> PINCH / SELECT
            self.selected_cube = self.cube_at(index_tip.x, index_tip.y)
        if pinching and self.selected_cube is not None:  # SELECT -> DRAG
            self.selected_cube["x"] = index_tip.x
            self.selected_cube["y"] = index_tip.y
        if not pinching:  # DRAG -> RELEASE -> IDLE
            self.selected_cube = None

        self.was_pinching = pinching
        self.update()

    def cube_at(self, x, y):
        for cube in reversed(self.cubes):
            half = cube["size"] / 2
            if cube["x"] - half <= x <= cube["x"] + half and \
                    cube["y"] - half <= y <= cube["y"] + half:
                return cube
        return None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))

        for cube in self.cubes:
            self.draw_cube(painter, cube, cube is self.selected_cube)

        draw_landmarks(painter, self.hands, self.width(), self.height())

        if self.distance is not None:
            state = "PINCH / DRAG" if self.was_pinching else "IDLE"
            painter.setPen(QColor("#334155"))
            painter.drawText(18, 28, f"{state}   distance: {self.distance:.3f}")

    def draw_cube(self, painter, cube, selected):
        size = cube["size"] * min(self.width(), self.height())
        center_x = cube["x"] * self.width()
        center_y = cube["y"] * self.height()
        front = QRectF(center_x - size / 2, center_y - size / 2, size, size)
        offset = size * 0.22
        color = QColor(cube["color"])

        top = QPolygonF([
            front.topLeft(), front.topRight(),
            front.topRight() + QPointF(offset, -offset),
            front.topLeft() + QPointF(offset, -offset),
        ])
        side = QPolygonF([
            front.topRight(), front.bottomRight(),
            front.bottomRight() + QPointF(offset, -offset),
            front.topRight() + QPointF(offset, -offset),
        ])
        painter.setPen(QPen(QColor("#475569"), 3 if selected else 1))
        painter.setBrush(color.lighter(135))
        painter.drawPolygon(top)
        painter.setBrush(color.darker(125))
        painter.drawPolygon(side)
        painter.setBrush(color)
        painter.drawRect(front)
