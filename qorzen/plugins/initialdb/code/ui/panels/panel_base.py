from __future__ import annotations

"""
Base panel for the InitialDB application.

This module provides the base class for dockable panels in the application,
with support for content switching, state preservation, and consistent styling.
"""

from typing import Dict, List, Optional, Type, cast

import structlog
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDockWidget, QFrame, QHBoxLayout, QPushButton, QScrollArea,
    QSizePolicy, QToolBar, QToolButton, QVBoxLayout, QWidget
)
from initialdb.utils.icon_utils import load_icon

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
        """
        Initialize the side button.

        Args:
            text: The button text
            icon_name: Optional icon name for themed icons
            icon: Optional explicit icon
            parent: The parent widget
        """
        super().__init__(parent)

        self.setText(text)

        self.setCheckable(True)

        self.setMinimumSize(32, 32)
        if text:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        else:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Set icon if provided
        if icon:
            self.setIcon(icon)
        elif icon_name:
            # Try theme icon
            self.setIcon(load_icon(icon_name, color="#FFFFFF"))

            themed_icon = QIcon.fromTheme(icon_name)
            if not themed_icon.isNull():
                self.setIcon(themed_icon)

        # Style
        # self.setStyleSheet("""
        #     QToolButton {
        #         border: none;
        #         padding: 8px;
        #         text-align: left;
        #         border-radius: 4px;
        #         margin: 2px;
        #     }
        #     QToolButton:hover {
        #         background-color: rgba(0, 0, 0, 0.1);
        #     }
        #     QToolButton:checked {
        #         background-color: rgba(0, 0, 0, 0.15);
        #     }
        # """)


class PanelContent(QWidget):
    """Base class for panel content widgets."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the panel content.

        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        # Create the main layout
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface.

        This method should be overridden by subclasses to add widgets to the layout.
        Subclasses should NOT create a new layout but use self.layout() to get the
        existing layout.
        """
        pass

    def layout(self) -> QVBoxLayout:
        """
        Get the main layout.

        Returns:
            The main layout
        """
        return self._main_layout

    def activate(self) -> None:
        """Called when this content is activated."""
        pass

    def deactivate(self) -> None:
        """Called when this content is deactivated."""
        pass

    def save_state(self) -> Dict:
        """
        Save the content state.

        Returns:
            Dictionary with the state
        """
        return {}

    def restore_state(self, state: Dict) -> None:
        """
        Restore the content state.

        Args:
            state: Dictionary with the state
        """
        pass


class PanelBase(QDockWidget):
    """Base class for dockable panels with side buttons."""

    title_changed = pyqtSignal(str)

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the panel base.

        Args:
            title: The panel title
            parent: The parent widget
        """
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
        """Set up the user interface."""
        # Main widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)

        # Main layout
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Side toolbar for buttons
        self.side_toolbar = QToolBar()
        self.side_toolbar.setOrientation(Qt.Orientation.Vertical)
        self.side_toolbar.setMovable(False)
        self.side_toolbar.setFloatable(False)
        self.side_toolbar.setIconSize(QSize(20, 20))
        # self.side_toolbar.setStyleSheet("""
        #     QToolBar {
        #         border: none;
        #         background-color: #f5f5f5;
        #         border-right: 1px solid #ddd;
        #     }
        # """)

        self.main_layout.addWidget(self.side_toolbar)

        # Scroll area for content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.content_container)
        self.main_layout.addWidget(self.scroll_area)

        # Side buttons group (for exclusive selection)
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
        """
        Add a content widget to the panel.

        Args:
            content_id: Unique identifier for this content
            content: The content widget
            button_text: Text for the side button
            icon_name: Optional icon name for themed icons
            icon: Optional explicit icon
            activate: Whether to activate this content immediately
        """
        if content_id in self._contents:
            logger.warning(f"Content ID '{content_id}' already exists, replacing")

        # Store the content
        self._contents[content_id] = content

        # Add to layout but hide initially
        content.setVisible(False)
        self.content_layout.addWidget(content)

        # Create side button
        button = SideButton(button_text, icon_name, icon, self)
        button.clicked.connect(lambda checked, cid=content_id: self.activate_content(cid))
        if tooltip:
            button.setToolTip(tooltip)

        self.side_toolbar.addWidget(button)
        self.side_buttons[content_id] = button

        # Add a spacer at the end to push buttons to the top
        if len(self.side_buttons) == 1:
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            self.side_toolbar.addWidget(spacer)

        # Activate if requested or if this is the first content
        if activate or len(self._contents) == 1:
            self.activate_content(content_id)

    def activate_content(self, content_id: str) -> None:
        """
        Activate a specific content panel.

        Args:
            content_id: The ID of the content to activate
        """
        if content_id not in self._contents:
            logger.error(f"Content ID '{content_id}' does not exist")
            return

        # Deactivate current content
        if self._active_content_id and self._active_content_id in self._contents:
            self._contents[self._active_content_id].setVisible(False)
            self._contents[self._active_content_id].deactivate()

            # Uncheck button
            if self._active_content_id in self.side_buttons:
                self.side_buttons[self._active_content_id].setChecked(False)

        # Activate new content
        self._contents[content_id].setVisible(True)
        self._contents[content_id].activate()
        self._active_content_id = content_id

        # Check button
        if content_id in self.side_buttons:
            self.side_buttons[content_id].setChecked(True)

    def get_active_content(self) -> Optional[PanelContent]:
        """
        Get the currently active content widget.

        Returns:
            The active content widget or None
        """
        if self._active_content_id and self._active_content_id in self._contents:
            return self._contents[self._active_content_id]
        return None

    def get_content(self, content_id: str) -> Optional[PanelContent]:
        """
        Get a content widget by ID.

        Args:
            content_id: The ID of the content to get

        Returns:
            The content widget or None
        """
        return self._contents.get(content_id)

    def save_state(self) -> Dict:
        """
        Save the panel state.

        Returns:
            Dictionary with the state
        """
        content_states = {}
        for content_id, content in self._contents.items():
            content_states[content_id] = content.save_state()

        return {
            "active_content_id": self._active_content_id,
            "content_states": content_states
        }

    def restore_state(self, state: Dict) -> None:
        """
        Restore the panel state.

        Args:
            state: Dictionary with the state
        """
        # Restore content states
        content_states = state.get("content_states", {})
        for content_id, content_state in content_states.items():
            if content_id in self._contents:
                self._contents[content_id].restore_state(content_state)

        # Activate the previously active content
        active_content_id = state.get("active_content_id")
        if active_content_id and active_content_id in self._contents:
            self.activate_content(active_content_id)