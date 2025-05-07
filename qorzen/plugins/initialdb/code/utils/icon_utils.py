from typing import Union

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QSize
from pathlib import Path

from ..config.settings import get_resource_path


def colorize_svg_icon(svg_path: str, color: QColor, size: QSize = QSize(24, 24)) -> QIcon:
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    return QIcon(pixmap)

def load_icon(name: str, color: Union[str, QColor], size: QSize = QSize(24, 24)) -> QIcon:
    # Convert color string to QColor if needed
    if isinstance(color, str):
        color = QColor(color)

    svg_path = Path(get_resource_path("resources/ui_icons") / f"{name}.svg")
    return colorize_svg_icon(str(svg_path), color, size)
