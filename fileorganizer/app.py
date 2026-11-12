"""Entry point: `python -m fileorganizer` or `./run.sh`."""

from __future__ import annotations

import os
import sys


def main(argv: list[str] | None = None) -> int:
    # Qt's FFmpeg backend plays AVI, MKV, WMV and more (N-2). It's the default on macOS,
    # but set it explicitly so nothing silently falls back to AVFoundation (MP4/MOV only).
    os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")
    # FFmpeg prints a long probe report for every file it opens. Playback errors still
    # reach the status bar through QMediaPlayer.errorOccurred.
    os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg*=false")
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 isn't installed for this Python.\n"
            "Run ./run.sh, or set up the environment with:\n"
            "  python3.14 -m venv .venv && .venv/bin/pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    from PySide6.QtGui import QIcon, QPixmap

    from .icon import draw_icon
    from .main_window import MainWindow
    from .theme import apply_theme

    app = QApplication(argv if argv is not None else sys.argv)
    app.setOrganizationName("app-fileorganizer")
    app.setApplicationName("Video File Organizer")
    app.setWindowIcon(QIcon(QPixmap.fromImage(draw_icon(512))))  # Dock icon, also when run from Terminal
    apply_theme(app)

    window = MainWindow()
    window.showMaximized()  # L-1
    return app.exec()
