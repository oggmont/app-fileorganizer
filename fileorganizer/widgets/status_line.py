"""The status bar at the bottom of the left section. All prompts and alerts go here (section 4)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from ..theme import STATUS_COLORS
from .common import ElidedLabel

MESSAGE_MS = 5000  # M-11, R-8

# Callback returning the default text and its kind, shown when no other message is up.
IdleProvider = Callable[[], tuple[str, str]]


class StatusLine(QFrame):
    """Shows one message at a time.

    - Timed messages (e.g. "Moved ...") stay for 5 s, or until a new message replaces them.
    - Errors and prompts stay until a new message replaces them.
    - With nothing else to show, the idle text from `idle_provider` is shown, e.g. the
      "Click or press Enter on <folder> to move <video>" prompt (M-12b).
    """

    def __init__(self, idle_provider: IdleProvider):
        super().__init__()
        self.setObjectName("statusLine")
        self.setFixedHeight(30)
        self._idle_provider = idle_provider
        self._mode = "idle"  # idle | timed | sticky
        self._kind = "muted"

        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._label = ElidedLabel(mode=Qt.TextElideMode.ElideRight)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)
        layout.addWidget(self._dot)
        layout.addWidget(self._label, 1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.show_idle)

    # -- public API ---------------------------------------------------------
    def show_message(self, text: str, kind: str = "prompt", timeout_ms: int | None = None) -> None:
        self._timer.stop()
        self._set(text, kind)
        if timeout_ms:
            self._mode = "timed"
            self._timer.start(timeout_ms)
        else:
            self._mode = "sticky"

    def show_idle(self) -> None:
        self._timer.stop()
        text, kind = self._idle_provider()
        self._set(text, kind)
        self._mode = "idle"

    def refresh(self) -> None:
        """Update to the current idle text, unless a timed message is still showing."""
        if self._mode != "timed":
            self.show_idle()

    def text(self) -> str:
        return self._label.full_text()

    def kind(self) -> str:
        return self._kind

    # -- internals ----------------------------------------------------------
    def _set(self, text: str, kind: str) -> None:
        color = STATUS_COLORS.get(kind, STATUS_COLORS["muted"])
        self._kind = kind
        self._label.set_full_text(text)
        self._label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._dot.setStyleSheet(f"background: {color}; border-radius: 4px;")
