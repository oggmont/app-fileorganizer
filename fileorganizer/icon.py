"""The app icon, drawn in code: a yellow folder with a play button on a blue tile.

Used for the window/Dock icon at runtime and by scripts/make_icon.py for the .app bundle.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPolygonF

from .theme import CURSOR, SELECTED


def draw_icon(size: int = 1024) -> QImage:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    s = size / 1024  # everything below is laid out on a 1024 grid

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)

    # Rounded tile, sized like standard macOS app icons (824 of 1024).
    tile = QRectF(100 * s, 100 * s, 824 * s, 824 * s)
    gradient = QLinearGradient(tile.topLeft(), tile.bottomLeft())
    gradient.setColorAt(0, QColor("#3b93ff"))
    gradient.setColorAt(1, QColor("#0a4cad"))
    painter.setBrush(gradient)
    painter.drawRoundedRect(tile, 185 * s, 185 * s)

    # Folder: tab, then body.
    painter.setBrush(QColor("#e8b94f"))
    painter.drawRoundedRect(QRectF(232 * s, 292 * s, 240 * s, 110 * s), 36 * s, 36 * s)
    painter.setBrush(QColor(CURSOR))
    painter.drawRoundedRect(QRectF(232 * s, 350 * s, 560 * s, 390 * s), 44 * s, 44 * s)

    # Play button on the folder.
    painter.setBrush(QColor(SELECTED))
    painter.drawPolygon(QPolygonF([QPointF(450 * s, 455 * s), QPointF(450 * s, 635 * s), QPointF(605 * s, 545 * s)]))
    painter.end()
    return image
