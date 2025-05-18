from __future__ import annotations

"""
Image preview widget for the Media Processor Plugin.

This module provides a widget for displaying image previews with 
zoom controls and status messages.
"""

import io
import os
from typing import Optional, Union

from PySide6.QtCore import Qt, Signal, Slot, QSize, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPixmap, QImage, QPainter, QPen, QBrush, QColor,
    QResizeEvent, QPaintEvent, QWheelEvent, QMouseEvent
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)


class ImagePreviewWidget(QWidget):
    """
    Widget for displaying image previews with zoom controls.

    Features:
    - Image loading from file or bytes
    - Zoom in/out with mouse wheel
    - Pan with mouse drag
    - Status and error messages
    - Loading indicator
    """

    # Signals
    zoomChanged = Signal(float)  # Current zoom level

    def __init__(
            self,
            logger: Optional[object] = None,
            parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the image preview widget.

        Args:
            logger: Optional logger instance
            parent: Parent widget
        """
        super().__init__(parent)

        self._logger = logger

        # Image data
        self._image: Optional[QImage] = None
        self._pixmap: Optional[QPixmap] = None
        self._zoom_factor: float = 1.0
        self._min_zoom: float = 0.1
        self._max_zoom: float = 5.0
        self._zoom_step: float = 0.1

        # For panning
        self._panning: bool = False
        self._pan_start_pos: Optional[QPointF] = None
        self._offset: QPointF = QPointF(0, 0)

        # Status
        self._loading: bool = False
        self._error_text: Optional[str] = None
        self._status_text: Optional[str] = None

        # Set up UI
        self._init_ui()

        # Enable mouse tracking for hover events
        self.setMouseTracking(True)

        # Set focus policy to accept focus
        self.setFocusPolicy(Qt.StrongFocus)

        # Set up loading animation timer
        self._loading_angle = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading_animation)
        self._loading_timer.setInterval(50)  # 20 fps

    def _init_ui(self) -> None:
        """Initialize the UI components."""
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Set background color
        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(240, 240, 240))
        self.setPalette(pal)

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Handle paint event to draw the image and status.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Fill background
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        # Draw image if available
        if self._pixmap and not self._loading:
            # Calculate centered position
            scaled_width = self._pixmap.width() * self._zoom_factor
            scaled_height = self._pixmap.height() * self._zoom_factor

            x = (self.width() - scaled_width) / 2 + self._offset.x()
            y = (self.height() - scaled_height) / 2 + self._offset.y()

            # Draw the pixmap
            painter.drawPixmap(
                QRectF(x, y, scaled_width, scaled_height),
                self._pixmap,
                QRectF(0, 0, self._pixmap.width(), self._pixmap.height())
            )

            # Draw border around image
            painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.SolidLine))
            painter.drawRect(QRectF(x, y, scaled_width, scaled_height))

            # Draw zoom indicator
            zoom_text = f"{int(self._zoom_factor * 100)}%"
            painter.setPen(QColor(80, 80, 80))
            painter.drawText(10, 20, zoom_text)

        # Draw loading indicator
        elif self._loading:
            self._draw_loading_spinner(painter)

        # Draw error message
        elif self._error_text:
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(
                event.rect(),
                Qt.AlignCenter,
                self._error_text
            )

        # Draw status message or placeholder
        elif self._status_text:
            painter.setPen(QColor(120, 120, 120))
            painter.drawText(
                event.rect(),
                Qt.AlignCenter,
                self._status_text
            )
        else:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(
                event.rect(),
                Qt.AlignCenter,
                "No image loaded"
            )

        painter.end()

    def _draw_loading_spinner(self, painter: QPainter) -> None:
        """
        Draw a loading spinner animation.

        Args:
            painter: Active QPainter instance
        """
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(50, min(self.width(), self.height()) / 4)

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self._loading_angle)

        # Draw spinner
        for i in range(12):
            painter.save()
            painter.rotate(i * 30)
            opacity = 0.2 + 0.8 * (i / 12)
            painter.setPen(QPen(QColor(80, 80, 80, int(opacity * 255)), 3))
            painter.drawLine(radius - 10, 0, radius, 0)
            painter.restore()

        # Draw loading text
        painter.resetTransform()
        painter.setPen(QColor(80, 80, 80))
        painter.drawText(
            QRectF(-100, radius + 10, 200, 30).translated(center_x, center_y),
            Qt.AlignCenter,
            "Loading..."
        )

        painter.restore()

    def _update_loading_animation(self) -> None:
        """Update the loading animation state and trigger a repaint."""
        self._loading_angle = (self._loading_angle + 10) % 360
        self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        Handle wheel event for zooming.

        Args:
            event: Wheel event
        """
        if not self._pixmap or self._loading:
            return

        # Calculate zoom delta
        delta = event.angleDelta().y()
        zoom_delta = self._zoom_step if delta > 0 else -self._zoom_step

        # Calculate mouse position relative to image center
        center_x = self.width() / 2 + self._offset.x()
        center_y = self.height() / 2 + self._offset.y()

        mouse_x = event.position().x()
        mouse_y = event.position().y()

        rel_x = mouse_x - center_x
        rel_y = mouse_y - center_y

        # Apply zoom
        old_zoom = self._zoom_factor
        self._zoom_factor = max(self._min_zoom, min(self._max_zoom, self._zoom_factor + zoom_delta))

        # Adjust offset to zoom around mouse position
        if old_zoom != self._zoom_factor:
            zoom_ratio = self._zoom_factor / old_zoom

            # Adjust offset
            self._offset.setX(mouse_x - (mouse_x - self._offset.x()) * zoom_ratio)
            self._offset.setY(mouse_y - (mouse_y - self._offset.y()) * zoom_ratio)

            # Emit signal
            self.zoomChanged.emit(self._zoom_factor)

            # Trigger repaint
            self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press event for panning.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton and self._pixmap and not self._loading:
            self._panning = True
            self._pan_start_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse release event for panning.

        Args:
            event: Mouse event
        """
        if event.button() == Qt.LeftButton and self._panning:
            self._panning = False
            self._pan_start_pos = None
            self.setCursor(Qt.ArrowCursor)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse move event for panning.

        Args:
            event: Mouse event
        """
        if self._panning and self._pan_start_pos:
            # Calculate drag delta
            delta = event.position() - self._pan_start_pos

            # Update offset
            self._offset += delta

            # Update start position
            self._pan_start_pos = event.position()

            # Trigger repaint
            self.update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle resize event.

        Args:
            event: Resize event
        """
        super().resizeEvent(event)

        # Reset offset on resize
        self._offset = QPointF(0, 0)

        # Trigger repaint
        self.update()

    def load_image(self, file_path: str) -> bool:
        """
        Load an image from a file path.

        Args:
            file_path: Path to the image file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.set_error(f"File not found: {file_path}")
                return False

            # Load image
            image = QImage(file_path)

            if image.isNull():
                self.set_error(f"Invalid image format: {file_path}")
                return False

            # Set the image
            self._image = image
            self._pixmap = QPixmap.fromImage(image)

            # Reset zoom and offset
            self._zoom_factor = 1.0
            self._offset = QPointF(0, 0)

            # Clear error and status
            self._error_text = None
            self._status_text = None

            # Trigger repaint
            self.update()

            return True

        except Exception as e:
            if self._logger:
                self._logger.error(f"Error loading image: {str(e)}")

            self.set_error(f"Error loading image: {str(e)}")
            return False

    def load_image_data(self, data: bytes) -> bool:
        """
        Load an image from raw bytes.

        Args:
            data: Image data as bytes

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            # Load image from bytes
            image = QImage()
            if not image.loadFromData(data):
                self.set_error("Invalid image data")
                return False

            # Set the image
            self._image = image
            self._pixmap = QPixmap.fromImage(image)

            # Reset zoom and offset
            self._zoom_factor = 1.0
            self._offset = QPointF(0, 0)

            # Clear error and status
            self._error_text = None
            self._status_text = None

            # Trigger repaint
            self.update()

            return True

        except Exception as e:
            if self._logger:
                self._logger.error(f"Error loading image data: {str(e)}")

            self.set_error(f"Error loading image data: {str(e)}")
            return False

    def set_loading(self, loading: bool) -> None:
        """
        Set the loading state.

        Args:
            loading: Whether the widget is in loading state
        """
        if self._loading == loading:
            return

        self._loading = loading

        if loading:
            # Start loading animation
            self._loading_timer.start()
        else:
            # Stop loading animation
            self._loading_timer.stop()

        # Trigger repaint
        self.update()

    def set_error(self, error_text: str) -> None:
        """
        Set an error message.

        Args:
            error_text: Error message to display
        """
        self._error_text = error_text
        self._status_text = None
        self._image = None
        self._pixmap = None

        # Trigger repaint
        self.update()

    def set_status(self, status_text: str) -> None:
        """
        Set a status message.

        Args:
            status_text: Status message to display
        """
        self._status_text = status_text
        self._error_text = None

        # Trigger repaint
        self.update()

    def clear(self) -> None:
        """Clear the image and reset the widget."""
        self._image = None
        self._pixmap = None
        self._zoom_factor = 1.0
        self._offset = QPointF(0, 0)
        self._error_text = None
        self._status_text = None
        self._loading = False

        # Trigger repaint
        self.update()

    def get_image(self) -> Optional[QImage]:
        """
        Get the current image.

        Returns:
            The current image, or None if no image is loaded
        """
        return self._image

    def set_zoom(self, zoom_factor: float) -> None:
        """
        Set the zoom factor.

        Args:
            zoom_factor: New zoom factor
        """
        if not self._pixmap:
            return

        # Apply zoom limits
        self._zoom_factor = max(self._min_zoom, min(self._max_zoom, zoom_factor))

        # Emit signal
        self.zoomChanged.emit(self._zoom_factor)

        # Trigger repaint
        self.update()

    def reset_view(self) -> None:
        """Reset zoom and panning to default values."""
        self._zoom_factor = 1.0
        self._offset = QPointF(0, 0)

        # Emit signal
        self.zoomChanged.emit(self._zoom_factor)

        # Trigger repaint
        self.update()

    def sizeHint(self) -> QSize:
        """
        Get the recommended size for the widget.

        Returns:
            Recommended size
        """
        return QSize(400, 300)