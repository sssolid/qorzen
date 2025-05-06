from __future__ import annotations

"""
API routes for the InitialDB plugin.

This module provides API endpoints for accessing vehicle data, executing queries,
and performing exports.
"""

from typing import Any, Dict, List, Optional

# We'll assume FastAPI-like imports will be available
# with type hints for proper type checking
from typing import Annotated

from pydantic import BaseModel, Field

from ..query.builder import FilterParams
from ..services.export_service import ExportError


# API Request/Response Models
class FilterParamsModel(BaseModel):
    """API model for filter parameters."""

    year_ids: List[int] = Field(default_factory=list, description="List of year IDs to filter by")
    year_range_start: Optional[int] = Field(None, description="Start year for range filter")
    year_range_end: Optional[int] = Field(None, description="End year for range filter")
    make_ids: List[int] = Field(default_factory=list, description="List of make IDs to filter by")
    model_ids: List[int] = Field(default_factory=list, description="List of model IDs to filter by")
    sub_model_ids: List[int] = Field(default_factory=list, description="List of sub-model IDs to filter by")
    region_ids: List[int] = Field(default_factory=list, description="List of region IDs to filter by")
    engine_block_ids: List[int] = Field(default_factory=list, description="List of engine block IDs to filter by")
    engine_liters: List[str] = Field(default_factory=list, description="List of engine liters to filter by")
    engine_cylinders: List[str] = Field(default_factory=list, description="List of engine cylinders to filter by")
    fuel_type_ids: List[int] = Field(default_factory=list, description="List of fuel type IDs to filter by")
    aspiration_ids: List[int] = Field(default_factory=list, description="List of aspiration IDs to filter by")
    body_type_ids: List[int] = Field(default_factory=list, description="List of body type IDs to filter by")
    transmission_type_ids: List[int] = Field(default_factory=list,
                                             description="List of transmission type IDs to filter by")

    class Config:
        json_schema_extra = {
            "example": {
                "year_ids": [2020, 2021],
                "make_ids": [1, 2],
                "model_ids": [100, 101],
                "engine_liters": ["2.0", "3.5"]
            }
        }


class VehicleQueryRequest(BaseModel):
    """API request model for vehicle queries."""

    filters: FilterParamsModel = Field(..., description="Filter criteria")
    limit: Optional[int] = Field(1000, description="Maximum number of results to return")


class CustomQueryRequest(BaseModel):
    """API request model for custom queries."""

    query: str = Field(..., description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class ExportRequest(BaseModel):
    """API request model for exports."""

    filters: FilterParamsModel = Field(..., description="Filter criteria")
    format: str = Field(..., description="Export format (csv or excel)")
    template_name: Optional[str] = Field(None, description="Template name")
    filename: Optional[str] = Field(None, description="Custom filename")


class TemplateCreateRequest(BaseModel):
    """API request model for template creation."""

    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    mappings: Dict[str, Dict[str, str]] = Field(..., description="Field mappings")


def register_api_routes(api_manager: Any,
                        vehicle_service: Any,
                        export_service: Any,
                        logger: Any) -> None:
    """
    Register API routes for the InitialDB plugin.

    Args:
        api_manager: API manager for registering endpoints
        vehicle_service: Vehicle service for data access
        export_service: Export service for exports
        logger: Logger for logging
    """
    # Import current_user from the API manager
    current_user = api_manager._get_current_user
    plugin_prefix = "/api/v1/initialdb"

    logger.info("Registering API routes")

    # GET /vehicles - Get vehicles with filters
    async def get_vehicles(request: VehicleQueryRequest, current_user: Any = Annotated[Any, current_user]) -> Dict[
        str, Any]:
        """
        Get vehicles based on filter criteria.

        Args:
            request: Query request with filters and limit
            current_user: Current authenticated user

        Returns:
            Dictionary with vehicles and count
        """
        logger.debug(f"API request: get_vehicles, filters: {request.filters}, user: {current_user['username']}")

        try:
            # Convert filter model to FilterParams
            filter_params = FilterParams(
                **{k: v for k, v in request.filters.model_dump().items() if k != "model_config"}
            )

            # Get vehicles
            vehicles = await vehicle_service.get_vehicles_async(
                filters=filter_params,
                limit=request.limit
            )

            return {
                "items": vehicles,
                "count": len(vehicles),
                "limit": request.limit
            }
        except Exception as e:
            logger.error(f"API error in get_vehicles: {e}")
            # Raise HTTPException - using type 'Any' since we don't know the exact type
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/vehicles",
        method="post",
        endpoint=get_vehicles,
        tags=["initialdb"],
        summary="Get vehicles",
        description="Get vehicles based on filter criteria"
    )

    # POST /filter-values - Get filter values
    async def get_filter_values(table_name: str,
                                id_column: str,
                                value_column: str,
                                filters: Optional[FilterParamsModel] = None,
                                current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Get distinct values for a column, optionally filtered.

        Args:
            table_name: Name of the table
            id_column: Name of the ID column
            value_column: Name of the value column to display
            filters: Optional filter parameters to apply
            current_user: Current authenticated user

        Returns:
            Dictionary with filter values
        """
        logger.debug(
            f"API request: get_filter_values, table: {table_name}, column: {value_column}, user: {current_user['username']}")

        try:
            # Convert filter model to FilterParams if provided
            filter_params = None
            if filters:
                filter_params = FilterParams(
                    **{k: v for k, v in filters.model_dump().items() if k != "model_config"}
                )

            # Get filter values
            values = await vehicle_service.get_filter_values_async(
                table_name=table_name,
                id_column=id_column,
                value_column=value_column,
                filters=filter_params
            )

            # Convert tuples to dictionaries for JSON response
            result = [{"id": id_val, "value": str(value)} for id_val, value in values]

            return {
                "items": result,
                "count": len(result)
            }
        except Exception as e:
            logger.error(f"API error in get_filter_values: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/filter-values/{{table_name}}/{{id_column}}/{{value_column}}",
        method="post",
        endpoint=get_filter_values,
        tags=["initialdb"],
        summary="Get filter values",
        description="Get distinct values for a column, optionally filtered"
    )

    # GET /filter-fields - Get available filter fields
    async def get_filter_fields(current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Get available filter fields.

        Args:
            current_user: Current authenticated user

        Returns:
            Dictionary with filter fields
        """
        logger.debug(f"API request: get_filter_fields, user: {current_user['username']}")

        try:
            # Get filter fields
            fields = vehicle_service.get_available_filter_fields()

            return {
                "items": fields,
                "count": len(fields)
            }
        except Exception as e:
            logger.error(f"API error in get_filter_fields: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/filter-fields",
        method="get",
        endpoint=get_filter_fields,
        tags=["initialdb"],
        summary="Get filter fields",
        description="Get available filter fields"
    )

    # GET /display-fields - Get available display fields
    async def get_display_fields(current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Get available display fields.

        Args:
            current_user: Current authenticated user

        Returns:
            Dictionary with display fields
        """
        logger.debug(f"API request: get_display_fields, user: {current_user['username']}")

        try:
            # Get display fields
            fields = vehicle_service.get_available_display_fields()

            return {
                "items": fields,
                "count": len(fields)
            }
        except Exception as e:
            logger.error(f"API error in get_display_fields: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/display-fields",
        method="get",
        endpoint=get_display_fields,
        tags=["initialdb"],
        summary="Get display fields",
        description="Get available display fields"
    )

    # POST /custom-query - Execute a custom query
    async def execute_custom_query(request: CustomQueryRequest, current_user: Any = Annotated[Any, current_user]) -> \
    Dict[str, Any]:
        """
        Execute a custom SQL query.

        Args:
            request: Custom query request
            current_user: Current authenticated user

        Returns:
            Dictionary with query results
        """
        logger.debug(f"API request: execute_custom_query, user: {current_user['username']}")

        # Check permissions - only certain roles can execute custom queries
        if "admin" not in current_user.get("roles", []) and "developer" not in current_user.get("roles", []):
            raise api_manager._exception_type(status_code=403, detail="Permission denied")

        try:
            # Execute custom query
            results = await vehicle_service.execute_custom_query_async(
                query_sql=request.query,
                params=request.params
            )

            return {
                "items": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"API error in execute_custom_query: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/custom-query",
        method="post",
        endpoint=execute_custom_query,
        tags=["initialdb"],
        summary="Execute custom query",
        description="Execute a custom SQL query"
    )

    # POST /export - Export data
    async def export_data(request: ExportRequest, current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Export data to file.

        Args:
            request: Export request
            current_user: Current authenticated user

        Returns:
            Dictionary with export path
        """
        logger.debug(
            f"API request: export_data, format: {request.format}, template: {request.template_name}, user: {current_user['username']}")

        try:
            # Convert filter model to FilterParams
            filter_params = FilterParams(
                **{k: v for k, v in request.filters.model_dump().items() if k != "model_config"}
            )

            # Export data
            output_path = export_service.export_query_results(
                filters=filter_params,
                format=request.format,
                template_name=request.template_name,
                filename=request.filename
            )

            return {
                "path": output_path,
                "filename": output_path.split("/")[-1],
                "format": request.format
            }
        except ExportError as e:
            logger.error(f"Export error: {e}")
            raise api_manager._exception_type(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"API error in export_data: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/export",
        method="post",
        endpoint=export_data,
        tags=["initialdb"],
        summary="Export data",
        description="Export data to file"
    )

    # GET /templates - Get available templates
    async def get_templates(current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Get available export templates.

        Args:
            current_user: Current authenticated user

        Returns:
            Dictionary with templates
        """
        logger.debug(f"API request: get_templates, user: {current_user['username']}")

        try:
            # Get templates
            templates = export_service.get_available_templates()

            return {
                "items": templates,
                "count": len(templates)
            }
        except Exception as e:
            logger.error(f"API error in get_templates: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/templates",
        method="get",
        endpoint=get_templates,
        tags=["initialdb"],
        summary="Get templates",
        description="Get available export templates"
    )

    # POST /templates - Create a template
    async def create_template(request: TemplateCreateRequest, current_user: Any = Annotated[Any, current_user]) -> Dict[
        str, Any]:
        """
        Create a new export template.

        Args:
            request: Template creation request
            current_user: Current authenticated user

        Returns:
            Dictionary with success status
        """
        logger.debug(f"API request: create_template, name: {request.name}, user: {current_user['username']}")

        # Check permissions - only certain roles can create templates
        if "admin" not in current_user.get("roles", []) and "developer" not in current_user.get("roles", []):
            raise api_manager._exception_type(status_code=403, detail="Permission denied")

        try:
            # Create template
            export_service.create_template(
                name=request.name,
                description=request.description,
                mappings=request.mappings
            )

            return {
                "success": True,
                "name": request.name
            }
        except ExportError as e:
            logger.error(f"Template creation error: {e}")
            raise api_manager._exception_type(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"API error in create_template: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/templates",
        method="post",
        endpoint=create_template,
        tags=["initialdb"],
        summary="Create template",
        description="Create a new export template"
    )

    # DELETE /templates/{name} - Delete a template
    async def delete_template(name: str, current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Delete an export template.

        Args:
            name: Template name
            current_user: Current authenticated user

        Returns:
            Dictionary with success status
        """
        logger.debug(f"API request: delete_template, name: {name}, user: {current_user['username']}")

        # Check permissions - only certain roles can delete templates
        if "admin" not in current_user.get("roles", []) and "developer" not in current_user.get("roles", []):
            raise api_manager._exception_type(status_code=403, detail="Permission denied")

        try:
            # Delete template
            export_service.delete_template(name=name)

            return {
                "success": True,
                "name": name
            }
        except ExportError as e:
            logger.error(f"Template deletion error: {e}")
            raise api_manager._exception_type(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"API error in delete_template: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/templates/{{name}}",
        method="delete",
        endpoint=delete_template,
        tags=["initialdb"],
        summary="Delete template",
        description="Delete an export template"
    )

    # GET /exports - Get recent exports
    async def get_recent_exports(limit: int = 10, current_user: Any = Annotated[Any, current_user]) -> Dict[str, Any]:
        """
        Get recent exports.

        Args:
            limit: Maximum number of exports to return
            current_user: Current authenticated user

        Returns:
            Dictionary with exports
        """
        logger.debug(f"API request: get_recent_exports, limit: {limit}, user: {current_user['username']}")

        try:
            # Get recent exports
            exports = export_service.get_recent_exports(limit=limit)

            return {
                "items": exports,
                "count": len(exports)
            }
        except Exception as e:
            logger.error(f"API error in get_recent_exports: {e}")
            raise api_manager._exception_type(status_code=500, detail=str(e))

    # Register the endpoint
    api_manager.register_api_endpoint(
        path=f"{plugin_prefix}/exports",
        method="get",
        endpoint=get_recent_exports,
        tags=["initialdb"],
        summary="Get recent exports",
        description="Get recent exports"
    )

    logger.info(f"Registered {11} API routes")