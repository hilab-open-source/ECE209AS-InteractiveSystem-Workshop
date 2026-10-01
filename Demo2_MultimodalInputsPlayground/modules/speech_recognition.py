"""Microphone recording and constrained Vosk speech-to-text."""

import json
from pathlib import Path

import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer, Model, SetLogLevel


SAMPLE_RATE = 16_000
COMMAND_GRAMMAR = ["play", "pause", "next", "previous", "[unk]"]


class SpeechRecognizer:
    """Record short clips and return their transcription without interpreting it."""

    def __init__(self, model_path: Path):
        self.audio_chunks = []
        self.stream = None
        SetLogLevel(-1)
        self.model = Model(str(model_path))

    def start_recording(self):
        if self.stream is not None:
            return
        self.audio_chunks = []
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=self._capture_audio,
        )
        self.stream.start()

    def stop_recording(self):
        if self.stream is None:
            return np.empty(0, dtype=np.float32)
        self.stream.stop()
        self.stream.close()
        self.stream = None
        if not self.audio_chunks:
            return np.empty(0, dtype=np.float32)
        return np.concatenate(self.audio_chunks).reshape(-1)

    def transcribe(self, audio):
        if audio.size == 0:
            return ""

        recognizer = KaldiRecognizer(
            self.model,
            SAMPLE_RATE,
            json.dumps(COMMAND_GRAMMAR),
        )
        pcm_audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        recognizer.AcceptWaveform(pcm_audio.tobytes())
        result = json.loads(recognizer.FinalResult())
        return result.get("text", "").strip()

    def close(self):
        if self.stream is not None:
            self.stop_recording()

    def _capture_audio(self, input_data, frames, time_info, status):
        self.audio_chunks.append(input_data.copy())
