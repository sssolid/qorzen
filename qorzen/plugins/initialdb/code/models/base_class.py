# app/db/base_class.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    ClassVar,
)

from sqlalchemy import DateTime, Boolean, inspect, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql.expression import Select
import logging

logger = logging.getLogger("models.base_class")

T = TypeVar("T", bound="Base")


class Base(DeclarativeBase):
    """Enhanced base class for all database models.

    This class provides common functionality for all models, including:
    - Automatic table name generation
    - Audit fields (created_at, updated_at, created_by_id, updated_by_id)
    - Soft deletion support
    - JSON serialization via the to_dict() method
    - Helper methods for common query operations
    """

    # Common columns for all models
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Class variables for configuration
    __exclude_from_dict__: ClassVar[List[str]] = ["is_deleted"]
    __include_relationships__: ClassVar[bool] = False

    @declared_attr
    def __tablename__(self) -> str:
        """Generate table name automatically from class name.

        Returns:
            str: Table name as lowercase class name
        """
        return self.__name__.lower()

    def to_dict(
        self,
        exclude: Optional[List[str]] = None,
        include_relationships: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        This method provides a consistent way to serialize models for API responses.
        It respects the exclude_from_dict and include_relationships configurations.

        Args:
            exclude: Additional fields to exclude from the result
            include_relationships: Override __include_relationships__ setting

        Returns:
            Dict[str, Any]: Dictionary representation of model
        """
        exclude_fields = set(self.__exclude_from_dict__)
        if exclude:
            exclude_fields.update(exclude)

        include_rels = (
            self.__include_relationships__
            if include_relationships is None
            else include_relationships
        )

        result = {}
        for key, value in inspect(self).dict.items():
            # Skip excluded fields and deleted flag
            if key in exclude_fields or (key == "is_deleted" and value):
                continue

            # Handle relationships
            if key.startswith("_"):
                # Skip private attributes and SQLAlchemy internals
                continue

            # Include relationships if configured
            mapper = inspect(self.__class__)
            if key in mapper.relationships and not include_rels:
                continue

            # Convert UUID objects to strings
            if isinstance(value, uuid.UUID):
                value = str(value)

            # Convert datetime objects to ISO format
            if isinstance(value, datetime):
                value = value.isoformat()

            result[key] = value

        return result

    @classmethod
    def get_columns(cls) -> List[str]:
        """Get a list of column names for this model.

        Returns:
            List[str]: Column names
        """
        return [c.name for c in inspect(cls).columns]

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a new instance from a dictionary.

        Args:
            data: Dictionary containing model data

        Returns:
            T: New model instance
        """
        valid_fields = cls.get_columns()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    @classmethod
    def filter_by_id(cls: Type[T], id_value: uuid.UUID) -> Select:
        """Create a query to filter by id.

        Args:
            id_value: UUID primary key to filter by

        Returns:
            Select: SQLAlchemy select statement filtered by id
        """
        return select(cls).where(cls.id == id_value, cls.is_deleted == False)

    @classmethod
    def active_only(cls) -> Select:
        """Create a query for non-deleted records only.

        Returns:
            Select: SQLAlchemy select statement filtered to non-deleted records
        """
        return select(cls).where(cls.is_deleted == False)

    def soft_delete(self, user_id: Optional[uuid.UUID] = None) -> None:
        """Mark the record as deleted without removing from database.

        Args:
            user_id: ID of the user performing the deletion
        """
        self.is_deleted = True
        if user_id:
            self.updated_by_id = user_id

    def restore(self, user_id: Optional[uuid.UUID] = None) -> None:
        """Restore a soft-deleted record.

        Args:
            user_id: ID of the user restoring the record
        """
        self.is_deleted = False
        if user_id:
            self.updated_by_id = user_id

    def update_from_dict(
        self,
        data: Dict[str, Any],
        user_id: Optional[uuid.UUID] = None,
        exclude: Optional[List[str]] = None,
    ) -> None:
        """Update model attributes from dictionary.

        Args:
            data: Dictionary containing values to update
            user_id: ID of the user performing the update
            exclude: Fields to exclude from update
        """
        if exclude is None:
            exclude = []

        exclude = exclude + ["id", "created_at", "created_by_id", "is_deleted"]

        columns = self.get_columns()

        for key, value in data.items():
            if key in columns and key not in exclude:
                setattr(self, key, value)

        if user_id:
            self.updated_by_id = user_id

    @classmethod
    def get_relationships(cls) -> Dict[str, Any]:
        """Get relationships defined on this model.

        Returns:
            Dict[str, Any]: Dictionary of relationship names and their properties
        """
        return {r.key: r for r in inspect(cls).relationships}
