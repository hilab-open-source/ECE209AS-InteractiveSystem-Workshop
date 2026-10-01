"""Camera input and raw MediaPipe hand landmark sensing."""

from pathlib import Path
import time

import cv2
import mediapipe as mp


class HandTracker:
    """Read camera frames and return MediaPipe's hand landmarks."""

    def __init__(self, model_path: Path, camera_index: int = 0):
        self.camera = cv2.VideoCapture(camera_index)

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(model_path),
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def read(self):
        """Return a mirrored BGR frame and a list of raw landmark lists."""
        ok, frame = self.camera.read()
        if not ok:
            return None, []

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        media_pipe_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = time.monotonic_ns() // 1_000_000
        result = self.landmarker.detect_for_video(media_pipe_image, timestamp_ms)
        return frame, result.hand_landmarks

    def close(self):
        self.camera.release()
        self.landmarker.close()
