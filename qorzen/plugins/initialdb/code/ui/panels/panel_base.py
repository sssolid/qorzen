# panel_base.py

from __future__ import annotations

"""
Base panel for the InitialDB application.

This module provides the base class for dockable panels in the application,
with support for content switching, state preservation, and consistent styling.
"""

from typing import Dict, Optional

import structlog
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDockWidget, QFrame, QHBoxLayout, QPushButton, QScrollArea,
    QSizePolicy, QToolBar, QToolButton, QVBoxLayout, QWidget
)
from ...utils.icon_utils import load_icon

logger = structlog.get_logger(__name__)


class SideButton(QToolButton):
    """Button for the panel sidebar."""

    def __init__(
        self,
        text: str,
        icon_name: Optional[str] = None,
        icon: Optional[QIcon] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setMinimumSize(32, 32)
        if text:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        else:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if icon:
            self.setIcon(icon)
        elif icon_name:
            self.setIcon(load_icon(icon_name, color="#FFFFFF"))
            themed_icon = QIcon.fromTheme(icon_name)
            if not themed_icon.isNull():
                self.setIcon(themed_icon)


class PanelContent(QWidget):
    """Base class for panel content widgets."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._setup_ui()

    def _setup_ui(self) -> None:
        pass

    def layout(self) -> QVBoxLayout:
        return self._main_layout

    def activate(self) -> None:
        pass

    def deactivate(self) -> None:
        pass

    def save_state(self) -> Dict:
        return {}

    def restore_state(self, state: Dict) -> None:
        pass


class PanelBase(QDockWidget):
    """Base class for dockable panels with side buttons."""

    title_changed = Signal(str)

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(title, parent)
        self.setObjectName(title.lower().replace(" ", "_") + "_panel")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self._contents: Dict[str, PanelContent] = {}
        self._active_content_id: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.side_toolbar = QToolBar()
        self.side_toolbar.setOrientation(Qt.Orientation.Vertical)
        self.side_toolbar.setMovable(False)
        self.side_toolbar.setFloatable(False)
        self.side_toolbar.setIconSize(QSize(20, 20))
        self.main_layout.addWidget(self.side_toolbar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.content_container)
        self.main_layout.addWidget(self.scroll_area)

        self.side_buttons: Dict[str, SideButton] = {}

    def add_content(
        self,
        content_id: str,
        content: PanelContent,
        button_text: Optional[str] = None,
        icon_name: Optional[str] = None,
        icon: Optional[QIcon] = None,
        activate: bool = False,
        tooltip: Optional[str] = None,
    ) -> None:
        if content_id in self._contents:
            logger.warning(f"Content ID '{content_id}' already exists, replacing")
        self._contents[content_id] = content
        content.setVisible(False)
        self.content_layout.addWidget(content)

        button = SideButton(button_text or "", icon_name, icon, self)
        button.clicked.connect(lambda checked, cid=content_id: self.activate_content(cid))
        if tooltip:
            button.setToolTip(tooltip)
        self.side_toolbar.addWidget(button)
        self.side_buttons[content_id] = button

        if len(self.side_buttons) == 1:
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            self.side_toolbar.addWidget(spacer)

        if activate or len(self._contents) == 1:
            self.activate_content(content_id)

    def activate_content(self, content_id: str) -> None:
        if content_id not in self._contents:
            logger.error(f"Content ID '{content_id}' does not exist")
            return
        if self._active_content_id:
            prev = self._contents[self._active_content_id]
            prev.setVisible(False)
            prev.deactivate()
            self.side_buttons[self._active_content_id].setChecked(False)

        new = self._contents[content_id]
        new.setVisible(True)
        new.activate()
        self._active_content_id = content_id
        self.side_buttons[content_id].setChecked(True)

    def get_active_content(self) -> Optional[PanelContent]:
        return self._contents.get(self._active_content_id)

    def get_content(self, content_id: str) -> Optional[PanelContent]:
        return self._contents.get(content_id)

    def save_state(self) -> Dict:
        content_states = {cid: c.save_state() for cid, c in self._contents.items()}
        return {"active_content_id": self._active_content_id, "content_states": content_states}

    def restore_state(self, state: Dict) -> None:
        for cid, cstate in state.get("content_states", {}).items():
            if cid in self._contents:
                self._contents[cid].restore_state(cstate)
        active = state.get("active_content_id")
        if active:
            self.activate_content(active)
