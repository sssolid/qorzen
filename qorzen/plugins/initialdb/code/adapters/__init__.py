from __future__ import annotations

"""
UI adapters for the InitialDB application.

This package provides adapters that help transition from the old repository
pattern to the new vehicle_service and registry singletons.
"""

from .vehicle_service_adapter import VehicleServiceAdapter

__all__ = ['VehicleServiceAdapter']