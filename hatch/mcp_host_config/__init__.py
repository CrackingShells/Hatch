"""MCP (Model Context Protocol) support for Hatch.

This module provides MCP host configuration management functionality,
including backup and restore capabilities for MCP server configurations,
decorator-based strategy registration, and consolidated Pydantic models.
"""

from .backup import MCPHostConfigBackupManager
from .models import (
    MCPHostType, MCPServerConfig, HostConfiguration, EnvironmentData,
    PackageHostConfiguration, EnvironmentPackageEntry, ConfigurationResult, SyncResult
)
from .host_management import (
    MCPHostRegistry, MCPHostStrategy, MCPHostConfigurationManager, register_host_strategy
)

# Import strategies to trigger decorator registration
from . import strategies

__all__ = [
    'MCPHostConfigBackupManager',
    'MCPHostType', 'MCPServerConfig', 'HostConfiguration', 'EnvironmentData',
    'PackageHostConfiguration', 'EnvironmentPackageEntry', 'ConfigurationResult', 'SyncResult',
    'MCPHostRegistry', 'MCPHostStrategy', 'MCPHostConfigurationManager', 'register_host_strategy'
]
