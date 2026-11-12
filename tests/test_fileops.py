from __future__ import annotations

import os
from pathlib import Path

import pytest

from fileorganizer.fileops import (
    MoveError,
    RenameError,
    TrashError,
    format_size,
    is_trash_path,
    list_folders,
    list_videos,
    move_verified,
    rename_video,
    trash_verified,
    unique_destination,
)


def write(path: Path, size: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


# -- list_videos (P-2, P-3, P-4) -------------------------------------------------
def test_videos_are_biggest_first_with_name_as_tiebreak(tmp_path):
    write(tmp_path / "small.mp4", 10)
    write(tmp_path / "big.avi", 300)
    write(tmp_path / "b_mid.mkv", 100)
    write(tmp_path / "a_mid.mov", 100)
    assert [v.name for v in list_videos(tmp_path)] == ["big.avi", "a_mid.mov", "b_mid.mkv", "small.mp4"]


def test_only_video_files_directly_inside_are_listed(tmp_path):
    write(tmp_path / "UPPER.MP4", 5)
    write(tmp_path / "notes.txt", 50)
    write(tmp_path / ".hidden.mp4", 50)
    write(tmp_path / "._metadata.mp4", 50)  # macOS AppleDouble file
    write(tmp_path / "sub" / "nested.mp4", 50)
    (tmp_path / "folder.mp4").mkdir()
    assert [v.name for v in list_videos(tmp_path)] == ["UPPER.MP4"]


# -- list_folders (F-2, F-4, F-5) -------------------------------------------------
def test_folders_sorted_hidden_skipped_source_excluded(tmp_path):
    for name in ["beach", "Animals", ".git", "unsorted", "zoo"]:
        (tmp_path / name).mkdir()
    write(tmp_path / "file.mp4", 1)
    (tmp_path / "beach" / "inner").mkdir()
    assert list_folders(tmp_path, exclude=tmp_path / "unsorted") == ["Animals", "beach", "zoo"]


# -- unique_destination and move_verified (M-8, M-9, M-10) -----------------------
def test_unique_destination_adds_a_number(tmp_path):
    assert unique_destination(tmp_path, "a.mp4") == tmp_path / "a.mp4"
    write(tmp_path / "a.mp4", 1)
    write(tmp_path / "a (1).mp4", 1)
    assert unique_destination(tmp_path, "a.mp4") == tmp_path / "a (2).mp4"


def test_move_puts_file_in_folder(tmp_path):
    src = write(tmp_path / "src" / "video.mp4", 1234)
    dest_folder = tmp_path / "dest" / "Beach"
    dest_folder.mkdir(parents=True)
    result = move_verified(src, dest_folder)
    assert result == dest_folder / "video.mp4"
    assert result.stat().st_size == 1234
    assert not src.exists()


def test_move_never_overwrites(tmp_path):
    src = write(tmp_path / "src" / "video.mp4", 20)
    dest_folder = tmp_path / "Beach"
    existing = write(dest_folder / "video.mp4", 99)
    result = move_verified(src, dest_folder)
    assert result.name == "video (1).mp4"
    assert existing.stat().st_size == 99
    assert result.stat().st_size == 20


def test_move_to_missing_folder_fails_and_keeps_the_file(tmp_path):
    src = write(tmp_path / "video.mp4", 5)
    with pytest.raises(MoveError):
        move_verified(src, tmp_path / "nope")
    assert src.exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores folder permissions")
def test_move_into_read_only_folder_fails_and_keeps_the_file(tmp_path):
    src = write(tmp_path / "src" / "video.mp4", 5)
    locked = tmp_path / "Locked"
    locked.mkdir()
    locked.chmod(0o500)
    try:
        with pytest.raises(MoveError):
            move_verified(src, locked)
    finally:
        locked.chmod(0o700)
    assert src.exists()
    assert list(locked.iterdir()) == []


# -- rename_video (R-2, R-4, R-6) ---------------------------------------------------
def test_rename_keeps_extension(tmp_path):
    src = write(tmp_path / "old name.avi", 3)
    result = rename_video(src, "  new name ")
    assert result == tmp_path / "new name.avi"
    assert result.exists() and not src.exists()


@pytest.mark.parametrize(
    "new_name, message",
    [("", "empty"), ("   ", "empty"), ("a/b", "/"), ("a:b", ":"), (".secret", "dot"), ("clip", "unchanged")],
)
def test_rename_rejects_bad_names(tmp_path, new_name, message):
    src = write(tmp_path / "clip.mp4", 3)
    with pytest.raises(RenameError, match=message):
        rename_video(src, new_name)
    assert src.exists()


def test_rename_never_overwrites(tmp_path):
    src = write(tmp_path / "clip.mp4", 3)
    other = write(tmp_path / "taken.mp4", 7)
    with pytest.raises(RenameError, match="already exists"):
        rename_video(src, "taken")
    assert src.exists() and other.stat().st_size == 7


def test_rename_case_only_change_is_allowed(tmp_path):
    src = write(tmp_path / "clip.mp4", 3)
    result = rename_video(src, "Clip")
    assert result.name == "Clip.mp4"
    assert [p.name for p in tmp_path.iterdir()] == ["Clip.mp4"]


def test_format_size():
    assert format_size(512) == "512 B"
    assert format_size(2048) == "2 KB"
    assert format_size(5 * 1024**2) == "5.0 MB"
    assert format_size(int(2.4 * 1024**3)) == "2.4 GB"


# -- trash and undo helpers (section 7) --------------------------------------------------
def _fake_trash(folder: Path):
    def trash(path: Path) -> Path:
        folder.mkdir(exist_ok=True)
        target = unique_destination(folder, path.name)
        path.rename(target)
        return target
    return trash


def test_trash_verified_returns_path_in_trash(tmp_path):
    src = write(tmp_path / "video.mp4", 10)
    trashed = trash_verified(src, _fake_trash(tmp_path / ".Trash"))
    assert trashed == tmp_path / ".Trash" / "video.mp4"
    assert trashed.exists() and not src.exists()


def test_trash_failure_keeps_file(tmp_path):
    src = write(tmp_path / "video.mp4", 10)

    def refuse(path):
        raise OSError("no Trash on this drive")

    with pytest.raises(TrashError, match="no Trash on this drive"):
        trash_verified(src, refuse)
    assert src.exists()


def test_trash_that_doesnt_move_the_file_is_an_error(tmp_path):
    src = write(tmp_path / "video.mp4", 10)
    with pytest.raises(TrashError, match="verify"):
        trash_verified(src, lambda path: tmp_path / "nowhere.mp4")
    assert src.exists()


def test_move_back_with_original_name(tmp_path):
    trashed = write(tmp_path / ".Trash" / "video 3.mp4", 10)
    source = tmp_path / "Unsorted"
    source.mkdir()
    restored = move_verified(trashed, source, name="video.mp4")
    assert restored == source / "video.mp4" and not trashed.exists()


def test_move_of_missing_file_says_where_it_was(tmp_path):
    (tmp_path / "Beach").mkdir()
    with pytest.raises(MoveError, match="no longer in Beach"):
        move_verified(tmp_path / "Beach" / "gone.mp4", tmp_path)


def test_is_trash_path():
    assert is_trash_path("/Users/me/.Trash/a.mp4")
    assert is_trash_path("/Volumes/Media/.Trashes/501/a.mp4")
    assert not is_trash_path("/Volumes/Media/Sorted/Beach/a.mp4")


def test_app_icon_draws(qapp):
    from fileorganizer.icon import draw_icon

    image = draw_icon(64)
    assert image.width() == 64 and not image.isNull()
    assert image.pixelColor(32, 32).alpha() == 255 and image.pixelColor(0, 0).alpha() == 0
