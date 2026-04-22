from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFontMetrics, QPixmap
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QLabel

from app.client.controllers.resource_path import ResourcePath
from app.client.controllers.sound_manager import SoundManager

REGION_SVG_MAP = {
    "Australia":          ("class", "Australia"),
    "Belgium":            ("id",    "BE"),
    "Brazil":             ("id",    "BR"),
    "Cameroon":           ("id",    "CM"),
    "Canada":             ("class", "Canada"),
    "Chile":              ("class", "Chile"),
    "China":              ("class", "China"),
    "Dominican Republic": ("id",    "DO"),
    "France":             ("class", "France"),
    "Italy":              ("class", "Italy"),
    "Hong Kong":          ("class", "China"),       # proxy: China
    "Japan":              ("class", "Japan"),
    "Norway":             ("class", "Norway"),
    "Saudi Arabia":       ("id",    "SA"),
    "Singapore":          ("id",    "MY"),           # proxy: Malaysia
    "South Korea":        ("id",    "KR"),
    "Sweden":             ("id",    "SE"),
    "Taiwan":             ("id",    "TW"),
    "UAE":                ("id",    "AE"),
    "United Kingdom":     ("class", "United Kingdom"),
    "United States":      ("class", "United States"),
    "Lebanon":                      ("id",    "LB"),
    "Germany":                      ("id",    "DE"),
    "South Africa":                 ("id",    "ZA"),
    "Netherlands":                 ("id",     "NL"),
    "Portugal":                 ("id",     "PT"),
}

def fit_text_to_width(label: QLabel, text: str, max_width: int,
                      min_font_size=2, max_font_size=40, bold=True):
    if not text or max_width <= 0:
        return
    font = label.font()
    font.setBold(bold)
    low, high, best_size = min_font_size, max_font_size, min_font_size
    while low <= high:
        mid = (low + high) // 2
        font.setPointSize(mid)
        if QFontMetrics(font).boundingRect(text).width() <= max_width:
            best_size = mid
            low = mid + 1
        else:
            high = mid - 1
    font.setPointSize(best_size)
    label.setFont(font)
    label.setText(text)

def set_status(widget, msg: str, code: int = 0):
    colors = {0: "#FFFFFF", 1: "#00ff0d", 2: "#FFD700"}
    sounds = {1: "success", 2: "error"}
    widget.status_label.setStyleSheet(f"""
        QLabel {{
            font-size: 16px;
            font-weight: bold;
            color: {colors.get(code, '#FFFFFF')};
        }}
    """)
    widget.status_label.setText(msg)


    if code in sounds:
        SoundManager.play(sounds[code])

    if hasattr(widget, "_status_timer") and widget._status_timer.isActive():
        widget._status_timer.stop()

    widget._status_timer = QTimer(widget)
    widget._status_timer.setSingleShot(True)
    widget._status_timer.timeout.connect(lambda: widget.status_label.setText(""))
    widget._status_timer.start(8000)

def _build_empty_label(scale=1):
    s = scale
    label = QLabel()
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    pixmap = QPixmap(str(ResourcePath.IMAGES / "empty_logo.png"))
    label.setPixmap(pixmap.scaled(
        100*s, 100*s,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    ))
    effect = QGraphicsOpacityEffect()
    effect.setOpacity(0.35)
    label.setGraphicsEffect(effect)
    return label
