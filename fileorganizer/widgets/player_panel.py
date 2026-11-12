"""The top of the left section: source folder, rename row, video and controls (sections 2 and 6)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QStackedWidget,
    QStyle,
    QStyleOptionSlider,
    QVBoxLayout,
    QWidget,
)

from ..fileops import Video, format_size
from .common import EditField, ElidedLabel, make_button, set_dynamic_property

SEEK_STEP_MS = 10_000  # P-7


def format_time(ms: int) -> str:
    seconds = max(0, ms) // 1000
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes:02}:{seconds:02}"


class SeekSlider(QSlider):
    """A slider that jumps straight to where you click on it."""

    seek_requested = Signal(int)

    def __init__(self):
        super().__init__(Qt.Orientation.Horizontal)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setRange(0, 0)
        self.sliderMoved.connect(self.seek_requested)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.maximum() > 0:
            option = QStyleOptionSlider()
            self.initStyleOption(option)
            style = self.style()
            groove = style.subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderGroove, self)
            handle = style.subControlRect(QStyle.ComplexControl.CC_Slider, option, QStyle.SubControl.SC_SliderHandle, self)
            pos = event.position().toPoint()
            if not handle.contains(pos):
                span = max(1, groove.width() - handle.width())
                x = int(pos.x() - groove.x() - handle.width() / 2)
                value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), x, span)
                self.setValue(value)
                self.seek_requested.emit(value)
        super().mousePressEvent(event)


class PlayerPanel(QWidget):
    change_source_clicked = Signal()
    undo_clicked = Signal()
    delete_clicked = Signal()
    skip_clicked = Signal()
    rename_submitted = Signal(str)
    rename_mode_changed = Signal(bool)
    playback_error = Signal(str)

    def __init__(self):
        super().__init__()
        self._editing = False
        self._stem = ""
        self._pending_position: int | None = None
        self._current_name = ""

        style = self.style()
        icon = style.standardIcon

        # -- top bar: source folder and current file (P-1, P-12) -------------
        self.change_source_button = make_button("Change source folder", icon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.change_source_button.clicked.connect(self.change_source_clicked)
        self._source_label = ElidedLabel(name="mutedLabel")
        self._name_label = ElidedLabel(name="videoName")
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._details_label = QLabel()
        self._details_label.setObjectName("videoDetails")

        # Undo and Delete sit between the location and the video info (L-6, section 7).
        self.undo_button = make_button("↩ Undo", small=True, name="undoButton")
        self.undo_button.setToolTip("Undo the last move or delete (⌘Z)")
        self.undo_button.setEnabled(False)
        self.undo_button.clicked.connect(self.undo_clicked)
        self.delete_button = make_button("Delete", icon(QStyle.StandardPixmap.SP_TrashIcon), small=True, name="deleteButton")
        self.delete_button.setToolTip("Move this video to the Trash (⌘⌫). Asks to confirm first.")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_clicked)

        top_bar = _bar("topBar", (14, 10, 14, 10))
        top_bar.layout().addWidget(self.change_source_button)
        top_bar.layout().addWidget(self._source_label, 1)
        top_bar.layout().addWidget(self.undo_button)
        top_bar.layout().addWidget(self.delete_button)
        top_bar.layout().addSpacing(6)
        top_bar.layout().addWidget(self._name_label, 2)
        top_bar.layout().addWidget(self._details_label)

        # -- rename row (section 6) -------------------------------------------
        name_caption = QLabel("Name")
        name_caption.setObjectName("mutedLabel")
        name_caption.setFixedWidth(44)
        self.rename_field = EditField()  # read-only and unfocusable until Change is pressed (R-3)
        self.rename_field.setReadOnly(True)
        self.rename_field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rename_field.returnPressed.connect(self._submit_rename)
        self.rename_field.cancel_requested.connect(self.cancel_rename)
        self._ext_label = QLabel()
        self._ext_label.setObjectName("extLabel")
        self._ext_label.setMinimumWidth(40)
        self.rename_change_button = make_button("Change", small=True)
        self.rename_change_button.clicked.connect(self.start_rename)
        self.rename_ok_button = make_button("OK", small=True, name="okButton")
        self.rename_ok_button.setEnabled(False)
        self.rename_ok_button.clicked.connect(self._submit_rename)

        rename_row = _bar("renameRow", (14, 8, 14, 8))
        rename_row.layout().setSpacing(8)
        rename_row.layout().addWidget(name_caption)
        rename_row.layout().addWidget(self.rename_field, 1)
        rename_row.layout().addWidget(self._ext_label)
        rename_row.layout().addWidget(self.rename_change_button)
        rename_row.layout().addWidget(self.rename_ok_button)

        # -- video ---------------------------------------------------------------
        self.video_widget = QVideoWidget()
        self.video_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.video_widget.setStyleSheet("background: #000000;")
        self._message_label = QLabel()
        self._message_label.setObjectName("videoMessage")
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._message_label.setWordWrap(True)
        self._stack = QStackedWidget()
        self._stack.setObjectName("videoStack")
        self._stack.setStyleSheet("#videoStack { background: #000000; }")
        self._stack.addWidget(self.video_widget)
        self._stack.addWidget(self._message_label)

        # -- controls (P-7) --------------------------------------------------------
        self.play_button = make_button("", icon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setToolTip("Play / Pause")
        self.play_button.clicked.connect(self.toggle_play)
        self.stop_button = make_button("", icon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.setToolTip("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.rewind_button = make_button("10s", icon(QStyle.StandardPixmap.SP_MediaSeekBackward))
        self.rewind_button.setToolTip("Rewind 10 seconds")
        self.rewind_button.clicked.connect(lambda: self.seek_by(-SEEK_STEP_MS))
        self.forward_button = make_button("10s", icon(QStyle.StandardPixmap.SP_MediaSeekForward))
        self.forward_button.setToolTip("Forward 10 seconds")
        self.forward_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.forward_button.clicked.connect(lambda: self.seek_by(SEEK_STEP_MS))
        self._time_label = QLabel("00:00")
        self._time_label.setObjectName("timeLabel")
        self.seek_slider = SeekSlider()
        self.seek_slider.seek_requested.connect(self._seek_to)
        self._duration_label = QLabel("00:00")
        self._duration_label.setObjectName("timeLabel")
        loop_label = QLabel("🔁 Loop")
        loop_label.setObjectName("loopLabel")
        loop_label.setToolTip("Videos replay until you stop, skip or move them (P-8)")
        self.skip_button = make_button("Skip", icon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.skip_button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.skip_button.setToolTip("Next video (→)")
        self.skip_button.clicked.connect(self.skip_clicked)

        controls = QFrame()
        controls.setObjectName("controls")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(8)
        for widget in (self.play_button, self.stop_button, self.rewind_button, self.forward_button):
            controls_layout.addWidget(widget)
        controls_layout.addSpacing(6)
        controls_layout.addWidget(self._time_label)
        controls_layout.addWidget(self.seek_slider, 1)
        controls_layout.addWidget(self._duration_label)
        controls_layout.addSpacing(6)
        controls_layout.addWidget(loop_label)
        controls_layout.addWidget(self.skip_button)

        video_area = QWidget()
        video_layout = QVBoxLayout(video_area)
        video_layout.setContentsMargins(14, 10, 14, 0)
        video_layout.setSpacing(0)
        video_layout.addWidget(self._stack, 1)
        video_layout.addWidget(controls)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(top_bar)
        layout.addWidget(rename_row)
        layout.addWidget(video_area, 1)

        # -- media player ------------------------------------------------------------
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)
        self.player.setLoops(_INFINITE_LOOPS)  # P-8: replay until stopped, skipped or moved
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.mediaStatusChanged.connect(self._on_media_status)
        self.player.errorOccurred.connect(self._on_error)

        self.set_source_path(None)
        self.set_video(None, 0, 0)
        self.show_message("Choose a source folder to start.")

    # -- source and current video -----------------------------------------------------
    def set_source_path(self, path: Path | None) -> None:
        self._source_label.set_full_text(str(path) if path else "No folder chosen")

    def set_video(self, video: Video | None, position: int, total: int) -> None:
        """Update the file info and rename row for `video` (P-12, R-2)."""
        if self._editing:
            self._end_rename()
        if video is None:
            self._current_name = ""
            self._stem = ""
            self._name_label.set_full_text("")
            self._details_label.setText(f"0 / {total}" if total else "")
            self.rename_field.setText("")
            self._ext_label.setText("")
            self.rename_change_button.setEnabled(False)
            return
        self._current_name = video.name
        self._stem = video.path.stem
        self._name_label.set_full_text(video.name)
        self._details_label.setText(f"· {format_size(video.size)} · {position} / {total}")
        self.rename_field.setText(self._stem)
        self.rename_field.setCursorPosition(0)
        self._ext_label.setText(video.path.suffix)
        self.rename_change_button.setEnabled(True)

    def play_file(self, path: Path, position_ms: int = 0, autoplay: bool = True) -> None:
        """Load `path` and start playing it (P-6), optionally from `position_ms` (R-7)."""
        self._pending_position = position_ms if position_ms > 0 else None
        self._stack.setCurrentWidget(self.video_widget)
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        if autoplay:
            self.player.play()
        else:
            self.player.pause()

    def release(self) -> None:
        """Stop and let go of the file so it can be moved (M-7)."""
        self.player.stop()
        self.player.setSource(QUrl())
        self._pending_position = None

    def show_message(self, text: str) -> None:
        """Replace the video with a message, e.g. "No more videos" (P-13)."""
        self.release()
        self._message_label.setText(text)
        self._stack.setCurrentWidget(self._message_label)
        self._on_duration(0)
        self._on_position(0)

    def message(self) -> str | None:
        return self._message_label.text() if self._stack.currentWidget() is self._message_label else None

    # -- playback controls (P-7, P-9) ----------------------------------------------------
    def toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif not self.player.source().isEmpty():
            self.player.play()

    def stop(self) -> None:
        self.player.stop()

    def seek_by(self, delta_ms: int) -> None:
        if self.player.source().isEmpty():
            return
        duration = self.player.duration()
        target = max(0, self.player.position() + delta_ms)
        if duration > 0:
            target = min(target, max(0, duration - 500))
        self.player.setPosition(target)

    def position(self) -> int:
        return self.player.position()

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def is_stopped(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState

    # -- undo and delete (section 7) ---------------------------------------------------------
    def set_delete_pending(self, pending: bool) -> None:
        """D-2: the Delete button turns red and asks for the second press."""
        self.delete_button.setText("Confirm delete" if pending else "Delete")
        set_dynamic_property(self.delete_button, "danger", pending)

    # -- rename (section 6) ----------------------------------------------------------------
    @property
    def editing(self) -> bool:
        return self._editing

    def start_rename(self) -> None:
        if self._editing or not self._current_name:
            return
        self._editing = True
        self.rename_field.setReadOnly(False)
        self.rename_field.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        set_dynamic_property(self.rename_field, "editing", True)
        self.rename_ok_button.setEnabled(True)
        self.rename_change_button.setEnabled(False)
        self.rename_field.setFocus(Qt.FocusReason.OtherFocusReason)
        self.rename_field.selectAll()
        self.rename_mode_changed.emit(True)

    def cancel_rename(self) -> None:
        """R-5, R-9: stop editing and put the current name back."""
        if self._editing:
            self._end_rename()

    def finish_rename(self) -> None:
        """Called after a successful rename."""
        if self._editing:
            self._end_rename()

    def _end_rename(self) -> None:
        self._editing = False
        self.rename_field.setText(self._stem)
        self.rename_field.setCursorPosition(0)
        self.rename_field.setReadOnly(True)
        self.rename_field.clearFocus()
        self.rename_field.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        set_dynamic_property(self.rename_field, "editing", False)
        self.rename_ok_button.setEnabled(False)
        self.rename_change_button.setEnabled(bool(self._current_name))
        self.rename_mode_changed.emit(False)

    def _submit_rename(self) -> None:
        if self._editing:
            self.rename_submitted.emit(self.rename_field.text())

    # -- player signals ----------------------------------------------------------------
    def _seek_to(self, value: int) -> None:
        self.player.setPosition(value)

    def _on_position(self, position: int) -> None:
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self._time_label.setText(format_time(position))

    def _on_duration(self, duration: int) -> None:
        self.seek_slider.setRange(0, max(0, duration))
        self._duration_label.setText(format_time(duration))

    def _on_state(self, state) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        pixmap = QStyle.StandardPixmap.SP_MediaPause if playing else QStyle.StandardPixmap.SP_MediaPlay
        self.play_button.setIcon(self.style().standardIcon(pixmap))

    def _on_media_status(self, status) -> None:
        loaded = (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia)
        if self._pending_position is not None and status in loaded:
            self.player.setPosition(self._pending_position)
            self._pending_position = None

    def _on_error(self, error, message: str) -> None:
        if error == QMediaPlayer.Error.NoError:
            return
        name = self._current_name or "this video"
        self.playback_error.emit(f"✗ Can't play {name}: {message or error.name}. Press → or Skip for the next one.")


def _infinite_loops() -> int:
    loops = getattr(QMediaPlayer, "Loops", None)
    value = getattr(loops, "Infinite", -1) if loops is not None else -1
    return int(getattr(value, "value", value))


_INFINITE_LOOPS = _infinite_loops()


def _bar(name: str, margins: tuple[int, int, int, int]) -> QWidget:
    bar = QWidget()
    bar.setObjectName(name)
    bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(*margins)
    layout.setSpacing(10)
    return bar
