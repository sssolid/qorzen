from __future__ import annotations

"""
API routes package for the InitialDB plugin.

This package provides API endpoints for the InitialDB plugin, enabling
access to vehicle data through HTTP requests.
"""

from .api import register_api_routes

__all__ = ['register_api_routes']