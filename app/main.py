import sys
import traceback
from pathlib import Path

from PyQt6.QtCore import QLockFile
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QPalette
from PyQt6.QtWidgets import QApplication

from app.client.app import FantasyApp
from app.client.theme import *
from app.client.controllers.resource_path import ResourcePath

APP_NAME = "SF6FantasyLeague"

appdata_dir = Path.home() / "AppData" / "Roaming" / APP_NAME
appdata_dir.mkdir(parents=True, exist_ok=True)

def main():
    # creating lock file to prevent multiple applications
    lock_file_path = appdata_dir / "app.lock"
    lock = QLockFile(str(lock_file_path))
    lock.setStaleLockTime(0)

    if not lock.tryLock():
        sys.exit(0)

    app = QApplication(sys.argv)

    # custom theme stuff (font + colors)
    _setup_theme(app=app)

    # custom excepthook for bluescreening and error logging
    sys.excepthook = _excepthook

    window = FantasyApp()
    window.show()

    app.setWindowIcon(QIcon(str(ResourcePath.ICONS / "logo.ico")))
    window.setWindowIcon(QIcon(str(ResourcePath.ICONS / "logo.ico")))

    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Failed to launch app: {e}")

def _excepthook(exc_type, exc, tb):
    error_text = "".join(traceback.format_exception(exc_type, exc, tb))

    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, FantasyApp):
            widget.blue_screen.show_error(error_text)
            break

def _setup_theme(app):
    try:
        # apply global palette
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Window, PRIMARY_BG_COLOR)
        palette.setColor(QPalette.ColorRole.WindowText, PRIMARY_FG_COLOR)
        palette.setColor(QPalette.ColorRole.Base, BASE_COLOR)
        palette.setColor(QPalette.ColorRole.ToolTipBase, TOOLTIP_BG_COLOR)
        palette.setColor(QPalette.ColorRole.ToolTipText, TOOLTIP_TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.PlaceholderText, PLACEHOLDER_TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.Text, TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.Button, BUTTON_BG_COLOR)
        palette.setColor(QPalette.ColorRole.ButtonText, BUTTON_TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.BrightText, BRIGHT_TEXT_COLOR)
        palette.setColor(QPalette.ColorRole.Highlight, HIGHLIGHT_COLOR)
        palette.setColor(QPalette.ColorRole.HighlightedText, HIGHLIGHTED_TEXT_COLOR)
        app.setPalette(palette)
    except Exception as e:
        print(f"Failed to load theme: {e}")

    try:
        regular_id = QFontDatabase.addApplicationFont(str(ResourcePath.FONTS / "centurygothic.ttf"))
        bold_id = QFontDatabase.addApplicationFont(str(ResourcePath.FONTS / "centurygothic_bold.ttf"))

        if regular_id == -1 or bold_id == -1:
            raise Exception("One of the fonts failed to load.")

        regular_family = QFontDatabase.applicationFontFamilies(regular_id)[0]
        bold_font = QFont(QFontDatabase.applicationFontFamilies(bold_id)[0], 12)
        bold_font.setBold(True)
        app.setFont(QFont(regular_family, 12))
    except Exception:
        print(f"Failed to load font: {e}")

if __name__ == "__main__":
    main()
