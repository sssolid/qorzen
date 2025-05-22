from __future__ import annotations
'\nImage preview widget for the Media Processor Plugin.\n\nThis module provides a widget for displaying image previews with \nzoom controls and status messages.\n'
import io
import os
from typing import Optional, Union
from PySide6.QtCore import Qt, Signal, Slot, QSize, QRectF, QPointF, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QBrush, QColor, QResizeEvent, QPaintEvent, QWheelEvent, QMouseEvent
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QSizePolicy
class ImagePreviewWidget(QWidget):
    zoomChanged = Signal(float)
    def __init__(self, logger: Optional[object]=None, parent: Optional[QWidget]=None) -> None:
        super().__init__(parent)
        self._logger = logger
        self._image: Optional[QImage] = None
        self._pixmap: Optional[QPixmap] = None
        self._zoom_factor: float = 1.0
        self._min_zoom: float = 0.1
        self._max_zoom: float = 5.0
        self._zoom_step: float = 0.1
        self._panning: bool = False
        self._pan_start_pos: Optional[QPointF] = None
        self._offset: QPointF = QPointF(0, 0)
        self._loading: bool = False
        self._error_text: Optional[str] = None
        self._status_text: Optional[str] = None
        self._init_ui()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._loading_angle = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading_animation)
        self._loading_timer.setInterval(50)
    def _init_ui(self) -> None:
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(240, 240, 240))
        self.setPalette(pal)
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(event.rect(), QColor(240, 240, 240))
        if self._pixmap and (not self._loading):
            scaled_width = self._pixmap.width() * self._zoom_factor
            scaled_height = self._pixmap.height() * self._zoom_factor
            x = (self.width() - scaled_width) / 2 + self._offset.x()
            y = (self.height() - scaled_height) / 2 + self._offset.y()
            painter.drawPixmap(QRectF(x, y, scaled_width, scaled_height), self._pixmap, QRectF(0, 0, self._pixmap.width(), self._pixmap.height()))
            painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.SolidLine))
            painter.drawRect(QRectF(x, y, scaled_width, scaled_height))
            zoom_text = f'{int(self._zoom_factor * 100)}%'
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(10, 20, zoom_text)
        elif self._loading:
            self._draw_loading_spinner(painter)
        elif self._error_text:
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(event.rect(), Qt.AlignCenter, self._error_text)
        elif self._status_text:
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(event.rect(), Qt.AlignCenter, self._status_text)
        else:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(event.rect(), Qt.AlignCenter, 'No image loaded')
        painter.end()
    def _draw_loading_spinner(self, painter: QPainter) -> None:
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(50, min(self.width(), self.height()) / 4)
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self._loading_angle)
        for i in range(12):
            painter.save()
            painter.rotate(i * 30)
            opacity = 0.2 + 0.8 * (i / 12)
            painter.setPen(QPen(QColor(80, 80, 80, int(opacity * 255)), 3))
            painter.drawLine(radius - 10, 0, radius, 0)
            painter.restore()
        painter.resetTransform()
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(QRectF(-100, radius + 10, 200, 30).translated(center_x, center_y), Qt.AlignCenter, 'Loading...')
        painter.restore()
    def _update_loading_animation(self) -> None:
        self._loading_angle = (self._loading_angle + 10) % 360
        self.update()
    def wheelEvent(self, event: QWheelEvent) -> None:
        if not self._pixmap or self._loading:
            return
        delta = event.angleDelta().y()
        zoom_delta = self._zoom_step if delta > 0 else -self._zoom_step
        center_x = self.width() / 2 + self._offset.x()
        center_y = self.height() / 2 + self._offset.y()
        mouse_x = event.position().x()
        mouse_y = event.position().y()
        rel_x = mouse_x - center_x
        rel_y = mouse_y - center_y
        old_zoom = self._zoom_factor
        self._zoom_factor = max(self._min_zoom, min(self._max_zoom, self._zoom_factor + zoom_delta))
        if old_zoom != self._zoom_factor:
            zoom_ratio = self._zoom_factor / old_zoom
            self._offset.setX(mouse_x - (mouse_x - self._offset.x()) * zoom_ratio)
            self._offset.setY(mouse_y - (mouse_y - self._offset.y()) * zoom_ratio)
            self.zoomChanged.emit(self._zoom_factor)
            self.update()
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._pixmap and (not self._loading):
            self._panning = True
            self._pan_start_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and self._panning:
            self._panning = False
            self._pan_start_pos = None
            self.setCursor(Qt.ArrowCursor)
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._panning and self._pan_start_pos:
            delta = event.position() - self._pan_start_pos
            self._offset += delta
            self._pan_start_pos = event.position()
            self.update()
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._offset = QPointF(0, 0)
        self.update()
    def load_image(self, file_path: str) -> bool:
        try:
            if not os.path.exists(file_path):
                self.set_error(f'File not found: {file_path}')
                return False
            image = QImage(file_path)
            if image.isNull():
                self.set_error(f'Invalid image format: {file_path}')
                return False
            self._image = image
            self._pixmap = QPixmap.fromImage(image)
            self._zoom_factor = 1.0
            self._offset = QPointF(0, 0)
            self._error_text = None
            self._status_text = None
            self.update()
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error loading image: {str(e)}')
            self.set_error(f'Error loading image: {str(e)}')
            return False
    def load_image_data(self, data: bytes) -> bool:
        try:
            image = QImage()
            if not image.loadFromData(data):
                self.set_error('Invalid image data')
                return False
            self._image = image
            self._pixmap = QPixmap.fromImage(image)
            self._zoom_factor = 1.0
            self._offset = QPointF(0, 0)
            self._error_text = None
            self._status_text = None
            self.update()
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f'Error loading image data: {str(e)}')
            self.set_error(f'Error loading image data: {str(e)}')
            return False
    def set_loading(self, loading: bool) -> None:
        if self._loading == loading:
            return
        self._loading = loading
        if loading:
            self._loading_timer.start()
        else:
            self._loading_timer.stop()
        self.update()
    def set_error(self, error_text: str) -> None:
        self._error_text = error_text
        self._status_text = None
        self._image = None
        self._pixmap = None
        self.update()
    def set_status(self, status_text: str) -> None:
        self._status_text = status_text
        self._error_text = None
        self.update()
    def clear(self) -> None:
        self._image = None
        self._pixmap = None
        self._zoom_factor = 1.0
        self._offset = QPointF(0, 0)
        self._error_text = None
        self._status_text = None
        self._loading = False
        self.update()
    def get_image(self) -> Optional[QImage]:
        return self._image
    def set_zoom(self, zoom_factor: float) -> None:
        if not self._pixmap:
            return
        self._zoom_factor = max(self._min_zoom, min(self._max_zoom, zoom_factor))
        self.zoomChanged.emit(self._zoom_factor)
        self.update()
    def reset_view(self) -> None:
        self._zoom_factor = 1.0
        self._offset = QPointF(0, 0)
        self.zoomChanged.emit(self._zoom_factor)
        self.update()
    def sizeHint(self) -> QSize:
        return QSize(400, 300)