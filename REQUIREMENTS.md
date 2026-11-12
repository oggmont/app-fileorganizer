# Video File Organizer: Requirements

A desktop app for sorting a large number of videos into folders: watch a video on the
left, click a destination folder on the right, and the video is moved there.

## 1. Window and layout

| ID | Requirement |
|----|-------------|
| L-1 | The app opens filling the whole screen (maximized or full screen). |
| L-2 | The window has two side-by-side sections: **Left** (player, log, status bar) and **Folders** (right). |
| L-3 | A draggable vertical divider between the sections changes their widths. |
| L-4 | Both sections fill the full height of the window, top to bottom. |
| L-5 | Each section has its own button to change its location (source folder / destination root). |
| L-6 | From top to bottom, the left section contains: a top bar with the **Change source folder** button and folder path, the **Undo** and **Delete** buttons, and the current file info; the **rename** row; the **video player** with its controls, the **move log** (small), and the **status bar**. The status bar sits inside the left section so the folder list keeps the full window height. |
| L-7 | A mockup of the layout is in [`ui-mockup.png`](ui-mockup.png). |

## 2. Player (left section)

| ID | Requirement |
|----|-------------|
| P-1 | A **Change source folder** button opens a folder picker. |
| P-2 | The app lists only the video files directly inside the source folder. Subfolders aren't searched. Hidden files are skipped, including the `._name.mp4` files macOS leaves on external drives. |
| P-3 | Supported extensions: `.mp4`, `.m4v`, `.mov`, `.avi`, `.mkv`, `.wmv`, `.flv`, `.webm`, `.mpg`, `.mpeg`, `.3gp`. Matching ignores upper/lower case. |
| P-4 | Videos are ordered by file size, **biggest first**. Each next video is the next smaller one. |
| P-5 | Only one video is loaded at a time: the first one in that order. |
| P-6 | The video starts playing automatically as soon as it is loaded. |
| P-7 | Controls: **Play/Pause**, **Stop**, **Rewind** (−10 s), **Forward** (+10 s), **Skip** (next video), and a seek bar showing current time and duration. |
| P-8 | When a video reaches the end, it **replays from the start**. It keeps looping until the user presses **Stop**, presses **Skip**, or moves it. |
| P-9 | **Stop** stops playback and keeps the same video loaded. **Play** starts it again. |
| P-10 | The current video changes **only** when (a) it is moved to a folder, (b) the user presses **Skip**, (c) the user presses the **Left/Right** arrow keys (section 8), (d) it is moved to the Trash, or (e) a video is brought back with **Undo** (section 7). |
| P-11 | **Skip** (or **→**) loads the next smaller video. **←** loads the previous one, which is the next bigger. Neither touches the file on disk. |
| P-12 | The player shows the current file name, its size, and its position (e.g. `12 / 340`). |
| P-13 | When no videos are left, the player shows a clear "No more videos" message. |
| P-14 | If a file can't be decoded, an error appears in the status bar and the user can skip the file. The app must not crash. |

## 3. Folders section (right)

| ID | Requirement |
|----|-------------|
| F-1 | A small **Change destination folder** button opens a folder picker. |
| F-2 | The section lists only the folders directly inside the chosen destination folder, sorted by name. Subfolders aren't searched. |
| F-3 | The list fills the full height of the section and scrolls when there are more folders than fit. |
| F-4 | Hidden folders (names starting with `.`) are not shown. |
| F-5 | If the source folder is one of the listed folders, it is not shown as a destination. |
| F-6 | The list shows two different states. The **keyboard cursor** (moved with ↑/↓) is an outline around the row. The **selected** folder (after a first click or first Enter) is a filled highlight. |

## 4. Move flow

There are **no pop-up dialogs**. All prompts and alerts appear in the status bar.

| ID | Requirement |
|----|-------------|
| M-1 | **First click** (or first **Enter**) on a folder selects it (highlight). The status bar shows: *"Click or press Enter on `<folder>` again to move `<video>`"*. |
| M-2 | **Second click** (or second **Enter**) on the same selected folder confirms the move. |
| M-3 | A quick **double-click** on a folder moves the video right away, with no separate selection step. Pressing **Enter twice** does the same from the keyboard. |
| M-4 | Clicking a different folder moves the selection to that folder and updates the status bar message. Nothing is moved. |
| M-5 | Only **Esc**, or changing either location, clears the selection. Nothing is moved. Moving or skipping a video does **not** clear it. |
| M-6 | Once the move is confirmed, the folder's color changes to a "moving" state. When the move finishes, it goes back to the normal selected color. |
| M-7 | Before moving, the player stops and releases the file, so the file is not locked. |
| M-8 | The file is moved into the selected folder. This also works when the destination is on another drive. |
| M-9 | If a file with the same name already exists in the destination, it is **never overwritten**. A suffix is added instead (e.g. `name (1).mp4`). |
| M-10 | **Verification:** the file exists in the destination with the same size as the original, and it no longer exists in the source folder. |
| M-11 | On success, the status bar shows *"Moved `<video>` → `<folder>`"*. The message stays for **5 seconds**, or until a new message replaces it. |
| M-12 | Right after a successful move, the next video loads and starts playing. Playback doesn't wait for the 5-second message. |
| M-12a | After a move, and after Skip or **← / →**, the same folder **stays selected**. One click or one **Enter** on it then moves the new video there. This makes it quick to send several videos in a row to the same folder. |
| M-12b | Once the 5-second "Moved" message ends, the status bar goes back to the prompt for the selected folder: *"Click or press Enter on `<folder>` to move `<video>`"*. |
| M-13 | If the move or verification fails, the error appears in the status bar and stays until a new message replaces it. The video stays where it was and the app does not advance. |
| M-14 | Clicks are ignored while a move is in progress, so the same file is never moved twice. |
| M-15 | A double-click, or a fast Enter-Enter, never moves more than one video. This matters once a folder stays selected (M-12a), where a single click already moves a video. After a move starts and after it ends, clicks and Enter on folders are ignored for one double-click interval (about half a second). The same applies to Undo, so a double-click on Undo brings back only one video. |
| M-16 | A move between drives runs in the background, so the window doesn't freeze. The app can't be closed while a move is running. |

## 5. Move log

| ID | Requirement |
|----|-------------|
| G-1 | The left section has a small log panel, below the player controls, listing the latest moves, newest first. |
| G-2 | Each entry shows the time, the file name, and the destination folder name (e.g. `14:32:05  holiday.mp4 → Beach`). If the file was renamed (M-9), the entry shows the new name. |
| G-3 | Every successful move is also added to a text file in the project root: `moves_log.txt`. This includes Undo (a move back to the source folder) and Delete (a move to the Trash). Nothing is ever removed from this file. |
| G-4 | Each line in the file holds: date and time, full source path, full destination path, and file size, separated by tabs. |
| G-5 | At startup, the log panel loads the latest entries (up to 100) from `moves_log.txt`. |
| G-6 | Failed moves are not written to the log. They appear only in the status bar. |

## 6. Rename

The rename row only renames the current video. It never moves the file to another folder.

| ID | Requirement |
|----|-------------|
| R-1 | The left section has a rename row above the player: a text field with the current video's name, a **Change** button, and an **OK** button. |
| R-2 | The text field shows the name without the extension. The extension (e.g. `.mp4`) is shown next to it, can't be edited, and is always kept. |
| R-3 | The text field is read-only by default. **Change** makes it editable and selects the text. **OK** stays disabled until Change is pressed. |
| R-4 | **OK** (or Enter) renames the file in the same source folder. The field becomes read-only again. |
| R-5 | **Esc** while editing cancels the edit and restores the current name. Nothing is renamed. |
| R-6 | The new name is rejected, with an error in the status bar and nothing renamed, when it is empty, unchanged, contains `/` or `:`, starts with `.` (the file would become hidden), or matches a file that already exists in the folder. An existing file is **never overwritten**. A change of upper/lower case only (`clip` → `Clip`) is allowed. |
| R-7 | Renaming keeps the same video loaded. Playback continues from the same position. |
| R-8 | On success, the status bar shows *"Renamed `<old>` → `<new>`"* for 5 seconds, or until a new message replaces it. |
| R-9 | Clicking a folder in the right section, Skip, or changing a location cancels an edit in progress. |
| R-10 | Renames are not written to the move log (section 5), and Undo doesn't reverse them. |

## 7. Undo and delete

Two buttons sit in the top bar of the left section, between the folder path and the video
info: **Undo** and **Delete**.

### Undo (⌘Z)

| ID | Requirement |
|----|-------------|
| U-1 | The app keeps a list of the moves and deletes made since the source folder was chosen. |
| U-2 | **Undo** (or **⌘Z**) reverses the most recent one: the video comes back into the source folder, from its destination folder or from the Trash. Pressing it again reverses the one before, and so on. |
| U-3 | The video that comes back gets its original name and becomes the current video. It plays from the start. The folder selection stays as it was. |
| U-4 | Undo never overwrites. If a file with the original name is back in the source folder, a suffix is added (`name (1).mp4`), as in M-9. The move back is verified like any move (M-10). |
| U-5 | If the video can't be brought back (e.g. it was moved away in Finder, or the Trash was emptied), the status bar shows an error and that step is removed from the list. If the failure might be temporary (e.g. the drive isn't connected), the step stays so it can be tried again. |
| U-6 | The list is cleared when the source folder changes, so Undo always brings videos back into the folder on the left. It isn't kept between launches. |
| U-7 | The button is disabled when there is nothing to undo. Its tooltip names the video and where it will come back from. With nothing to undo, ⌘Z shows *"Nothing to undo."* |
| U-8 | On success the status bar shows *"↩ Brought `<video>` back from `<folder>`"* (or *"from the Trash"*) for 5 seconds. Messages after a move or delete end with *"· ⌘Z to undo"*. |

### Delete (⌘⌫)

| ID | Requirement |
|----|-------------|
| D-1 | **Delete** (or **⌘⌫**; ⌘ + forward delete works too) moves the current video to the **macOS Trash**. The app never deletes a file permanently. |
| D-2 | Delete needs confirmation, without a pop-up. The first press turns the button red (*"Confirm delete"*), and the status bar shows *"Press Delete again (or ⌘⌫) to move `<video>` to the Trash. Esc cancels."* The second press moves the video to the Trash. |
| D-3 | A double-click on the button, or ⌘⌫ pressed twice very quickly, doesn't count as a confirmation. The second press must come at least one double-click interval (about half a second) after the first. |
| D-4 | Before moving, the player releases the file (as in M-7). The app checks that the file left the folder and is in the Trash. Then the next video plays, as after a move (M-12). |
| D-5 | A pending delete is cancelled by **Esc**, after 5 seconds without confirmation, or by any other action: changing video, a folder click or Enter, Undo, Rename, or changing a location. After that, the next press asks again. |
| D-6 | The delete is written to the move log with the path inside the Trash as its destination. The log panel shows it as `name → Trash` in red. |
| D-7 | If the Trash refuses the file (e.g. some network drives have no Trash), an error appears in the status bar and the video stays where it was. It is never deleted permanently. |

## 8. Keyboard controls

The whole sorting flow works from the keyboard: **← / →** to pick a video, **↑ / ↓** to
pick a folder, then **Enter, Enter** to move.

| Key | Action |
|-----|--------|
| **→** | Next video (next smaller). Same as **Skip**. |
| **←** | Previous video (next bigger). |
| **↓** | Move the folder cursor down one row. |
| **↑** | Move the folder cursor up one row. |
| **Enter** (1st) | Select the folder under the cursor. Same as a first click. |
| **Enter** (2nd) | Move the video into the selected folder. Same as a second click. Once a folder is selected, every later Enter moves the current video there. |
| **Esc** | Cancel a pending delete; otherwise clear the folder selection, or cancel a rename in progress. |
| **⌘Z** | Undo the last move or delete (U-2). |
| **⌘⌫** | Delete: the first press asks, the second moves the video to the Trash (D-2). |

| ID | Requirement |
|----|-------------|
| K-1 | The keys above work anywhere in the window. The folder list doesn't need focus first. |
| K-2 | **← / →** change the playing video. They do not seek inside the video; use the Rewind/Forward buttons for that. |
| K-3 | At the first video, **←** does nothing. At the last video, **→** does nothing. In both cases the status bar shows *"First video"* or *"Last video"*. |
| K-4 | **← / →** keep the current folder selection, the same as **Skip** (M-5, M-12a). |
| K-5 | **↑ / ↓** stop at the top and bottom of the list; they don't wrap around. The list scrolls to keep the cursor visible. On first load, the cursor is on the first folder. |
| K-6 | Moving the cursor away from the selected folder clears the selection (as in M-4). The next **Enter** selects the folder under the cursor. |
| K-7 | **Enter** follows the same rules as clicks (M-1 to M-3). There is no time limit between the two presses. |
| K-8 | After a move, the cursor and the selection both stay on the same folder. A single **Enter** sends the next video there too (M-12a). |
| K-9 | While the rename field is being edited, arrows, Enter, Esc, ⌘Z and ⌘⌫ belong to the text field (Enter = OK, Esc = cancel, ⌘Z undoes typing, ⌘⌫ deletes text). They don't control videos, folders or files. |
| K-10 | Keys pressed while a move, undo or delete is in progress are ignored (as in M-14). |
| K-11 | Holding down a key repeats only **↑ / ↓**. Holding **Enter** doesn't move a stream of videos, and holding **← / →** doesn't skip through dozens of videos. |

## 9. Non-functional

| ID | Requirement |
|----|-------------|
| N-1 | Runs on macOS 13 (Ventura), Intel x86_64, as on the developer's machine. |
| N-2 | Plays common formats (MP4/H.264, H.265, AVI with Xvid/DivX/MJPEG, MKV, WMV) without the user installing extra codecs. |
| N-3 | A large folder (1,000+ files) is listed in under 2 seconds. Listing reads file sizes only, never file contents. |
| N-4 | The app remembers the last source and destination folders between launches. |
| N-5 | No file is ever deleted permanently: Delete moves videos to the macOS Trash, and Undo can bring them back. Besides moving, trashing and renaming videos, the only thing the app writes to disk is `moves_log.txt` (plus its saved settings, N-4). |
| N-6 | The app can be opened with a double-click in Finder, from `Video File Organizer.app` (built by `make_app.sh`). In the Dock and menu bar it shows its own name and icon, not "Python". |

## 10. Recommended technology

**Python 3.14 + PySide6 (Qt 6.11) with QtMultimedia.**

- Qt 6's multimedia uses a built-in **FFmpeg** backend on macOS. The PySide6 wheels ship
  it, so AVI, MKV, WMV and others play without installing anything else. (Java and
  web/Electron players can't do this; see below.)
- Qt widgets that fit the requirements:
  - `QSplitter` for the resizable divider.
  - `QListWidget` for the folder list. It reports both single clicks and double-clicks.
  - `QStatusBar.showMessage(text, 5000)` for the 5-second status messages.
  - A small `QListWidget` for the log panel.
  - `QLineEdit.setReadOnly()` for the rename field, and `os.rename` for the rename itself.
  - `QFile.moveToTrash()` for Delete. It uses the same Trash as Finder, including `.Trashes`
    on external drives, and reports where the file landed, which Undo needs.
  - `QShortcut` with `Qt.ApplicationShortcut` for keys that work anywhere in the window (K-1).
    On macOS, Qt's `Ctrl+Z` and `Ctrl+Backspace` are ⌘Z and ⌘⌫.
    It is turned off while the rename field is being edited (K-9).
  - `QMediaPlayer.setLoops(QMediaPlayer.Infinite)` for replaying a video until it is stopped.
  - `showMaximized()` / `showFullScreen()` to fill the screen.
- `shutil.move` handles moves between drives. `os.path.getsize` is used for sorting and
  verification.
- **Fallback:** if a specific file won't decode, swap the player for `python-vlc`.
  VLC 3.0.20 is already installed in `/Applications`.

> Note: the default `python3` on this Mac is 3.15, and PySide6 doesn't support it yet.
> Create the virtual environment with `python3.14`, which is already installed.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
pip install PySide6
```

### Why not the alternatives

| Option | Video support on macOS | Verdict |
|--------|-----------------------|---------|
| Java Swing | No video at all. You need JavaFX Media (MP4 only, **no AVI**) or VLCJ (needs VLC and native setup). | Most work, least reliable. |
| JS / Electron | Chromium `<video>` plays MP4/WebM, but **not AVI**, WMV, or most MKV. AVI would need FFmpeg transcoding or a libmpv add-on. | Fine for MP4 only. |
| Python + PySide6 | FFmpeg backend is built in. Handles MP4, AVI, MKV, MOV and WMV. | **Recommended.** |
| Python + python-vlc | VLC plays almost anything. Depends on VLC.app being installed. | Good fallback. |
