"""Writes the app icon as a macOS .icns file. Used by make_app.sh.

Usage: .venv/bin/python scripts/make_icon.py OUTPUT.icns
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtGui import QGuiApplication  # noqa: E402

from fileorganizer.icon import draw_icon  # noqa: E402


def main(output: Path) -> None:
    app = QGuiApplication([])  # noqa: F841 (QPainter needs an application object)
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "AppIcon.iconset"
        iconset.mkdir()
        # Each size is drawn from scratch, so small sizes stay sharp.
        for size in (16, 32, 128, 256, 512):
            draw_icon(size).save(str(iconset / f"icon_{size}x{size}.png"))
            draw_icon(size * 2).save(str(iconset / f"icon_{size}x{size}@2x.png"))
        subprocess.run(["iconutil", "-c", "icns", "-o", str(output), str(iconset)], check=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
