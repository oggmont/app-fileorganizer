"""Small widgets shared by both panels."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QSizePolicy, QWidget


def make_button(text: str, icon: QIcon | None = None, small: bool = False, name: str | None = None) -> QPushButton:
    """A button that never takes keyboard focus, so the arrow and Enter keys keep working (K-1)."""
    button = QPushButton(text)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if icon is not None:
        button.setIcon(icon)
    if small:
        button.setProperty("small", True)
    if name:
        button.setObjectName(name)
    return button


class ElidedLabel(QLabel):
    """A one-line label that shortens its text with "…" to fit, with the full text as a tooltip."""

    def __init__(self, text: str = "", mode: Qt.TextElideMode = Qt.TextElideMode.ElideMiddle, name: str | None = None):
        super().__init__()
        self._full_text = ""
        self._mode = mode
        if name:
            self.setObjectName(name)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(20)
        self.set_full_text(text)

    def full_text(self) -> str:
        return self._full_text

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self.setToolTip(text)
        self._refresh()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        self.setText(self.fontMetrics().elidedText(self._full_text, self._mode, max(0, self.width())))


class EditField(QLineEdit):
    """A text field where Esc asks to cancel the edit, used by Rename (R-5) and New folder (F-12)."""

    cancel_requested = Signal()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape and not self.isReadOnly():
            self.cancel_requested.emit()
            return
        super().keyPressEvent(event)


def set_dynamic_property(widget: QWidget, name: str, value) -> None:
    """Set a dynamic property and re-apply the style sheet rules that depend on it."""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
