# Mid-Air Multimodal Music Player — Demo 2

This HCI workshop demo is a fully touchless desktop music player. One hand
directly manipulates playback controls, while two simultaneous pinches create a
context for speaking a discrete media command. It is intentionally a small
teaching prototype rather than a production application.

The demo uses Python 3.11, PySide6 Widgets and Qt Multimedia, OpenCV, MediaPipe
Hand Landmarker, SoundDevice, and Vosk offline speech recognition.

## Setup

From `Demo2_MultimodalInputsPlayground`:

```bash
conda create -n multimodal-player python=3.11
conda activate multimodal-player
pip install PySide6 opencv-python "mediapipe==0.10.35" numpy sounddevice vosk
python app.py
```

On first launch, allow macOS camera and microphone access. If SoundDevice cannot
open the microphone, install PortAudio with `brew install portaudio`, then
reinstall SoundDevice in the Conda environment.

The MediaPipe model is already included at `assets/hand_landmarker.task`; no
manual model download is required. The local Vosk English model is included at
`assets/vosk-model-small-en-us-0.15`, so speech recognition also works offline.

## Interaction

- **One hand:** move the index fingertip to the horizontal timeline or vertical
  volume control, pinch to grab, drag, and release to drop.
- **Two hands:** both landmark skeletons remain visible and direct manipulation
  is disabled.
- **Both hands pinching:** microphone recording starts immediately and the UI
  shows `LISTENING`.
- **Release either pinch:** recording stops immediately, speech is transcribed,
  and the recognized command is executed.

Vosk is constrained to `play`, `pause`, `next`, `previous`, and an unknown-word
fallback. Only the four commands trigger player actions. The three-track list
loops in both directions. Playback starts on Digital Clouds, paused at 0:00.

## Code structure

- `app.py` builds the UI, overlays landmarks, and coordinates gesture and voice
  interaction.
- `modules/hand_tracking.py` returns raw landmarks for up to two hands.
- `modules/speech_recognition.py` records microphone audio and runs constrained
  offline Vosk recognition.
- `modules/music_player.py` controls the fixed local playlist with
  `QMediaPlayer` and `QAudioOutput`.
- `assets/` contains the covers, MP3 tracks, MediaPipe model, and Vosk model.

## Asset attribution

The MP3 tracks **Digital Clouds**, **Groovy Jazz**, and **Sleepy Cat** were
downloaded from Mixkit and are used under the applicable Mixkit free music
license. The images in `assets/covers/` were AI-generated specifically for this
classroom demo; they are not official album covers. The included
`vosk-model-small-en-us-0.15` model is published by Alpha Cephei under the
Apache 2.0 license.
