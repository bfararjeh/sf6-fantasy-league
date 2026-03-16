from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class BlueScreen(QWidget):
    '''
    Displays a blue screen with a full stack trace should something go wrong.
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
        self.text.setPlainText(
            f"Unfortunately, the application has crashed.\n\n"
            f"Below is the full stack trace, you can report this issue on "
            f"https://github.com/bfararjeh/sf6-fantasy-league/issues\n\n{error_text}"
        )
        self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        self.setFocus()
