"""MCP (Model Context Protocol) support for Hatch.

This module provides MCP host configuration management functionality,
including backup and restore capabilities for MCP server configurations,
decorator-based strategy registration, and consolidated Pydantic models.
"""

from .backup import MCPHostConfigBackupManager
from .models import (
    MCPHostType, MCPServerConfig, HostConfiguration, EnvironmentData,
    PackageHostConfiguration, EnvironmentPackageEntry, ConfigurationResult, SyncResult,
    # Host-specific configuration models
    MCPServerConfigBase, MCPServerConfigGemini, MCPServerConfigVSCode,
    MCPServerConfigCursor, MCPServerConfigClaude, MCPServerConfigKiro,
    MCPServerConfigCodex, MCPServerConfigOmni,
    HOST_MODEL_REGISTRY
)
from .host_management import (
    MCPHostRegistry, MCPHostStrategy, MCPHostConfigurationManager, register_host_strategy
)
from .reporting import (
    FieldOperation, ConversionReport, generate_conversion_report, display_report
)

# Import strategies to trigger decorator registration
from . import strategies

__all__ = [
    'MCPHostConfigBackupManager',
    'MCPHostType', 'MCPServerConfig', 'HostConfiguration', 'EnvironmentData',
    'PackageHostConfiguration', 'EnvironmentPackageEntry', 'ConfigurationResult', 'SyncResult',
    # Host-specific configuration models
    'MCPServerConfigBase', 'MCPServerConfigGemini', 'MCPServerConfigVSCode',
    'MCPServerConfigCursor', 'MCPServerConfigClaude', 'MCPServerConfigKiro',
    'MCPServerConfigCodex', 'MCPServerConfigOmni',
    'HOST_MODEL_REGISTRY',
    # User feedback reporting
    'FieldOperation', 'ConversionReport', 'generate_conversion_report', 'display_report',
    'MCPHostRegistry', 'MCPHostStrategy', 'MCPHostConfigurationManager', 'register_host_strategy'
]
