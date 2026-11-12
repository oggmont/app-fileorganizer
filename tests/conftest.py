from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

# Must be set before Qt is imported: no window on screen, and the FFmpeg media backend.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")

import pytest

# name -> ffmpeg output arguments. Durations differ so the file sizes differ.
SAMPLE_VIDEOS = {
    "beach_long.mp4": ["-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "holiday_2019.avi": ["-t", "4", "-c:v", "libxvid", "-q:v", "4", "-c:a", "libmp3lame"],
    "drone_lake.mkv": ["-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "old_camera.wmv": ["-t", "2", "-c:v", "wmv2", "-c:a", "wmav2"],
    "clip.mov": ["-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
}


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    from fileorganizer.theme import apply_theme

    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    yield app


@pytest.fixture(scope="session")
def sample_videos(tmp_path_factory) -> Path:
    """Real, playable videos in several formats, made once per test run with ffmpeg."""
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is needed to generate sample videos (brew install ffmpeg)")
    folder = tmp_path_factory.mktemp("samples")
    for name, args in SAMPLE_VIDEOS.items():
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc=size=320x240:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440",
            *args, "-shortest", str(folder / name),
        ]
        subprocess.run(cmd, check=True)
    return folder


def wait_until(condition, timeout: float = 10.0) -> bool:
    """Process Qt events until `condition()` is true or `timeout` seconds pass."""
    from PySide6.QtWidgets import QApplication

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    QApplication.processEvents()
    return bool(condition())
