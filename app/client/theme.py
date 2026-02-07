from PyQt6.QtGui import QColor, QFont

# ----------------------
# Core UI Colors
# ----------------------
PRIMARY_BG_COLOR = QColor("#10194D")         # Main window background
PRIMARY_FG_COLOR = QColor("#FFFFFF")         # Main window foreground / text
SECONDARY_BG_COLOR = QColor("#1A2066")       # Panels, sidebars
TEXT_COLOR = QColor("#000000")               # Default text (contrasts with dark BG)
DISABLED_TEXT_COLOR = QColor("#888888")      # For disabled/inactive text
BASE_COLOR = QColor("#1E2466")               # Background for inputs
ALTERNATE_BASE_COLOR = QColor("#282E7A")     # Alternate row backgrounds (tables, lists)
PLACEHOLDER_TEXT_COLOR = QColor("#AAAAAA")   # Placeholder text (subtle)
TOOLTIP_BG_COLOR = QColor("#282E7A")         # Tooltip background
TOOLTIP_TEXT_COLOR = QColor("#FFFFFF")       # Tooltip text

# ----------------------
# Highlights & Accent
# ----------------------
ACCENT_COLOR = QColor("#FFD166")             # Primary accent (selection, active elements)
HIGHLIGHT_COLOR = QColor("#FFD166")          # Text / item highlight
HIGHLIGHTED_TEXT_COLOR = QColor("#10194D")   # Text over highlight
BUTTON_BG_COLOR = QColor("#1A2066")          # Default button background
BUTTON_TEXT_COLOR = QColor("#FFFFFF")        # Default button text
BRIGHT_TEXT_COLOR = QColor("#FF4D6D")        # Text that needs strong contrast


# ----------------------
# Button Stylesheet
# ----------------------
button_bg = QColor("#4200FF")
button_text = QColor("#ffffff")
disabled = QColor("#444F9C")
border = 6

BUTTON_STYLESHEET = f"""
QPushButton {{
    background-color: {button_bg.name()};
    color: {button_text.name()};
    border-radius: {border}px;
    padding: 10px 10px;
    font-size: 16px;
}}
QPushButton:hover {{
    background-color: {button_bg.lighter(120).name()};
}}
QPushButton:pressed {{
    background-color: {button_bg.darker(120).name()};
}}
QPushButton:disabled {{
    background-color: {disabled.name()};
    color: #888888;
}}
"""

FILE_DIALOG_STYLESHEET = f"""
        QFileDialog {{
            background-color: {BASE_COLOR.name()};
            color: {PRIMARY_FG_COLOR.name()};
        }}

        QListView, QTreeView {{
            background-color: {BASE_COLOR.name()};
            color: {PRIMARY_FG_COLOR.name()};
            selection-background-color: {HIGHLIGHT_COLOR.name()};
            selection-color: {HIGHLIGHTED_TEXT_COLOR.name()};
        }}

        QComboBox {{
            background-color: {BASE_COLOR.name()};
            color: {PRIMARY_FG_COLOR.name()};
            selection-background-color: {HIGHLIGHT_COLOR.name()};
            selection-color: {HIGHLIGHTED_TEXT_COLOR.name()};
        }}

        QComboBox QAbstractItemView {{
            background-color: {BASE_COLOR.name()};
            color: {PRIMARY_FG_COLOR.name()};
            selection-background-color: {HIGHLIGHT_COLOR.name()};
            selection-color: {HIGHLIGHTED_TEXT_COLOR.name()};
        }}

        QHeaderView {{
            background-color: {BASE_COLOR.name()};
            color: {TEXT_COLOR.name()};
        }}

        QPushButton {{
            background-color: {BUTTON_BG_COLOR.name()};
            color: {BUTTON_TEXT_COLOR.name()};
        }}
        """