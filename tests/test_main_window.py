"""Drives the real window offscreen, with real videos, the way a user would."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPointF, QSettings, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from conftest import SAMPLE_VIDEOS, wait_until
from fileorganizer.fileops import list_videos, unique_destination


@pytest.fixture
def setup(qapp, tmp_path, sample_videos):
    source = tmp_path / "Unsorted"
    shutil.copytree(sample_videos, source)
    dest = tmp_path / "Sorted"
    for name in ["Animals", "Beach", "Family"]:
        (dest / name).mkdir(parents=True)
    log_path = tmp_path / "moves_log.txt"
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)

    from fileorganizer.main_window import MainWindow

    window = MainWindow(settings=settings, log_path=log_path, trash=fake_trash(tmp_path / ".Trash"))
    window.resize(1400, 900)
    window.set_source(source)
    window.set_dest(dest)
    yield window, source, dest, log_path
    window.player_panel.release()
    window.close()
    window.deleteLater()


def fake_trash(folder: Path):
    """Stands in for the macOS Trash so tests never put files in the user's real Trash."""

    def trash(path: Path) -> Path:
        folder.mkdir(exist_ok=True)
        target = unique_destination(folder, path.name)
        shutil.move(path, target)
        return target

    return trash


def expected_order(source: Path) -> list[str]:
    return [v.name for v in list_videos(source)]


def wait_for_move(window) -> None:
    assert wait_until(lambda: not window.busy, 15), "file operation didn't finish"


def _send_mouse(window, name: str, event_types) -> None:
    lst = window.folder_panel.list
    row = window.folder_panel.names().index(name)
    point = lst.visualItemRect(lst.item(row)).center()
    viewport = lst.viewport()
    for event_type in event_types:
        buttons = Qt.MouseButton.NoButton if event_type == QEvent.Type.MouseButtonRelease else Qt.MouseButton.LeftButton
        event = QMouseEvent(
            event_type, QPointF(point), QPointF(viewport.mapToGlobal(point)),
            Qt.MouseButton.LeftButton, buttons, Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(viewport, event)


def click_folder(window, name: str) -> None:
    _send_mouse(window, name, [QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease])


def double_click_folder(window, name: str) -> None:
    # What the OS sends for a double-click: press, release, double-click, release.
    _send_mouse(window, name, [
        QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
        QEvent.Type.MouseButtonDblClick, QEvent.Type.MouseButtonRelease,
    ])


# -- playback (N-2, P-6, P-8) -----------------------------------------------------
@pytest.mark.parametrize("name", list(SAMPLE_VIDEOS))
def test_every_format_plays(setup, name):
    window, source, *_ = setup
    window.index = expected_order(source).index(name)
    window._load_current()
    player = window.player_panel.player
    errors = []
    player.errorOccurred.connect(lambda error, text: errors.append(text))
    assert wait_until(lambda: player.position() > 300 or errors, 10)
    assert not errors, f"{name}: {errors}"
    assert player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    assert player.loops() == -1  # replays until stopped, skipped or moved


def test_videos_play_biggest_first(setup):
    window, source, *_ = setup
    order = expected_order(source)
    assert window.current_video.name == order[0]
    assert window.player_panel._details_label.text().endswith(f"1 / {len(order)}")
    assert window.player_panel.player.source().toLocalFile().endswith(order[0])


# -- navigation (P-11, K-2, K-3) ---------------------------------------------------
def test_left_right_and_skip_change_video(setup):
    window, source, *_ = setup
    order = expected_order(source)
    window.previous_video()
    assert window.current_video.name == order[0]
    assert window.status_line.text() == "First video."
    window.next_video()
    window.player_panel.skip_button.click()
    assert window.current_video.name == order[2]
    window.previous_video()
    assert window.current_video.name == order[1]
    for _ in range(10):
        window.next_video()
    assert window.current_video.name == order[-1]
    assert window.status_line.text() == "Last video."
    assert sorted(p.name for p in source.iterdir()) == sorted(order)  # nothing touched on disk


# -- move flow (section 4) ------------------------------------------------------------
def test_click_selects_then_second_click_moves_and_selection_stays(setup):
    window, source, dest, log_path = setup
    order = expected_order(source)

    click_folder(window, "Beach")
    assert window.folder_panel.armed_name() == "Beach"
    assert "again to move" in window.status_line.text()
    assert (source / order[0]).exists()

    click_folder(window, "Beach")
    wait_for_move(window)
    assert (dest / "Beach" / order[0]).exists()
    assert not (source / order[0]).exists()
    assert window.status_line.text().startswith(f"✓ Moved {order[0]} → Beach")
    assert window.status_line.kind() == "ok"
    assert window.current_video.name == order[1]  # M-12: next smaller video
    assert window.player_panel.player.source().toLocalFile().endswith(order[1])
    assert window.folder_panel.armed_name() == "Beach"  # M-12a

    # Log file and panel (G-2, G-3, G-4)
    line = log_path.read_text().strip()
    fields = line.split("\t")
    assert fields[1] == str(source / order[0]) and fields[2] == str(dest / "Beach" / order[0])
    assert window.log_panel.entries()[0].folder == "Beach"

    # M-12a: one more click on the still-selected folder moves the next video.
    window._ignore_activations_until = 0
    click_folder(window, "Beach")
    wait_for_move(window)
    assert (dest / "Beach" / order[1]).exists()
    assert window.current_video.name == order[2]


def test_double_click_moves_exactly_one_video(setup):
    window, source, dest, _ = setup
    order = expected_order(source)
    double_click_folder(window, "Family")
    wait_for_move(window)
    assert sorted(p.name for p in (dest / "Family").iterdir()) == [order[0]]

    # Folder is still selected now; a double-click on it must still move only one video.
    window._ignore_activations_until = 0
    double_click_folder(window, "Family")
    wait_for_move(window)
    wait_until(lambda: False, 0.2)
    assert sorted(p.name for p in (dest / "Family").iterdir()) == sorted(order[:2])


def test_clicking_another_folder_moves_the_selection_only(setup):
    window, source, dest, _ = setup
    click_folder(window, "Beach")
    click_folder(window, "Animals")
    assert window.folder_panel.armed_name() == "Animals"
    assert not any((dest / "Beach").iterdir()) and not any((dest / "Animals").iterdir())


def test_name_clash_adds_number(setup):
    window, source, dest, _ = setup
    first = expected_order(source)[0]
    (dest / "Beach" / first).write_bytes(b"keep me")
    double_click_folder(window, "Beach")
    wait_for_move(window)
    stem, ext = first.rsplit(".", 1)
    assert (dest / "Beach" / f"{stem} (1).{ext}").exists()
    assert (dest / "Beach" / first).read_bytes() == b"keep me"
    assert f"as {stem} (1).{ext}" in window.status_line.text()


def test_failed_move_shows_error_and_stays_on_video(setup):
    window, source, dest, log_path = setup
    first = expected_order(source)[0]
    click_folder(window, "Beach")
    shutil.rmtree(dest / "Beach")  # folder disappears before the move
    click_folder(window, "Beach")
    wait_for_move(window)
    assert window.status_line.kind() == "error"
    assert window.current_video.name == first
    assert (source / first).exists()
    assert not log_path.exists()


# -- keyboard (section 7) ----------------------------------------------------------------
def test_keyboard_flow(setup):
    window, source, dest, _ = setup
    order = expected_order(source)
    window.show()
    window.activateWindow()
    if not QTest.qWaitForWindowActive(window, 3000):
        pytest.skip("offscreen platform couldn't activate the window")

    QTest.keyClick(window, Qt.Key.Key_Right)
    assert window.current_video.name == order[1]
    QTest.keyClick(window, Qt.Key.Key_Left)
    assert window.current_video.name == order[0]

    assert window.folder_panel.cursor_name() == "Animals"  # K-5
    QTest.keyClick(window, Qt.Key.Key_Up)
    assert window.folder_panel.cursor_name() == "Animals"  # stops at the top
    QTest.keyClick(window, Qt.Key.Key_Down)
    assert window.folder_panel.cursor_name() == "Beach"

    QTest.keyClick(window, Qt.Key.Key_Return)
    assert window.folder_panel.armed_name() == "Beach"
    QTest.keyClick(window, Qt.Key.Key_Down)
    assert window.folder_panel.armed_name() is None  # K-6
    QTest.keyClick(window, Qt.Key.Key_Up)

    QTest.keyClick(window, Qt.Key.Key_Return)
    QTest.keyClick(window, Qt.Key.Key_Return)
    wait_for_move(window)
    assert (dest / "Beach" / order[0]).exists()
    # A fast extra Enter right after the move is ignored (double Enter = one move).
    QTest.keyClick(window, Qt.Key.Key_Return)
    wait_until(lambda: False, 0.2)
    wait_for_move(window)
    assert not (dest / "Beach" / order[1]).exists()

    # K-8: a single Enter later moves the next video to the same folder.
    window._ignore_activations_until = 0
    QTest.keyClick(window, Qt.Key.Key_Right)  # skip one; selection stays (K-4)
    assert window.folder_panel.armed_name() == "Beach"
    QTest.keyClick(window, Qt.Key.Key_Return)
    wait_for_move(window)
    assert (dest / "Beach" / order[2]).exists()

    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert window.folder_panel.armed_name() is None


# -- rename (section 6) ----------------------------------------------------------------------
def test_rename_flow(setup):
    window, source, *_ = setup
    first = expected_order(source)[0]
    panel = window.player_panel
    stem, ext = first.rsplit(".", 1)
    assert panel.rename_field.text() == stem and panel.rename_field.isReadOnly()
    assert not panel.rename_ok_button.isEnabled()

    panel.rename_change_button.click()
    assert panel.editing and not panel.rename_field.isReadOnly()
    assert not any(s.isEnabled() for s in window._shortcuts)  # K-9

    panel.rename_field.setText("bad/name")
    panel.rename_ok_button.click()
    assert window.status_line.kind() == "error" and panel.editing
    assert (source / first).exists()

    panel.rename_field.setText("renamed video")
    panel.rename_ok_button.click()
    new_name = f"renamed video.{ext}"
    assert (source / new_name).exists() and not (source / first).exists()
    assert not panel.editing and panel.rename_field.text() == "renamed video"
    assert window.current_video.name == new_name
    assert window.status_line.text() == f"✓ Renamed {first} → {new_name}"
    assert all(s.isEnabled() for s in window._shortcuts)
    assert panel.player.source().toLocalFile().endswith(new_name)


def test_folder_click_while_renaming_only_cancels(setup):
    window, source, dest, _ = setup
    panel = window.player_panel
    panel.rename_change_button.click()
    panel.rename_field.setText("half typed")
    click_folder(window, "Beach")
    assert not panel.editing
    assert window.folder_panel.armed_name() is None
    assert not any((dest / "Beach").iterdir())


def test_no_more_videos(setup):
    window, source, dest, _ = setup
    for _ in SAMPLE_VIDEOS:
        window._ignore_activations_until = 0
        if window.folder_panel.armed_name() is None:
            click_folder(window, "Animals")
        click_folder(window, "Animals")
        wait_for_move(window)
    assert window.current_video is None
    assert window.player_panel.message() == "No more videos."
    assert len(list((dest / "Animals").iterdir())) == len(SAMPLE_VIDEOS)
    assert len(window.log_panel.entries()) == len(SAMPLE_VIDEOS)


def test_settings_remember_locations(setup, tmp_path):
    window, source, dest, log_path = setup
    from fileorganizer.main_window import MainWindow

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    second = MainWindow(settings=settings, log_path=log_path)
    try:
        assert second.source == source and second.dest == dest
    finally:
        second.player_panel.release()
        second.deleteLater()


# -- undo (section 7) -------------------------------------------------------------------------
def test_undo_brings_moved_video_back_and_plays_it(setup):
    window, source, dest, log_path = setup
    order = expected_order(source)
    panel = window.player_panel
    assert not panel.undo_button.isEnabled()

    double_click_folder(window, "Beach")
    wait_for_move(window)
    window._ignore_activations_until = 0
    window.next_video()  # now on order[2]
    assert panel.undo_button.isEnabled()

    panel.undo_button.click()
    wait_for_move(window)
    assert (source / order[0]).exists() and not (dest / "Beach" / order[0]).exists()
    assert window.current_video.name == order[0]  # U-3: it plays again
    assert panel.player.source().toLocalFile().endswith(order[0])
    assert window.status_line.text() == f"↩ Brought {order[0]} back from Beach"
    assert window.folder_panel.armed_name() == "Beach"  # selection stays
    lines = log_path.read_text().splitlines()
    assert len(lines) == 2 and lines[1].split("\t")[2] == str(source / order[0])  # G-3
    assert not panel.undo_button.isEnabled()

    window._ignore_activations_until = 0
    window.undo()
    assert window.status_line.text() == "Nothing to undo."


def test_undo_goes_back_one_step_at_a_time(setup):
    window, source, dest, _ = setup
    order = expected_order(source)
    for folder in ["Beach", "Family"]:
        window._ignore_activations_until = 0
        window.folder_panel.clear_armed()
        double_click_folder(window, folder)
        wait_for_move(window)
    window._ignore_activations_until = 0
    window.undo()
    wait_for_move(window)
    assert (source / order[1]).exists() and (dest / "Beach" / order[0]).exists()
    window._ignore_activations_until = 0
    window.undo()
    wait_for_move(window)
    assert (source / order[0]).exists()
    assert window.current_video.name == order[0]


def test_undo_never_overwrites(setup):
    window, source, dest, _ = setup
    first = expected_order(source)[0]
    double_click_folder(window, "Beach")
    wait_for_move(window)
    (source / first).write_bytes(b"a new file with the same name")
    window._ignore_activations_until = 0
    window.undo()
    wait_for_move(window)
    stem, ext = first.rsplit(".", 1)
    assert (source / first).read_bytes() == b"a new file with the same name"
    assert (source / f"{stem} (1).{ext}").exists()
    assert window.current_video.name == f"{stem} (1).{ext}"


def test_undo_when_file_is_gone_reports_and_forgets_it(setup):
    window, source, dest, _ = setup
    first = expected_order(source)[0]
    double_click_folder(window, "Beach")
    wait_for_move(window)
    (dest / "Beach" / first).unlink()
    window._ignore_activations_until = 0
    window.undo()
    wait_for_move(window)
    assert window.status_line.kind() == "error"
    assert "no longer in Beach" in window.status_line.text()
    assert not window.player_panel.undo_button.isEnabled()  # U-5


def test_changing_source_clears_undo(setup, tmp_path):
    window, source, *_ = setup
    double_click_folder(window, "Beach")
    wait_for_move(window)
    other = tmp_path / "Other"
    other.mkdir()
    window.set_source(other)
    assert not window.player_panel.undo_button.isEnabled()  # U-6


# -- delete (section 7) ---------------------------------------------------------------------
def confirm_delete(window) -> None:
    """Second press of Delete, after the double-click interval has passed."""
    window._delete_pending_since -= 5
    window.request_delete()


def test_delete_needs_a_second_press_and_goes_to_trash(setup, tmp_path):
    window, source, dest, log_path = setup
    order = expected_order(source)
    panel = window.player_panel

    panel.delete_button.click()
    assert window.delete_pending and panel.delete_button.text() == "Confirm delete"
    assert window.status_line.kind() == "danger"
    assert (source / order[0]).exists()

    panel.delete_button.click()  # too fast: a double-click isn't a confirmation (D-3)
    assert (source / order[0]).exists() and window.delete_pending

    confirm_delete(window)
    wait_for_move(window)
    assert not (source / order[0]).exists()
    assert (tmp_path / ".Trash" / order[0]).exists()
    assert window.current_video.name == order[1]  # next video plays
    assert window.status_line.text().startswith(f"🗑 Moved {order[0]} to the Trash")
    assert panel.delete_button.text() == "Delete"
    entry = window.log_panel.entries()[0]
    assert entry.in_trash and entry.folder == "Trash"  # D-6

    # Undo brings it back from the Trash and plays it (U-2).
    window._ignore_activations_until = 0
    window.undo()
    wait_for_move(window)
    assert (source / order[0]).exists() and not (tmp_path / ".Trash" / order[0]).exists()
    assert window.current_video.name == order[0]
    assert window.status_line.text() == f"↩ Brought {order[0]} back from the Trash"


@pytest.mark.parametrize("action", ["escape", "next", "folder", "timeout", "undo"])
def test_pending_delete_is_cancelled(setup, action):
    window, source, *_ = setup
    first = expected_order(source)[0]
    window.request_delete()
    assert window.delete_pending
    if action == "escape":
        window.press_escape()
        assert window.status_line.text() == "Delete cancelled."
    elif action == "next":
        window.next_video()
    elif action == "folder":
        click_folder(window, "Beach")
    elif action == "timeout":
        window._delete_timer.setInterval(10)
        window._delete_timer.start()
        wait_until(lambda: not window.delete_pending, 2)
    elif action == "undo":
        window.undo()
    assert not window.delete_pending
    assert window.player_panel.delete_button.text() == "Delete"
    assert (source / first).exists()
    # The next press starts over: it asks again instead of deleting.
    window.request_delete()
    assert window.delete_pending and (source / first).exists()


def test_failed_delete_keeps_video(setup, tmp_path):
    window, source, *_ = setup
    first = expected_order(source)[0]

    def broken_trash(path):
        raise OSError("the Trash refused the file")

    window._trash = broken_trash
    window.request_delete()
    confirm_delete(window)
    wait_for_move(window)
    assert window.status_line.kind() == "error" and "refused" in window.status_line.text()
    assert (source / first).exists() and window.current_video.name == first
    assert not window.player_panel.undo_button.isEnabled()


def test_cmd_z_and_cmd_delete_keys(setup, tmp_path):
    window, source, dest, _ = setup
    order = expected_order(source)
    window.show()
    window.activateWindow()
    if not QTest.qWaitForWindowActive(window, 3000):
        pytest.skip("offscreen platform couldn't activate the window")
    cmd = Qt.KeyboardModifier.ControlModifier  # Qt's Ctrl is ⌘ on macOS

    QTest.keyClick(window, Qt.Key.Key_Backspace, cmd)
    assert window.delete_pending
    window._delete_pending_since -= 5
    QTest.keyClick(window, Qt.Key.Key_Backspace, cmd)
    wait_for_move(window)
    assert (tmp_path / ".Trash" / order[0]).exists()

    window._ignore_activations_until = 0
    QTest.keyClick(window, Qt.Key.Key_Z, cmd)
    wait_for_move(window)
    assert (source / order[0]).exists() and window.current_video.name == order[0]

    # K-9: while renaming, ⌘Z and ⌘⌫ belong to the text field.
    window.player_panel.rename_change_button.click()
    assert not any(s.isEnabled() for s in window._shortcuts)
