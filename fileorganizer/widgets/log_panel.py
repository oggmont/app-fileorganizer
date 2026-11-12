"""The small "Recent moves" panel in the left section (G-1, G-2)."""

from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QTextBrowser, QVBoxLayout

from ..movelog import PANEL_LIMIT, LogEntry


class LogPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("logFrame")
        self.setFixedHeight(150)
        self._entries: list[LogEntry] = []

        title = QLabel("RECENT MOVES")
        title.setObjectName("logTitle")

        self._view = QTextBrowser()
        self._view.setObjectName("logView")
        self._view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._view.setOpenLinks(False)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.document().setDocumentMargin(6)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title)
        layout.addWidget(self._view, 1)

    def set_entries(self, entries: list[LogEntry]) -> None:
        """`entries` must be newest first."""
        self._entries = list(entries[:PANEL_LIMIT])
        self._render()

    def add_entry(self, entry: LogEntry) -> None:
        self._entries.insert(0, entry)
        del self._entries[PANEL_LIMIT:]
        self._render()

    def entries(self) -> list[LogEntry]:
        return list(self._entries)

    def _render(self) -> None:
        if not self._entries:
            self._view.setHtml('<span style="color:#777777">No moves yet.</span>')
            return
        rows = [
            '<div style="margin:0 0 4px 0">'
            f'<span style="color:#777777">{e.when:%H:%M:%S}</span>&nbsp;&nbsp;'
            f'<span style="color:#bbbbbb">{escape(e.name)}</span>'
            ' <span style="color:#777777">→</span> '
            f'<span style="color:{"#ff7b72" if e.in_trash else "#8fd18f"}">{escape(e.folder)}</span></div>'
            for e in self._entries
        ]
        self._view.setHtml(
            '<div style="font-family:Menlo, Monaco, monospace; font-size:12px">' + "".join(rows) + "</div>"
        )
