"""MCP Host Config Adapters.

This module provides host-specific adapters for the Unified Adapter Architecture.
Each adapter handles validation and serialization for a specific MCP host.
"""

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.adapters.claude import ClaudeAdapter
from hatch.mcp_host_config.adapters.codex import CodexAdapter
from hatch.mcp_host_config.adapters.cursor import CursorAdapter
from hatch.mcp_host_config.adapters.gemini import GeminiAdapter
from hatch.mcp_host_config.adapters.kiro import KiroAdapter
from hatch.mcp_host_config.adapters.lmstudio import LMStudioAdapter
from hatch.mcp_host_config.adapters.opencode import OpenCodeAdapter
from hatch.mcp_host_config.adapters.registry import (
    AdapterRegistry,
    get_adapter,
    get_default_registry,
)
from hatch.mcp_host_config.adapters.vscode import VSCodeAdapter

__all__ = [
    # Base classes and exceptions
    "AdapterValidationError",
    "BaseAdapter",
    # Registry
    "AdapterRegistry",
    "get_adapter",
    "get_default_registry",
    # Host-specific adapters
    "ClaudeAdapter",
    "CodexAdapter",
    "CursorAdapter",
    "GeminiAdapter",
    "KiroAdapter",
    "LMStudioAdapter",
    "OpenCodeAdapter",
    "VSCodeAdapter",
]
