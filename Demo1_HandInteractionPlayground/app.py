"""Hand Gesture Interaction Playground: a small HCI teaching prototype."""

import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from modules.draw import DrawCanvas
from modules.hand_tracking import HandTracker
from modules.landmarks import LandmarksView
from modules.openness import OpennessCanvas
from modules.pinch import PinchCanvas


ROOT = Path(__file__).resolve().parent


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Gesture Interaction Playground")
        self.resize(980, 720)

        self.tracker = HandTracker(ROOT / "assets" / "hand_landmarker.task")
        self.status = QLabel()
        self.status.setObjectName("status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.hide()

        self.panels = [
            LandmarksView(),
            DrawCanvas(),
            PinchCanvas(),
            OpennessCanvas(ROOT / "assets" / "cat.png"),
        ]
        self.panel_stack = QStackedWidget()
        for panel in self.panels:
            self.panel_stack.addWidget(panel)

        navigation = QHBoxLayout()
        button_group = QButtonGroup(self)
        button_group.setExclusive(True)
        for index, name in enumerate(["1. LANDMARKS", "2. DRAW", "3. PINCH", "4. OPENNESS"]):
            button = QPushButton(name)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self.change_step(i))
            button_group.addButton(button)
            navigation.addWidget(button)
            if index == 0:
                button.setChecked(True)

        view_layout = QGridLayout()
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.addWidget(self.panel_stack, 0, 0)
        view_layout.addWidget(
            self.status, 0, 0,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
        )
        view_container = QWidget()
        view_container.setLayout(view_layout)

        main_layout = QVBoxLayout()
        title = QLabel("Hand Gesture Interaction Playground")
        title.setObjectName("title")
        main_layout.addWidget(title)
        main_layout.addLayout(navigation)
        main_layout.addWidget(view_container, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.apply_style()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def change_step(self, index):
        """Stop the previous interaction before showing the selected step."""
        self.panels[self.panel_stack.currentIndex()].update_landmarks([])
        self.panel_stack.setCurrentIndex(index)

    def update_frame(self):
        frame, hands = self.tracker.read()
        if frame is None:
            self.show_status("Camera unavailable")
            self.panels[self.panel_stack.currentIndex()].update_landmarks([])
            return

        hand_count = len(hands)
        current_step = self.panel_stack.currentIndex()
        if hand_count > 1 and current_step > 0:
            self.show_status("Multiple hands detected")
        else:
            self.status.hide()

        active_panel = self.panels[self.panel_stack.currentIndex()]
        active_panel.update_landmarks(hands)

    def show_status(self, message):
        self.status.setText(message)
        self.status.adjustSize()
        self.status.show()
        self.status.raise_()

    def closeEvent(self, event):
        self.timer.stop()
        self.tracker.close()
        event.accept()

    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background: #f1f5f9; }
            QLabel { color: #0f172a; font-size: 15px; }
            QLabel#title { font-size: 25px; font-weight: 700; padding: 6px; }
            QLabel#status {
                background: #991b1b; color: white; padding: 8px 18px;
                border-radius: 5px; font-weight: 600; margin-top: 12px;
            }
            QPushButton {
                background: #64748b; color: white; border: 1px solid #64748b;
                border-radius: 6px; padding: 10px 16px; font-weight: 600;
            }
            QPushButton:hover { background: #475569; border-color: #475569; }
            QPushButton:checked { background: #2563eb; color: white; border-color: #2563eb; }
            QStackedWidget { background: white; border: 1px solid #cbd5e1; border-radius: 8px; }
        """)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
