from __future__ import annotations

"""
Panel components for the InitialDB application UI.

This module provides the dockable panel components used throughout the application
for a customizable IDE-like interface.
"""

from .left_panel import LeftPanel
from .right_panel import RightPanel
from .bottom_panel import BottomPanel
from .panel_base import PanelBase, PanelContent

__all__ = [
    "LeftPanel",
    "RightPanel",
    "BottomPanel",
    "PanelBase",
    "PanelContent"
]