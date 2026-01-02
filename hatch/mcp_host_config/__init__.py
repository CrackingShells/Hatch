"""MCP (Model Context Protocol) support for Hatch.

This module provides MCP host configuration management functionality,
including backup and restore capabilities for MCP server configurations,
decorator-based strategy registration, and consolidated Pydantic models.

Architecture Notes (v2.0 - Unified Adapter Architecture):
- MCPServerConfig is the single unified model for all MCP configurations
- Host-specific serialization is handled by adapters in hatch/mcp_host_config/adapters/
- Legacy host-specific models (MCPServerConfigGemini, etc.) have been removed
"""

from .backup import MCPHostConfigBackupManager
from .models import (
    MCPHostType, MCPServerConfig, HostConfiguration, EnvironmentData,
    PackageHostConfiguration, EnvironmentPackageEntry, ConfigurationResult, SyncResult,
)
from .host_management import (
    MCPHostRegistry, MCPHostStrategy, MCPHostConfigurationManager, register_host_strategy
)
from .reporting import (
    FieldOperation, ConversionReport, generate_conversion_report, display_report
)
from .adapters import HostAdapterRegistry

# Import strategies to trigger decorator registration
from . import strategies

__all__ = [
    'MCPHostConfigBackupManager',
    # Core models
    'MCPHostType', 'MCPServerConfig', 'HostConfiguration', 'EnvironmentData',
    'PackageHostConfiguration', 'EnvironmentPackageEntry', 'ConfigurationResult', 'SyncResult',
    # Adapter architecture
    'HostAdapterRegistry',
    # User feedback reporting
    'FieldOperation', 'ConversionReport', 'generate_conversion_report', 'display_report',
    # Host management
    'MCPHostRegistry', 'MCPHostStrategy', 'MCPHostConfigurationManager', 'register_host_strategy'
]
