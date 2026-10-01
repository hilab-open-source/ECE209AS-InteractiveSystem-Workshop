"""Mid-Air Multimodal Music Player: Demo 2 for the HCI workshop."""

import math
import string
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from modules.hand_tracking import HandTracker
from modules.music_player import MusicPlayer
from modules.speech_recognition import SpeechRecognizer


ROOT = Path(__file__).resolve().parent

# Interaction constants are intentionally visible and easy to change for class discussion.
PINCH_DISTANCE = 0.055
CONTROL_HIT_MARGIN = 28

THUMB_TIP = 4
INDEX_TIP = 8
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
]


class SpeechSignals(QObject):
    transcribed = Signal(str)
    failed = Signal(str)


class PlayerView(QWidget):
    """Paint the music player and hand skeletons in one interaction space."""

    def __init__(self, music_player):
        super().__init__()
        self.music_player = music_player
        self.hands = []
        self.voice_state = "OFF"
        self.heard_text = ""
        self.camera_available = True
        self.cover_cache = {
            str(track["cover"]): QPixmap(str(track["cover"]))
            for track in music_player.tracks
        }
        self.setMinimumSize(820, 650)

    def timeline_rect(self):
        return QRectF(135, self.height() * 0.62, self.width() - 370, 8)

    def volume_rect(self):
        return QRectF(self.width() - 150, self.height() * 0.40, 8, self.height() * 0.28)

    def point_from_landmark(self, landmark):
        return QPointF(landmark.x * self.width(), landmark.y * self.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f4f7fb"))

        self._draw_player(painter)
        self._draw_hands(painter)
        self._draw_voice_status(painter)

    def _draw_player(self, painter):
        cover_size = min(250, int(self.height() * 0.34))
        cover_rect = QRectF((self.width() - cover_size) / 2, 34, cover_size, cover_size)
        cover = self.cover_cache[str(self.music_player.current_track["cover"])]
        scaled_cover = cover.scaled(
            cover_rect.size().toSize(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(cover_rect.toRect(), scaled_cover)

        painter.setPen(QColor("#162033"))
        painter.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title_rect = QRectF(40, cover_rect.bottom() + 18, self.width() - 80, 38)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.music_player.current_track["title"])

        state_text = "PLAYING" if self.music_player.is_playing else "PAUSED"
        painter.setPen(QColor("#657087"))
        painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        painter.drawText(
            QRectF(40, title_rect.bottom() + 2, self.width() - 80, 24),
            Qt.AlignmentFlag.AlignCenter,
            state_text,
        )

        timeline = self.timeline_rect()
        duration = self.music_player.duration
        progress = self.music_player.position / duration if duration > 0 else 0.0
        progress = max(0.0, min(progress, 1.0))
        knob_x = timeline.left() + progress * timeline.width()
        timeline_y = timeline.center().y()
        timeline_start = QPointF(timeline.left(), timeline_y)
        timeline_end = QPointF(timeline.right(), timeline_y)

        painter.setPen(QPen(QColor("#c7d0df"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(timeline_start, timeline_end)
        painter.setPen(QPen(QColor("#3867e8"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(timeline_start, QPointF(knob_x, timeline_y))
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#3867e8"), 4))
        painter.drawEllipse(QPointF(knob_x, timeline_y), 10, 10)

        painter.setPen(QColor("#596579"))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(
            QRectF(timeline.left() - 72, timeline.top() - 13, 62, 28),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            format_time(self.music_player.position),
        )
        painter.drawText(
            QRectF(timeline.right() + 12, timeline.top() - 13, 62, 28),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            format_time(duration),
        )

        volume = self.volume_rect()
        knob_y = volume.bottom() - self.music_player.volume * volume.height()
        volume_x = volume.center().x()
        volume_top = QPointF(volume_x, volume.top())
        volume_bottom = QPointF(volume_x, volume.bottom())
        painter.setPen(QPen(QColor("#c7d0df"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(volume_top, volume_bottom)
        painter.setPen(QPen(QColor("#3867e8"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(volume_bottom, QPointF(volume_x, knob_y))
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(QColor("#3867e8"), 4))
        painter.drawEllipse(QPointF(volume_x, knob_y), 10, 10)
        painter.setPen(QColor("#596579"))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(QPointF(volume_x - 20, volume.top() - 18), "VOL +")
        painter.drawText(QPointF(volume_x - 20, volume.bottom() + 28), "VOL −")

    def _draw_hands(self, painter):
        colors = [QColor("#00a884"), QColor("#f05a7e")]
        for hand_index, hand in enumerate(self.hands):
            color = colors[hand_index % len(colors)]
            points = [self.point_from_landmark(landmark) for landmark in hand]
            painter.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            for start, end in HAND_CONNECTIONS:
                painter.drawLine(points[start], points[end])
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            for point in points:
                painter.drawEllipse(point, 5, 5)

    def _draw_voice_status(self, painter):
        if self.voice_state == "LISTENING":
            color = QColor("#d92d20")
        elif self.voice_state == "Recognizing...":
            color = QColor("#b45309")
        else:
            color = QColor("#526077")

        painter.setPen(color)
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(
            QRectF(40, self.height() - 86, self.width() - 80, 28),
            Qt.AlignmentFlag.AlignCenter,
            f"Voice: {self.voice_state}",
        )
        painter.setPen(QColor("#526077"))
        painter.setFont(QFont("Arial", 12))
        heard = f'Heard: "{self.heard_text}"' if self.heard_text else "Heard: —"
        painter.drawText(
            QRectF(40, self.height() - 54, self.width() - 80, 26),
            Qt.AlignmentFlag.AlignCenter,
            heard,
        )
        if not self.camera_available:
            painter.setPen(QColor("#b42318"))
            painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            painter.drawText(
                QRectF(20, 12, self.width() - 40, 28),
                Qt.AlignmentFlag.AlignCenter,
                "Camera unavailable",
            )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mid-Air Multimodal Music Player")
        self.resize(980, 720)

        self.music_player = MusicPlayer(ROOT / "assets")
        self.hand_tracker = HandTracker(ROOT / "assets" / "hand_landmarker.task")
        self.speech_recognizer = SpeechRecognizer(
            ROOT / "assets" / "vosk-model-small-en-us-0.15"
        )
        self.view = PlayerView(self.music_player)
        self.setCentralWidget(self.view)

        self.dragging_control = None
        self.recording = False
        self.recognizing = False
        self.speech_signals = SpeechSignals()
        self.speech_signals.transcribed.connect(self.handle_transcript)
        self.speech_signals.failed.connect(self.handle_transcription_error)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_interaction)
        self.timer.start(33)

    def update_interaction(self):
        frame, hands = self.hand_tracker.read()
        self.view.camera_available = frame is not None
        self.view.hands = hands

        pinching = [is_pinching(hand) for hand in hands]
        both_hands_pinching = len(hands) == 2 and all(pinching)

        if self.recording:
            if not both_hands_pinching:
                self.stop_voice_recording()
        elif not self.recognizing and both_hands_pinching:
            self.start_voice_recording()

        if len(hands) == 1 and not self.recording and not self.recognizing:
            self.handle_direct_manipulation(hands[0], pinching[0])
        else:
            self.dragging_control = None

        self.view.update()

    def handle_direct_manipulation(self, hand, pinching):
        pointer = self.view.point_from_landmark(hand[INDEX_TIP])
        if not pinching:
            self.dragging_control = None
            return

        if self.dragging_control is None:
            timeline_hit_area = self.view.timeline_rect().adjusted(
                -CONTROL_HIT_MARGIN, -CONTROL_HIT_MARGIN,
                CONTROL_HIT_MARGIN, CONTROL_HIT_MARGIN,
            )
            volume_hit_area = self.view.volume_rect().adjusted(
                -CONTROL_HIT_MARGIN, -CONTROL_HIT_MARGIN,
                CONTROL_HIT_MARGIN, CONTROL_HIT_MARGIN,
            )
            timeline_hit = timeline_hit_area.contains(pointer)
            volume_hit = volume_hit_area.contains(pointer)
            if timeline_hit and volume_hit:
                timeline_distance = abs(pointer.y() - self.view.timeline_rect().center().y())
                volume_distance = abs(pointer.x() - self.view.volume_rect().center().x())
                self.dragging_control = (
                    "timeline" if timeline_distance < volume_distance else "volume"
                )
            elif timeline_hit:
                self.dragging_control = "timeline"
            elif volume_hit:
                self.dragging_control = "volume"

        if self.dragging_control == "timeline":
            timeline = self.view.timeline_rect()
            pointer_x = pointer.x()
            fraction = (pointer_x - timeline.left()) / timeline.width()
            fraction = max(0.0, min(fraction, 1.0))
            self.music_player.seek(fraction * self.music_player.duration)
        elif self.dragging_control == "volume":
            volume = self.view.volume_rect()
            pointer_y = pointer.y()
            fraction = 1.0 - (pointer_y - volume.top()) / volume.height()
            self.music_player.set_volume(fraction)

    def start_voice_recording(self):
        try:
            self.speech_recognizer.start_recording()
        except Exception as error:
            self.view.voice_state = "Microphone unavailable"
            self.view.heard_text = str(error)
            return
        self.recording = True
        self.view.voice_state = "LISTENING"
        self.view.heard_text = ""

    def stop_voice_recording(self):
        audio = self.speech_recognizer.stop_recording()
        self.recording = False
        self.recognizing = True
        self.view.voice_state = "Recognizing..."
        thread = threading.Thread(target=self.transcribe_audio, args=(audio,), daemon=True)
        thread.start()

    def transcribe_audio(self, audio):
        try:
            text = self.speech_recognizer.transcribe(audio)
            self.speech_signals.transcribed.emit(text)
        except Exception as error:
            self.speech_signals.failed.emit(str(error))

    def handle_transcript(self, text):
        self.recognizing = False
        self.view.voice_state = "OFF"
        self.view.heard_text = text

        command = text.lower().strip().strip(string.punctuation).strip()
        actions = {
            "play": self.music_player.play,
            "pause": self.music_player.pause,
            "next": self.music_player.next,
            "previous": self.music_player.previous,
        }
        action = actions.get(command)
        if action is not None:
            action()
        self.view.update()

    def handle_transcription_error(self, message):
        self.recognizing = False
        self.view.voice_state = "OFF"
        self.view.heard_text = f"Recognition failed: {message}"
        self.view.update()

    def closeEvent(self, event):
        self.timer.stop()
        self.hand_tracker.close()
        self.speech_recognizer.close()
        event.accept()


def is_pinching(hand):
    thumb = hand[THUMB_TIP]
    index = hand[INDEX_TIP]
    distance = math.hypot(thumb.x - index.x, thumb.y - index.y)
    return distance < PINCH_DISTANCE


def format_time(milliseconds):
    total_seconds = max(0, int(milliseconds)) // 1000
    return f"{total_seconds // 60}:{total_seconds % 60:02d}"


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
