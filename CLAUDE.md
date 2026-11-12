# CLAUDE.md

Video File Organizer: a PySide6 (Qt 6) desktop app for macOS that plays videos from a source
folder and moves each one into a destination folder chosen with a click or the keyboard.

## Source of truth

- `REQUIREMENTS.md` is the specification. Requirements have IDs (P-4, M-12a, K-8, ...) and the
  code cites them in comments. When behavior changes, update REQUIREMENTS.md in the same change,
  and `ui-mockup.png` if the layout changes.
- `ui-mockup.png` is the layout to match.
- `Prompt.md` (gitignored) holds the user's original prompts. Read it for intent; don't commit it.
  macOS file names ignore upper/lower case, so writing `prompt.md` overwrites `Prompt.md`.

## Commands

```sh
./run.sh                                         # run the app (creates .venv on first run)
.venv/bin/pip install -r requirements-dev.txt    # test dependencies
.venv/bin/python -m pytest                       # all tests, about 10 s
```

- Use **Python 3.14**. The default `python3` on this Mac is 3.15, which PySide6 doesn't support.
- GUI tests run offscreen (`QT_QPA_PLATFORM=offscreen`, set in `tests/conftest.py`) and need
  `ffmpeg` to generate sample videos. Never launch the app on the user's screen to test.
  Use the offscreen tests, or `window.grab()` for a screenshot.

## Layout

- `fileorganizer/fileops.py`: listing, moving, renaming and Trash checks. No Qt imports; keep it that way.
- `fileorganizer/trash.py`: the one Qt call that moves a file to the macOS Trash.
- `fileorganizer/main_window.py`: all app state (videos, index, selected folder, moving flag),
  keyboard shortcuts, and the move and rename flow. Moves run on a `QThreadPool` worker.
- `fileorganizer/widgets/`: the panels. They show state and emit signals; the logic stays in
  `main_window.py`.
- `fileorganizer/movelog.py`: `moves_log.txt` in the project root (gitignored).
  `FILEORGANIZER_LOG` overrides the path; the tests use it.

## Rules that must not break

- **Never overwrite or permanently delete a user's video.** Every move, including Undo, goes
  through `fileops.move_verified` (unique name, then size and existence check). Every rename goes
  through `fileops.rename_video`. Delete only ever goes to the Trash, through
  `fileops.trash_verified` with `trash.move_to_trash`.
- **Tests must never use the real Trash.** `MainWindow(trash=...)` takes a fake (see
  `fake_trash` in `tests/test_main_window.py`). On this Mac, listing `~/.Trash` from a terminal
  is blocked ("Operation not permitted"), but an exact path inside it can be read and moved.
  That's how Undo brings files back.
- Move, Undo and Delete all run as a `FileJob` on a worker thread. The `busy` flag blocks other
  actions until it finishes.
- Keyboard shortcuts use `Qt.ApplicationShortcut`, and every button, list and slider is
  `NoFocus`. That way the arrows and Enter work anywhere (K-1) and no widget takes them. The
  rename field is the only focusable widget, and the shortcuts are turned off while it's being
  edited (K-9).
- The selected folder stays selected after a move or skip (M-12a). So one click or Enter moves
  a video, and `_block_activations_briefly` makes sure a double-click or a fast Enter-Enter
  moves only one video. Keep a test for this. The Delete confirmation has the same kind of guard
  (D-3).
- The media backend is FFmpeg (`QT_MEDIA_BACKEND=ffmpeg`, set in `app.py`). It's what plays
  AVI, MKV and WMV; AVFoundation doesn't.
