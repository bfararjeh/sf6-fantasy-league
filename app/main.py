import sys
import traceback

from pathlib import Path

from PyQt6.QtWidgets import QApplication

from PyQt6.QtGui import QIcon, QPalette, QFontDatabase, QFont

from PyQt6.QtCore import QLockFile

from app.client.app import FantasyApp

from app.client.theme import *


APP_NAME = "SF6FantasyLeague"

def main():
    appdata_dir = Path.home() / "AppData" / "Roaming" / APP_NAME
    appdata_dir.mkdir(parents=True, exist_ok=True)

    # creating lock file to prevent multiple applications
    lock_file_path = appdata_dir / "app.lock"
    lock = QLockFile(str(lock_file_path))
    lock.setStaleLockTime(0)

    if not lock.tryLock():
        sys.exit(0)

    app = QApplication(sys.argv)

    try:
        # apply global palette
        palette = app.palette()
        palette.setColor(QPalette.ColorRole.Window, PRIMARY_BG_COLOR)
        palette.setColor(QPalette.ColorRole.WindowText, PRIMARY_FG_COLOR)
        palette.setColor(QPalette.ColorRole.Base, BASE_COLOR)
        palette.setColor(QPalette.ColorRole.AlternateBase, BASE_COLOR.lighter(110))
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
        print("Failed to load theme:", e)

    try:
        regular_id = QFontDatabase.addApplicationFont(
            str(resource_path("app/client/assets/fonts/centurygothic.ttf"))
        )
        bold_id = QFontDatabase.addApplicationFont(
            str(resource_path("app/client/assets/fonts/centurygothic_bold.ttf"))
        )

        if regular_id == -1 or bold_id == -1:
            raise Exception("One of the fonts failed to load.")

        regular_family = QFontDatabase.applicationFontFamilies(regular_id)[0]

        # manually include bold font
        bold_font = QFont(QFontDatabase.applicationFontFamilies(bold_id)[0], 12)
        bold_font.setBold(True)

        # set the default app font to regular
        app.setFont(QFont(regular_family, 12))

        print(f"Loaded font family: {regular_family}")

    except Exception as e:
        print("Failed to load font:", e)

    # custom excepthook for bluescreening and error logging
    sys.excepthook = excepthook

    window = FantasyApp()
    window.show()

    app.setWindowIcon(
        QIcon(
            str(resource_path("app/client/assets/icons/logo.ico"))
        )
    )

    window.setWindowIcon(
        QIcon(
            str(resource_path("app/client/assets/icons/logo.ico"))
        )
    )

    sys.exit(app.exec())


def excepthook(exc_type, exc, tb):
    error_text = "".join(traceback.format_exception(exc_type, exc, tb))

    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, FantasyApp):
            widget.blue_screen.show_error(error_text)
            break

def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / relative_path)
    return str(Path(relative_path).resolve())

if __name__ == "__main__":
    main()