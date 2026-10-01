"""Local track playback using Qt Multimedia."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class MusicPlayer:
    """Small wrapper around QMediaPlayer for the demo's fixed track list."""

    def __init__(self, assets_path: Path):
        self.tracks = [
            {
                "title": "Digital Clouds",
                "audio": assets_path / "tracks" / "mixkit-digital-clouds-175.mp3",
                "cover": assets_path / "covers" / "digital_clouds.png",
            },
            {
                "title": "Groovy Jazz",
                "audio": assets_path / "tracks" / "mixkit-groovy-jazz-646.mp3",
                "cover": assets_path / "covers" / "groovy_jazz.png",
            },
            {
                "title": "Sleepy Cat",
                "audio": assets_path / "tracks" / "mixkit-sleepy-cat-135.mp3",
                "cover": assets_path / "covers" / "sleepy_cat.png",
            },
        ]
        self.track_index = 0
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.7)
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self._load_current_track()

    @property
    def current_track(self):
        return self.tracks[self.track_index]

    @property
    def position(self):
        return self.media_player.position()

    @property
    def duration(self):
        return self.media_player.duration()

    @property
    def volume(self):
        return self.audio_output.volume()

    @property
    def is_playing(self):
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def play(self):
        self.media_player.play()

    def pause(self):
        self.media_player.pause()

    def next(self):
        self._switch_track(1)

    def previous(self):
        self._switch_track(-1)

    def seek(self, position):
        self.media_player.setPosition(max(0, min(int(position), self.duration)))

    def set_volume(self, value):
        self.audio_output.setVolume(max(0.0, min(float(value), 1.0)))

    def _switch_track(self, offset):
        was_playing = self.is_playing
        self.track_index = (self.track_index + offset) % len(self.tracks)
        self._load_current_track()
        if was_playing:
            self.play()

    def _load_current_track(self):
        audio_path = self.current_track["audio"]
        self.media_player.setSource(QUrl.fromLocalFile(str(audio_path)))
        self.media_player.setPosition(0)
