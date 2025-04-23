from __future__ import annotations
"""
AS400 Connector Plugin for Qorzen.

This plugin provides a user interface for connecting to and querying AS400/iSeries
databases within the Qorzen platform.
"""

from qorzen.plugins.as400_connector_plugin.plugin import AS400ConnectorPlugin

# Export the plugin class for the plugin manager to discover
__all__ = ["AS400ConnectorPlugin"]