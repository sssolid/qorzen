from __future__ import annotations

"""
API routes for the InitialDB plugin.

This module registers API endpoints for vehicle database access.
"""

import logging
from typing import Any, Dict, List, Optional, cast

from pydantic import BaseModel, Field


class VehicleQuery(BaseModel):
    """Model for vehicle query parameters."""

    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    limit: Optional[int] = Field(None, description="Maximum number of records to return")


class VehicleExport(BaseModel):
    """Model for vehicle export parameters."""

    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    format: str = Field("csv", description="Export format (csv, excel)")
    template_name: Optional[str] = Field(None, description="Template to apply")
    filename: Optional[str] = Field(None, description="Export filename")


def register_api_routes(api_manager: Any, vehicle_service: Any, export_service: Any, logger: logging.Logger) -> None:
    """Register API routes for the InitialDB plugin.

    Args:
        api_manager: API manager from Qorzen
        vehicle_service: Vehicle service instance
        export_service: Export service instance
        logger: Logger for API routes
    """
    try:
        # Register vehicle query endpoint
        @api_manager.register_api_endpoint(
            path="/api/v1/vehicle/query",
            method="post",
            tags=["Vehicle Database"],
            response_model=List[Dict[str, Any]]
        )
        async def query_vehicles(query: VehicleQuery) -> List[Dict[str, Any]]:
            """Query vehicles based on filters."""
            logger.debug(f"API: Query vehicles with filters: {query.filters}")

            from ..models.schema import FilterDTO
            filters = FilterDTO(**query.filters)

            return vehicle_service.get_vehicles(filters, limit=query.limit)

        # Register template list endpoint
        @api_manager.register_api_endpoint(
            path="/api/v1/vehicle/templates",
            method="get",
            tags=["Vehicle Database"],
            response_model=List[Dict[str, Any]]
        )
        async def get_templates() -> List[Dict[str, Any]]:
            """Get available export templates."""
            logger.debug("API: Get export templates")
            return export_service.get_available_templates()

        # Register export endpoint
        @api_manager.register_api_endpoint(
            path="/api/v1/vehicle/export",
            method="post",
            tags=["Vehicle Database"],
            response_model=Dict[str, Any]
        )
        async def export_vehicles(export_params: VehicleExport) -> Dict[str, Any]:
            """Export vehicles to file."""
            logger.debug(f"API: Export vehicles in {export_params.format} format")

            from ..models.schema import FilterDTO
            filters = FilterDTO(**export_params.filters)

            try:
                export_path = export_service.export_query_results(
                    filters=filters,
                    format=export_params.format,
                    template_name=export_params.template_name,
                    filename=export_params.filename
                )

                return {
                    "success": True,
                    "path": export_path,
                    "format": export_params.format,
                    "record_count": len(vehicle_service.get_vehicles(filters))
                }
            except Exception as e:
                logger.error(f"Export error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }

        logger.info("API routes registered successfully")
    except Exception as e:
        logger.error(f"Failed to register API routes: {str(e)}")