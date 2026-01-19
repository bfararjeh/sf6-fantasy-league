import sys
import traceback

from pathlib import Path

from PyQt6.QtWidgets import QApplication

from PyQt6.QtGui import QIcon

from PyQt6.QtCore import QLockFile

from app.client.app import FantasyApp


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

    # custom excepthook for bluescreening and error logging
    sys.excepthook = excepthook

    app.setWindowIcon(
        QIcon(
            str(resource_path("app/client/assets/icons/logo.png"))
        )
    )

    window = FantasyApp()
    window.show()

    sys.exit(app.exec())


def excepthook(exc_type, exc, tb):
    error_text = "".join(traceback.format_exception(exc_type, exc, tb))

    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, FantasyApp):
            widget.blue_screen.show_error(error_text)
            break

def resource_path(relative: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / relative
    return Path(relative)

if __name__ == "__main__":
    main()