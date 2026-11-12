"""Dark theme matching ui-mockup.png."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# Colors shared with widgets that paint themselves.
TEXT = "#dddddd"
MUTED = "#9a9a9a"
SELECTED = "#0a64d8"   # folder selected with a first click / Enter (F-6)
MOVING = "#c77800"     # folder while a move is running (M-6)
CURSOR = "#ffd479"     # keyboard cursor outline (F-6)
SEPARATOR = "#2e2e2e"
HOVER = "#2f2f2f"

STATUS_COLORS = {
    "muted": MUTED,
    "prompt": "#ffd479",
    "ok": "#8fd18f",
    "error": "#ff7b72",
    "danger": "#ff7b72",  # delete confirmation (D-2)
}

STYLE_SHEET = f"""
QWidget {{ color: {TEXT}; font-size: 13px; }}
QMainWindow {{ background: #1e1e1e; }}
#leftPanel {{ background: #232323; }}
#rightPanel {{ background: #262626; }}
#topBar, #renameRow, #folderHeader {{ border-bottom: 1px solid #333333; }}
#mutedLabel {{ color: {MUTED}; font-size: 12px; }}
#videoName {{ color: #ffffff; font-weight: 600; font-size: 12px; }}
#videoDetails {{ color: #bbbbbb; font-size: 12px; }}
#extLabel {{ color: #888888; }}
#folderTitle {{ color: #eeeeee; font-weight: 600; }}

QPushButton {{
    background: #3a3a3a; border: 1px solid #4a4a4a; border-radius: 6px;
    padding: 5px 12px; color: #eeeeee;
}}
QPushButton:hover {{ background: #444444; }}
QPushButton:pressed {{ background: #2f2f2f; }}
QPushButton:disabled {{ color: #6f6f6f; background: #2e2e2e; border-color: #383838; }}
QPushButton[small="true"] {{ padding: 3px 10px; font-size: 12px; }}
QPushButton#okButton {{ background: #0a64d8; border-color: #1a74e8; color: #ffffff; }}
QPushButton#deleteButton {{ color: #ff9b94; }}
QPushButton#deleteButton:disabled {{ color: #6f6f6f; }}
QPushButton#deleteButton[danger="true"] {{ background: #b3261e; border-color: #d33a2f; color: #ffffff; }}
QPushButton#okButton:disabled {{ background: #1f3550; border-color: #2a4466; color: #7a8ea8; }}

QLineEdit {{
    background: #1a1a1a; border: 1px solid #3d3d3d; border-radius: 5px;
    padding: 5px 8px; color: #cccccc;
}}
QLineEdit[editing="true"] {{ border-color: #0a84ff; color: #ffffff; }}

#controls {{ background: #2c2c2c; border-radius: 4px; }}
#timeLabel {{ color: #aaaaaa; font-size: 12px; }}
#loopLabel {{ color: #7fb8ff; font-size: 12px; }}
QSlider::groove:horizontal {{ height: 5px; background: #444444; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: #0a84ff; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: #ffffff; width: 13px; height: 13px; margin: -4px 0; border-radius: 6px;
}}

#videoMessage {{ background: #000000; color: #bbbbbb; font-size: 18px; }}

#logFrame {{ border: 1px solid #353535; border-radius: 4px; background: #1c1c1c; }}
#logTitle {{
    color: #888888; font-size: 11px; font-weight: 600;
    padding: 6px 10px; border-bottom: 1px solid #303030;
}}
QTextBrowser#logView {{ background: transparent; border: none; }}

#statusLine {{ background: #2a2a2a; border-top: 1px solid #383838; }}
#keyHints {{ background: #222222; border-top: 1px solid #333333; color: #999999; font-size: 12px; }}

QListWidget#folderList {{ background: #262626; border: none; }}
QSplitter::handle {{ background: #151515; }}
QScrollBar:vertical {{ background: #262626; width: 10px; }}
QScrollBar::handle:vertical {{ background: #4a4a4a; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#232323"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1a1a1a"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#262626"))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor("#3a3a3a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#eeeeee"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(SELECTED))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    app.setPalette(palette)
    app.setStyleSheet(STYLE_SHEET)
