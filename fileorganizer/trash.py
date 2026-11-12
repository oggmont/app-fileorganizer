"""Moving a file to the macOS Trash (D-4).

Uses Qt's QFile.moveToTrash, which calls NSFileManager: the same Trash Finder uses,
including the .Trashes folder on external drives. Kept apart from fileops.py so that
module stays free of Qt.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile


def move_to_trash(path: Path) -> Path:
    """Move `path` to the Trash and return its new path there. Raises OSError on failure."""
    file = QFile(str(path))
    if not file.moveToTrash():
        raise OSError(file.errorString() or "the Trash refused the file")
    # After a successful moveToTrash, fileName() is the file's path inside the Trash.
    return Path(file.fileName())
