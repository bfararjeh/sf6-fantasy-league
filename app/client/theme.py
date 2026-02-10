from PyQt6.QtGui import QColor

# main theme
PRIMARY_BG_COLOR = QColor("#10194D")
PRIMARY_FG_COLOR = QColor("#FFFFFF")
TEXT_COLOR = QColor("#000000")
BASE_COLOR = QColor("#1E2466")
PLACEHOLDER_TEXT_COLOR = QColor("#AAAAAA")
TOOLTIP_BG_COLOR = QColor("#282E7A")
TOOLTIP_TEXT_COLOR = QColor("#FFFFFF")
HIGHLIGHT_COLOR = QColor("#FFD166")
HIGHLIGHTED_TEXT_COLOR = QColor("#10194D")
BUTTON_BG_COLOR = QColor("#1A2066")
BUTTON_TEXT_COLOR = QColor("#FFFFFF")
BRIGHT_TEXT_COLOR = QColor("#FF4D6D")

# banner
BANNER_LABEL_STYLESHEET = f"""
QLabel {{
    background-color: {QColor("#4200FF").lighter(110).name()};
    color: {QColor("#FFFFFF").name()};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 500;
}}
"""

# theme col w/ text
BUTTON_STYLESHEET_A = f"""
QPushButton {{
    background-color: {QColor("#4200FF").name()};
    color: {QColor("#ffffff").name()};
    border-radius: 6px;
    padding: 8px 8px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {QColor("#4200FF").lighter(120).name()};
}}
QPushButton:pressed {{
    background-color: {QColor("#4200FF").darker(120).name()};
}}
QPushButton:disabled {{
    background-color: {QColor("#444F9C").name()};
    color: #888888;
}}
"""

# theme col for icon
BUTTON_STYLESHEET_B = f"""
QPushButton {{
    background-color: {QColor("#4200FF").name()};
    border-radius: 6px;
}}
QPushButton:hover {{
    background-color: {QColor("#4200FF").lighter(120).name()};
}}
QPushButton:pressed {{
    background-color: {QColor("#4200FF").darker(120).name()};
}}
QPushButton:disabled {{
    background-color: {QColor("#6C6FA3").name()};
}}
"""

# logout for icon
BUTTON_STYLESHEET_C = f"""
QPushButton {{
    background-color: {QColor("#700000").name()};
    border-radius: 6px;
}}
QPushButton:hover {{
    background-color: {QColor("#700000").lighter(120).name()};
}}
QPushButton:pressed {{
    background-color: {QColor("#700000").darker(120).name()};
}}
QPushButton:disabled {{
    background-color: {QColor("#505050").name()};
}}
"""

# owner tag, leave button
BUTTON_STYLESHEET_D = """
            font-size: 18px;
            font-weight: bold;
            color: white;

            background-color: #b0131e;

            padding: 6px 10px;
            border-radius: 8px;
        """

SCROLL_STYLESHEET = f"""
QScrollBar:vertical {{
    background: {QColor("#10194D").darker(130).name()};
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {QColor("#5A1DFF").name()};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {QColor("#5A1DFF").lighter(120).name()};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}
"""
