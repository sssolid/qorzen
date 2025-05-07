from __future__ import annotations

"""
Vehicle service adapter for the InitialDB application.

This module provides an adapter class for the VehicleService to be used
in UI components with simplified async handling and proper thread safety.
"""

import asyncio
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from PySide6.QtCore import QObject, QTimer, Signal

from ..models.schema import FilterDTO
from ..services.vehicle_service import VehicleService, get_vehicle_service
from ..utils.async_manager import AsyncManager, async_slot
from ..utils.dependency_container import resolve
from ..utils.schema_registry import SchemaRegistry

logger = structlog.get_logger(__name__)


class DatabaseOperation:
    """Represents a database operation with tracking information."""

    def __init__(self, operation_id: str, operation_type: str) -> None:
        """
        Initialize a database operation.

        Args:
            operation_id: The unique identifier for the operation
            operation_type: The type of operation
        """
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.result: Any = None


class AdapterSignals(QObject):
    """Qt signals for the vehicle service adapter."""

    operationCompleted = Signal(object)
    operationFailed = Signal(object, Exception)
    filterValuesLoaded = Signal(str, list)


class VehicleServiceAdapter:
    """
    Adapter for the VehicleService to be used in UI components.

    This class simplifies the interface to the VehicleService and provides
    Qt signals for operation completion and failure.
    """

    def __init__(self) -> None:
        """Initialize the vehicle service adapter."""
        self.signals = AdapterSignals()
        self._vehicle_service: Optional[VehicleService] = None
        self._registry: Optional[SchemaRegistry] = None
        self._async_manager = AsyncManager.instance()
        self._operations: Dict[str, DatabaseOperation] = {}

        # Initialize dependencies
        self._init_dependencies()

        logger.debug("VehicleServiceAdapter initialized")

    def _init_dependencies(self) -> None:
        """Initialize dependencies from the dependency container."""
        try:
            self._vehicle_service = resolve(VehicleService)
            self._registry = resolve(SchemaRegistry)

            # Connect signals
            self._async_manager.connect_operation_signals(
                self._on_operation_completed,
                self._on_operation_failed,
            )

        except Exception as e:
            logger.error(f"Error initializing dependencies: {e}", exc_info=True)

            # We'll try to resolve them later when needed
            pass

    def _ensure_dependencies(self) -> None:
        """Ensure that dependencies are initialized."""
        if self._vehicle_service is None:
            try:
                self._vehicle_service = resolve(VehicleService)
            except Exception as e:
                logger.error(f"Error resolving VehicleService: {e}", exc_info=True)
                raise RuntimeError("VehicleService not available") from e

        if self._registry is None:
            try:
                self._registry = resolve(SchemaRegistry)
            except Exception as e:
                logger.error(f"Error resolving SchemaRegistry: {e}", exc_info=True)
                raise RuntimeError("SchemaRegistry not available") from e

    def _on_operation_completed(self, operation_id: str, result: Any) -> None:
        """
        Handle operation completion.

        Args:
            operation_id: The ID of the completed operation
            result: The result of the operation
        """
        if operation_id in self._operations:
            operation = self._operations[operation_id]
            operation.result = result

            # Emit the appropriate signal
            self.signals.operationCompleted.emit(operation)

            # Special handling for filter values
            if operation.operation_type == "get_filter_values" and isinstance(result, list):
                self.signals.filterValuesLoaded.emit(operation_id, result)

            # Clean up
            del self._operations[operation_id]

    def _on_operation_failed(self, operation_id: str, error: Exception) -> None:
        """
        Handle operation failure.

        Args:
            operation_id: The ID of the failed operation
            error: The exception that caused the failure
        """
        if operation_id in self._operations:
            operation = self._operations[operation_id]

            # Emit the failure signal
            self.signals.operationFailed.emit(operation, error)

            # Clean up
            del self._operations[operation_id]

    def load_filter_values(
            self, filter_name: str, filters: Optional[FilterDTO] = None
    ) -> str:
        """
        Load values for a filter.

        Args:
            filter_name: The name of the filter
            filters: Optional filters to apply

        Returns:
            The operation ID that can be used to track the operation
        """
        self._ensure_dependencies()

        # Create an operation
        operation_id = str(uuid.uuid4())
        operation = DatabaseOperation(operation_id, "get_filter_values")
        self._operations[operation_id] = operation

        # Run the operation
        async def _load_filter_values() -> List[Tuple[Any, str]]:
            if self._vehicle_service is None:
                return []

            return await self._vehicle_service.get_filter_values(filter_name, filters)

        async def wrapper():
            try:
                result = await _load_filter_values()
                self._on_operation_completed(operation_id, result)
            except Exception as e:
                self._on_operation_failed(operation_id, e)

        asyncio.create_task(wrapper())

        return operation_id

    def load_filter_values_from_table(
            self, table: str, column: str, filters: Optional[FilterDTO] = None
    ) -> str:
        """
        Load filter values using the full table and column name.

        Args:
            table: Table name
            column: Column name
            filters: Filter criteria

        Returns:
            Operation ID
        """
        self._ensure_dependencies()

        operation_id = str(uuid.uuid4())
        operation = DatabaseOperation(operation_id, "get_filter_values")
        self._operations[operation_id] = operation

        async def _load():
            if self._vehicle_service is None:
                return []
            return await self._vehicle_service.get_filter_values(column, filters)

        async def wrapper():
            try:
                result = await _load()
                self._on_operation_completed(operation_id, result)
            except Exception as e:
                self._on_operation_failed(operation_id, e)

        asyncio.create_task(wrapper())
        return operation_id

    def get_filter_values_sync(
            self, table_name: str, id_column: str, value_column: str
    ) -> List[Tuple[Any, str]]:
        """
        Get filter values synchronously.

        This method is for testing only - in real use, you should use
        load_filter_values instead.

        Args:
            table_name: The name of the table
            id_column: The ID column
            value_column: The value column

        Returns:
            A list of (ID, value) tuples
        """
        self._ensure_dependencies()

        # Construct a simple test result
        return [(1, "Option 1"), (2, "Option 2"), (3, "Option 3")]

    @async_slot
    async def execute_query(
            self, filters: FilterDTO, display_fields: Optional[List[Tuple[str, str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query.

        Args:
            filters: The filters to apply
            display_fields: The fields to display in the results

        Returns:
            A list of result dictionaries
        """
        self._ensure_dependencies()

        if self._vehicle_service is None:
            return []

        return await self._vehicle_service.get_vehicles(filters, display_fields)

    def get_available_filters(self) -> List[Tuple[str, str, str]]:
        """
        Get all available filters.

        Returns:
            A list of (table_name, column_name, display_name) tuples
        """
        self._ensure_dependencies()

        if self._registry is None:
            return []

        return self._registry.get_available_filters()

    def get_available_display_fields(self) -> List[Tuple[str, str, str]]:
        """
        Get all available display fields.

        Returns:
            A list of (table_name, column_name, display_name) tuples
        """
        self._ensure_dependencies()

        if self._registry is None:
            return []

        return self._registry.get_available_display_fields()

    def cleanup(self) -> None:
        """Clean up the adapter resources."""
        # Disconnect signals
        try:
            self._async_manager.disconnect_operation_signals(
                self._on_operation_completed,
                self._on_operation_failed,
            )
        except Exception:
            pass

        # Clear operations
        self._operations.clear()

        logger.debug("VehicleServiceAdapter cleaned up")