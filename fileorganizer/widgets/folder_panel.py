"""The right section: destination folders (section 3)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileIconProvider,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from ..theme import CURSOR, HOVER, MOVING, SELECTED, SEPARATOR, TEXT
from .common import EditField, ElidedLabel, make_button

ROW_HEIGHT = 35
SELECTED_HINT = "selected · Enter / click to move"
MOVING_HINT = "moving…"


def _folder_icon() -> QIcon:
    icon = QFileIconProvider().icon(QFileIconProvider.IconType.Folder)
    return icon if not icon.isNull() else QIcon()


class FolderDelegate(QStyledItemDelegate):
    """Paints each row: fill for the selected folder, outline for the keyboard cursor (F-6)."""

    def __init__(self, folder_list: FolderList):
        super().__init__(folder_list)
        self._list = folder_list

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        return QSize(option.rect.width(), ROW_HEIGHT)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        lst = self._list
        rect = option.rect
        row = index.row()
        selected = row == lst.armed_row
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if selected:
            painter.fillRect(rect, QColor(MOVING if lst.moving else SELECTED))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, QColor(HOVER))
        painter.setPen(QColor(SEPARATOR))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        icon = index.data(Qt.ItemDataRole.DecorationRole)
        icon_rect = QRect(rect.left() + 14, rect.center().y() - 9, 18, 18)
        if isinstance(icon, QIcon) and not icon.isNull():
            icon.paint(painter, icon_rect)

        hint = ""
        hint_width = 0
        small = QFont(option.font)
        small.setPointSizeF(max(8.0, option.font.pointSizeF() - 2))
        if selected:
            hint = MOVING_HINT if lst.moving else SELECTED_HINT
            painter.setFont(small)
            hint_width = painter.fontMetrics().horizontalAdvance(hint) + 16

        text_left = icon_rect.right() + 10
        text_rect = QRect(text_left, rect.top(), max(0, rect.right() - text_left - hint_width - 8), rect.height())
        painter.setFont(option.font)
        painter.setPen(QColor("#ffffff" if selected else TEXT))
        name = painter.fontMetrics().elidedText(
            str(index.data(Qt.ItemDataRole.DisplayRole)), Qt.TextElideMode.ElideMiddle, text_rect.width()
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, name)

        if hint:
            painter.setFont(small)
            painter.setPen(QColor("#dbe8ff"))
            hint_rect = QRect(rect.right() - hint_width - 6, rect.top(), hint_width, rect.height())
            painter.drawText(hint_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, hint)

        if row == lst.currentRow():
            pen = QPen(QColor(CURSOR))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
        painter.restore()


class FolderList(QListWidget):
    """Folder list where every mouse press counts as one click.

    The second press of a double-click arrives as a double-click event, so it's
    treated as a second click: a double-click is "select, then move" (M-3).
    Qt's own selection isn't used; the selected folder is `armed_row`.
    """

    folder_clicked = Signal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("folderList")
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # keys are handled by window shortcuts (K-1)
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setItemDelegate(FolderDelegate(self))
        font = self.font()
        font.setPixelSize(14)
        self.setFont(font)
        self.armed_row = -1
        self.moving = False
        self._icon = _folder_icon()
        self.currentRowChanged.connect(lambda _row: self.viewport().update())

    def set_names(self, names: list[str]) -> None:
        self.clear()
        for name in names:
            self.addItem(QListWidgetItem(self._icon, name))

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            self.setCurrentRow(index.row())
            self.folder_clicked.emit(index.row())
        event.accept()

    def mouseDoubleClickEvent(self, event) -> None:
        self.mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        event.accept()


class FolderPanel(QWidget):
    change_dest_clicked = Signal()
    folder_clicked = Signal(int)
    new_folder_clicked = Signal()
    create_requested = Signal(str)
    new_folder_mode_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self._creating = False
        self.setObjectName("rightPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        title = QLabel("Folders")
        title.setObjectName("folderTitle")
        self._path_label = ElidedLabel(name="mutedLabel")
        self.change_button = make_button(
            "Change", self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon), small=True
        )
        self.change_button.setToolTip("Change destination folder")
        self.change_button.clicked.connect(self.change_dest_clicked)
        self.new_folder_button = make_button(
            "New folder", self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), small=True
        )
        self.new_folder_button.setToolTip("Create a folder in this list (⌘⇧N)")
        self.new_folder_button.setEnabled(False)
        self.new_folder_button.clicked.connect(self.new_folder_clicked)

        header = QWidget()
        header.setObjectName("folderHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 10, 14, 10)
        header_layout.setSpacing(10)
        header_layout.addWidget(title)
        header_layout.addWidget(self._path_label, 1)
        header_layout.addWidget(self.new_folder_button)
        header_layout.addWidget(self.change_button)

        # New folder row (F-9): hidden until New folder is pressed.
        caption = QLabel("New folder")
        caption.setObjectName("mutedLabel")
        self.new_folder_field = EditField()
        self.new_folder_field.setPlaceholderText("Folder name")
        self.new_folder_field.setProperty("editing", True)  # blue border, like the rename field while editing
        self.new_folder_field.returnPressed.connect(self._submit_new_folder)
        self.new_folder_field.cancel_requested.connect(self.cancel_new_folder)
        self.create_button = make_button("Create", small=True, name="okButton")
        self.create_button.clicked.connect(self._submit_new_folder)
        cancel_button = make_button("Cancel", small=True)
        cancel_button.clicked.connect(self.cancel_new_folder)
        self._new_folder_row = QWidget()
        self._new_folder_row.setObjectName("newFolderRow")
        self._new_folder_row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row_layout = QHBoxLayout(self._new_folder_row)
        row_layout.setContentsMargins(14, 8, 14, 8)
        row_layout.setSpacing(8)
        row_layout.addWidget(caption)
        row_layout.addWidget(self.new_folder_field, 1)
        row_layout.addWidget(self.create_button)
        row_layout.addWidget(cancel_button)
        self._new_folder_row.hide()

        self.list = FolderList()
        self.list.folder_clicked.connect(self.folder_clicked)

        self._empty_label = QLabel()
        self._empty_label.setObjectName("mutedLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._empty_label.hide()

        hint_items = [
            (["←", "→"], "video"), (["↑", "↓"], "folder"), (["Enter"], "select"),
            (["Enter"], "again:&nbsp;move"), (["⌘↵"], "open&nbsp;folder"), (["⌘↑"], "parent"),
            (["⌘⇧N"], "new&nbsp;folder"), (["Esc"], "clear"), (["⌘Z"], "undo"), (["⌘⌫"], "delete"),
        ]
        # Inside an item everything is joined with &nbsp;, so lines only wrap between items.
        hints = QLabel(" &nbsp; ".join("".join(_key(k) for k in keys) + label for keys, label in hint_items))
        hints.setObjectName("keyHints")
        hints.setTextFormat(Qt.TextFormat.RichText)
        hints.setContentsMargins(14, 8, 14, 8)
        hints.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(self._new_folder_row)
        layout.addWidget(self._empty_label)
        layout.addWidget(self.list, 1)
        layout.addWidget(hints)
        self.set_root(None)

    # -- new folder (F-8..F-14) --------------------------------------------------
    @property
    def creating(self) -> bool:
        return self._creating

    def start_new_folder(self) -> None:
        if self._creating:
            self.new_folder_field.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        self._creating = True
        self.new_folder_field.clear()
        self._new_folder_row.show()
        self.new_folder_field.setFocus(Qt.FocusReason.OtherFocusReason)
        self.new_folder_mode_changed.emit(True)

    def cancel_new_folder(self) -> None:
        """Hide the row without creating anything (F-12). Also used after a successful create."""
        if not self._creating:
            return
        self._creating = False
        self.new_folder_field.clearFocus()
        self.new_folder_field.clear()
        self._new_folder_row.hide()
        self.new_folder_mode_changed.emit(False)

    def _submit_new_folder(self) -> None:
        if self._creating:
            self.create_requested.emit(self.new_folder_field.text())

    # -- location -------------------------------------------------------------
    def set_root(self, path: Path | None) -> None:
        self._path_label.set_full_text(str(path) if path else "No folder chosen")

    def set_folders(self, names: list[str], message_if_empty: str = "", cursor_on: str | None = None) -> None:
        """Show `names`. The cursor goes to `cursor_on`, or stays on the same folder when it's
        still there, or starts at the top (K-5)."""
        previous = cursor_on if cursor_on is not None else self.cursor_name()
        self.list.armed_row = -1
        self.list.set_names(names)
        if names:
            row = names.index(previous) if previous in names else 0
            self.list.setCurrentRow(row)
            self._empty_label.hide()
            self.list.show()
        else:
            self._empty_label.setText(message_if_empty or "No folders here.")
            self._empty_label.show()
            self.list.hide()

    # -- cursor and selection --------------------------------------------------
    @property
    def armed_row(self) -> int:
        return self.list.armed_row

    def armed_name(self) -> str | None:
        return self.name_at(self.list.armed_row)

    def name_at(self, row: int) -> str | None:
        item = self.list.item(row) if row >= 0 else None
        return item.text() if item is not None else None

    def cursor_row(self) -> int:
        return self.list.currentRow()

    def cursor_name(self) -> str | None:
        return self.name_at(self.list.currentRow())

    def set_armed(self, row: int) -> None:
        self.list.armed_row = row
        self.list.viewport().update()

    def clear_armed(self) -> None:
        self.set_armed(-1)

    def set_moving(self, moving: bool) -> None:
        self.list.moving = moving
        self.list.viewport().update()

    def move_cursor(self, delta: int) -> bool:
        """Move the keyboard cursor; stops at the ends (K-5). Returns True if it moved."""
        count = self.list.count()
        if count == 0:
            return False
        current = self.list.currentRow()
        new = 0 if current < 0 else max(0, min(count - 1, current + delta))
        if new == current:
            return False
        self.list.setCurrentRow(new)
        self.list.scrollToItem(self.list.item(new))
        return True

    def names(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]


def _key(text: str) -> str:
    return (
        '<span style="background-color:#3a3a3a; color:#eeeeee; font-size:11px">'
        f"&nbsp;{text}&nbsp;</span>&nbsp;"
    )
