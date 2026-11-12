"""File-system work: listing videos and folders, moving and renaming.

This module has no Qt imports so it can be tested on its own. Requirement IDs
(P-2, M-9, ...) refer to REQUIREMENTS.md.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# P-3
VIDEO_EXTENSIONS = frozenset(
    {".mp4", ".m4v", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".mpg", ".mpeg", ".3gp"}
)

# R-6
FORBIDDEN_NAME_CHARS = "/:"


class MoveError(Exception):
    """The move failed or couldn't be verified. The message is shown to the user."""


class RenameError(Exception):
    """The new name was rejected or the rename failed. The message is shown to the user."""


class TrashError(Exception):
    """Moving to the Trash failed. The file is left where it was."""


# Takes a file, moves it to the Trash, returns its new path there.
TrashFunction = Callable[[Path], Path]


@dataclass(frozen=True)
class Video:
    path: Path
    size: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def sort_key(self) -> tuple[int, str]:
        """Biggest first (P-4); equal sizes are ordered by name so the order is stable."""
        return (-self.size, self.path.name.lower())


def list_videos(folder: Path) -> list[Video]:
    """Videos directly inside `folder`, biggest first (P-2, P-3, P-4).

    Hidden files are skipped, including the "._name.mp4" metadata files macOS
    leaves on external drives. Only file sizes are read (N-3).
    """
    videos: list[Video] = []
    with os.scandir(folder) as entries:
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if os.path.splitext(entry.name)[1].lower() not in VIDEO_EXTENSIONS:
                continue
            try:
                if not entry.is_file():
                    continue
                size = entry.stat().st_size
            except OSError:
                continue
            videos.append(Video(Path(entry.path), size))
    videos.sort(key=lambda v: v.sort_key)
    return videos


def list_folders(root: Path, exclude: Path | None = None) -> list[str]:
    """Names of folders directly inside `root`, sorted by name (F-2, F-4, F-5)."""
    excluded = _real(exclude) if exclude is not None else None
    names: list[str] = []
    with os.scandir(root) as entries:
        for entry in entries:
            if entry.name.startswith("."):
                continue
            try:
                if not entry.is_dir():
                    continue
            except OSError:
                continue
            if excluded is not None and _real(entry.path) == excluded:
                continue
            names.append(entry.name)
    names.sort(key=str.lower)
    return names


def unique_destination(folder: Path, filename: str) -> Path:
    """A path in `folder` that doesn't exist yet: `name.mp4`, then `name (1).mp4`, ... (M-9)."""
    target = folder / filename
    if not os.path.lexists(target):
        return target
    stem, ext = os.path.splitext(filename)
    n = 1
    while True:
        target = folder / f"{stem} ({n}){ext}"
        if not os.path.lexists(target):
            return target
        n += 1


def move_verified(source: Path, folder: Path, name: str | None = None) -> Path:
    """Move `source` into `folder` and verify it (M-8, M-9, M-10).

    `name` gives the file a different name in `folder`. Undo uses it to restore the
    original name of a file that comes back from the Trash (U-3).
    Returns the final path, which has a " (n)" suffix if the name was taken.
    Raises MoveError on failure. If the move fails, the original is left in place.
    """
    try:
        size = source.stat().st_size
    except FileNotFoundError as e:
        raise MoveError(f"{source.name} is no longer in {source.parent.name or source.parent}") from e
    except OSError as e:
        raise MoveError(f"Can't read {source.name}: {e.strerror or e}") from e
    if not folder.is_dir():
        raise MoveError(f"Folder not found: {folder}")

    destination = unique_destination(folder, name or source.name)
    try:
        # shutil.move renames on the same drive, and copies then deletes between drives.
        shutil.move(os.fspath(source), os.fspath(destination))
    except OSError as e:
        # A failed copy between drives can leave a partial file behind. Remove it, but
        # only while the original is still there (we created that file a moment ago).
        if source.exists() and os.path.lexists(destination) and not _same_file(source, destination):
            try:
                destination.unlink()
            except OSError:
                pass
        raise MoveError(f"Couldn't move {source.name}: {e.strerror or e}") from e

    problems = []
    try:
        if destination.stat().st_size != size:
            problems.append("the size in the destination is different")
    except OSError:
        problems.append("the file isn't in the destination")
    if os.path.lexists(source):
        problems.append("the original is still in the source folder")
    if problems:
        raise MoveError(f"Couldn't verify the move of {source.name}: {'; '.join(problems)}")
    return destination


def trash_verified(source: Path, trash: TrashFunction) -> Path:
    """Move `source` to the Trash with `trash` and check it arrived (D-4). Never deletes for good.

    Returns the path inside the Trash, which Undo needs to bring the file back (U-3).
    """
    if not source.is_file():
        raise TrashError(f"{source.name} is no longer in {source.parent.name}")
    try:
        trashed = trash(source)
    except OSError as e:
        raise TrashError(f"Couldn't move {source.name} to the Trash: {e.strerror or e}") from e
    if os.path.lexists(source) or not os.path.lexists(trashed):
        raise TrashError(f"Couldn't verify that {source.name} is in the Trash")
    return trashed


def is_trash_path(path: Path | str) -> bool:
    """True for files in the Trash: ~/.Trash, or .Trashes on an external drive."""
    return any(part in (".Trash", ".Trashes") for part in Path(path).parts)


def rename_video(source: Path, new_stem: str) -> Path:
    """Rename `source` in its own folder, keeping its extension (R-2, R-4, R-6).

    Returns the new path. Raises RenameError if the name is rejected or the rename fails.
    """
    stem = new_stem.strip()
    if not stem:
        raise RenameError("The name can't be empty.")
    if any(ch in stem for ch in FORBIDDEN_NAME_CHARS):
        raise RenameError("The name can't contain / or :")
    if stem.startswith("."):
        raise RenameError("The name can't start with a dot (the file would be hidden).")
    new_name = stem + source.suffix
    if new_name == source.name:
        raise RenameError("The name is unchanged.")
    target = source.with_name(new_name)
    # On macOS drives that ignore upper/lower case, "Clip" and "clip" are the same file,
    # so a case-only rename is allowed.
    if os.path.lexists(target) and not _same_file(source, target):
        raise RenameError(f"{new_name} already exists in this folder.")
    try:
        os.rename(source, target)
    except OSError as e:
        raise RenameError(f"Couldn't rename {source.name}: {e.strerror or e}") from e
    return target


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit in ("B", "KB") else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"  # unreachable, keeps type checkers happy


def _real(path: Path | str) -> str:
    return os.path.normcase(os.path.realpath(path))


def _same_file(a: Path, b: Path) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False
