"""The move log: `moves_log.txt` in the project root (section 5 of REQUIREMENTS.md).

Every file operation is a move: into a folder, back to the source folder (Undo), or into
the Trash (Delete), so all of them use the same line format (G-4).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .fileops import is_trash_path

DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent / "moves_log.txt"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PANEL_LIMIT = 100  # G-5


def default_log_path() -> Path:
    """The log file. FILEORGANIZER_LOG overrides it (used by the tests)."""
    override = os.environ.get("FILEORGANIZER_LOG")
    return Path(override) if override else DEFAULT_LOG_PATH


def _clean(text: str) -> str:
    # Tabs separate the fields and newlines separate entries, so escape them in paths.
    return text.replace("\t", "\\t").replace("\n", "\\n")


@dataclass(frozen=True)
class LogEntry:
    when: datetime
    source: str
    destination: str
    size: int

    @property
    def name(self) -> str:
        return Path(self.destination).name

    @property
    def folder(self) -> str:
        return "Trash" if self.in_trash else Path(self.destination).parent.name

    @property
    def in_trash(self) -> bool:
        return is_trash_path(self.destination)

    def to_line(self) -> str:
        """G-4: date and time, source path, destination path, size, separated by tabs."""
        return "\t".join(
            [self.when.strftime(TIME_FORMAT), _clean(self.source), _clean(self.destination), str(self.size)]
        )

    @classmethod
    def from_line(cls, line: str) -> LogEntry | None:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 4:
            return None
        try:
            return cls(datetime.strptime(parts[0], TIME_FORMAT), parts[1], parts[2], int(parts[3]))
        except ValueError:
            return None


class MoveLog:
    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, source: Path, destination: Path, size: int, when: datetime | None = None) -> LogEntry:
        """G-3: add one line. Lines are never removed."""
        entry = LogEntry(when or datetime.now().replace(microsecond=0), str(source), str(destination), size)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(entry.to_line() + "\n")
        return entry

    def latest(self, limit: int = PANEL_LIMIT) -> list[LogEntry]:
        """G-5: the newest `limit` entries, newest first. Broken lines are skipped."""
        try:
            lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        except FileNotFoundError:
            return []
        entries: list[LogEntry] = []
        for line in reversed(lines):
            entry = LogEntry.from_line(line)
            if entry is not None:
                entries.append(entry)
                if len(entries) >= limit:
                    break
        return entries
