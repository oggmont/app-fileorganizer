from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fileorganizer.movelog import LogEntry, MoveLog


def test_append_writes_tab_separated_lines(tmp_path):
    log = MoveLog(tmp_path / "moves_log.txt")
    when = datetime(2026, 11, 12, 14, 32, 5)
    entry = log.append(Path("/src/a.mp4"), Path("/dest/Beach/a.mp4"), 1234, when)
    assert (tmp_path / "moves_log.txt").read_text() == "2026-11-12 14:32:05\t/src/a.mp4\t/dest/Beach/a.mp4\t1234\n"
    assert entry.name == "a.mp4"
    assert entry.folder == "Beach"


def test_latest_is_newest_first_limited_and_skips_broken_lines(tmp_path):
    path = tmp_path / "moves_log.txt"
    log = MoveLog(path)
    for i in range(5):
        log.append(Path(f"/s/{i}.mp4"), Path(f"/d/F/{i}.mp4"), i, datetime(2026, 1, 1, 0, 0, i))
    with path.open("a") as f:
        f.write("not a log line\n")
    entries = log.latest(limit=3)
    assert [e.name for e in entries] == ["4.mp4", "3.mp4", "2.mp4"]


def test_missing_file_means_no_entries(tmp_path):
    assert MoveLog(tmp_path / "none.txt").latest() == []


def test_tabs_in_paths_dont_break_lines():
    entry = LogEntry(datetime(2026, 1, 1), "/s/a\tb.mp4", "/d/F/a\tb.mp4", 1)
    assert LogEntry.from_line(entry.to_line()) is not None


def test_trash_entries_show_as_trash():
    entry = LogEntry(datetime(2026, 1, 1), "/s/a.mp4", "/Users/me/.Trash/a.mp4", 1)
    assert entry.in_trash and entry.folder == "Trash"
    assert not LogEntry(datetime(2026, 1, 1), "/s/a.mp4", "/d/Beach/a.mp4", 1).in_trash
