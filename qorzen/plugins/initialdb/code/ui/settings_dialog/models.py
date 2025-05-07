from __future__ import annotations

"""
Settings models for the InitialDB application settings dialog.

This module provides data models for representing settings categories and individual settings.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast

import structlog

logger = structlog.get_logger(__name__)


class SettingType(Enum):
    """Enumeration of supported setting types."""

    STRING = auto()
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    COLOR = auto()
    FONT = auto()
    PATH = auto()
    CHOICE = auto()
    MULTISELECT = auto()
    PASSWORD = auto()


@dataclass
class Setting:
    """Represents a single configurable setting."""

    key: str
    name: str
    description: str
    setting_type: SettingType
    default_value: Any
    current_value: Any = None
    choices: List[tuple[Any, str]] = field(default_factory=list)
    validator: Optional[Callable[[Any], tuple[bool, str]]] = None
    visible: bool = True
    restart_required: bool = False
    advanced: bool = False
    group: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize the current value if not provided."""
        if self.current_value is None:
            self.current_value = self.default_value

    def validate(self, value: Any) -> tuple[bool, str]:
        """
        Validate the provided value against any constraints.

        Args:
            value: The value to validate

        Returns:
            A tuple of (is_valid, error_message)
        """
        if self.validator:
            return self.validator(value)
        return True, ""


@dataclass
class SettingsCategory:
    """Represents a category of settings."""

    id: str
    name: str
    description: str
    icon_name: str
    parent_id: Optional[str] = None
    settings: List[Setting] = field(default_factory=list)
    subcategories: List[SettingsCategory] = field(default_factory=list)
    visible: bool = True

    def add_setting(self, setting: Setting) -> None:
        """
        Add a setting to this category.

        Args:
            setting: The setting to add
        """
        self.settings.append(setting)

    def add_subcategory(self, category: SettingsCategory) -> None:
        """
        Add a subcategory to this category.

        Args:
            category: The subcategory to add
        """
        category.parent_id = self.id
        self.subcategories.append(category)

    def find_subcategory(self, category_id: str) -> Optional[SettingsCategory]:
        """
        Find a subcategory by ID.

        Args:
            category_id: The ID of the subcategory to find

        Returns:
            The found subcategory or None
        """
        if self.id == category_id:
            return self

        for subcategory in self.subcategories:
            found = subcategory.find_subcategory(category_id)
            if found:
                return found

        return None


@dataclass
class SettingsRegistry:
    """Registry for all settings categories and settings."""

    categories: List[SettingsCategory] = field(default_factory=list)
    _settings_map: Dict[str, Setting] = field(default_factory=dict)

    def add_category(self, category: SettingsCategory) -> None:
        """
        Add a top-level category to the registry.

        Args:
            category: The category to add
        """
        self.categories.append(category)
        self._register_settings(category)

    def _register_settings(self, category: SettingsCategory) -> None:
        """
        Recursively register all settings in a category.

        Args:
            category: The category whose settings should be registered
        """
        for setting in category.settings:
            self._settings_map[setting.key] = setting

        for subcategory in category.subcategories:
            self._register_settings(subcategory)

    def get_setting(self, key: str) -> Optional[Setting]:
        """
        Get a setting by key.

        Args:
            key: The setting key

        Returns:
            The setting or None if not found
        """
        return self._settings_map.get(key)

    def find_category(self, category_id: str) -> Optional[SettingsCategory]:
        """
        Find a category by ID.

        Args:
            category_id: The ID of the category to find

        Returns:
            The found category or None
        """
        for category in self.categories:
            found = category.find_subcategory(category_id)
            if found:
                return found

        return None