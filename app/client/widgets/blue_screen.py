from PyQt6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QTextEdit
)

class BlueScreen(QWidget):
    '''
    Responsible for displaying a bluescreen with a full stack trace should
    something go wrong. Better safe than sorry!
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.text = QTextEdit(self)
        self.text.setReadOnly(True)
        self.text.setStyleSheet("""
            color: white;
            font-family: Consolas;
            font-size: 16px;
            background: #150DF7;
            border: none;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text)

        self.hide()

    def show_error(self, error_text: str):
        self.text.setPlainText(f"Unfortunately, the application has crashed.\n\nBelow is the full stack trace, you can report this issue on https://github.com/bfararjeh/sf6-fantasy-league/issues\n\n{error_text}")

        self.setGeometry(self.parent().rect())

        self.show()
        self.raise_()
        self.setFocus()