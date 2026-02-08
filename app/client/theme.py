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
    padding: 10px 10px;
    font-size: 16px;
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