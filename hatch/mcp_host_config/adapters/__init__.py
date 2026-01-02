"""MCP Host Config Adapters.

This module provides host-specific adapters for the Unified Adapter Architecture.
Each adapter handles validation and serialization for a specific MCP host.
"""

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter

__all__ = ["AdapterValidationError", "BaseAdapter"]

