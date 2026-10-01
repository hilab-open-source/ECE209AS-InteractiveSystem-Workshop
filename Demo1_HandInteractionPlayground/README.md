# Hand Gesture Interaction Playground — Demo 1

This local desktop demo shows how the same hand-landmark sensor data can support
different interactions. It uses Python, PySide6, OpenCV, MediaPipe Hand
Landmarker, and NumPy (installed with OpenCV/MediaPipe).

## Setup and run

From `Demo1_HandInteractionPlayground`:

```bash
conda create -n hand-playground python=3.11
conda activate hand-playground
pip install PySide6 opencv-python "mediapipe==0.10.35" numpy
python app.py
```

Allow camera access if your operating system asks. The application expects the
official MediaPipe model at `assets/hand_landmarker.task` and the local cat image
at `assets/cat.png`; both are included in this demo.

The model is Google's official MediaPipe Hand Landmarker model. The cat image is
Alvesgaspar's *Cat August 2010-4* from Wikimedia Commons (CC BY-SA 3.0).

## Code structure

- `app.py` creates the window, navigation, camera loop, and single main view.
- `modules/hand_tracking.py` is the sensing layer. It returns raw landmark positions.
- `modules/landmarks.py` draws the skeleton without showing the raw camera image.
- `modules/draw.py` uses the index fingertip to draw.
- `modules/pinch.py` thresholds thumb-index distance to grab and drag cubes.
- `modules/openness.py` maps that same distance continuously to cat size.

The four steps make the progression **sensing → landmarks → interpretation →
interaction** visible: LANDMARKS shows raw input, DRAW uses one point, PINCH
turns a distance into a binary state, and OPENNESS uses the distance as a
continuous value.
