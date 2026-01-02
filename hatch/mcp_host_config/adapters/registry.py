"""Adapter registry for MCP host configurations.

This module provides a centralized registry for host-specific adapters.
The registry maps host names to adapter instances and provides factory methods.
"""

from typing import Dict, List, Optional, Type

from hatch.mcp_host_config.adapters.base import BaseAdapter
from hatch.mcp_host_config.adapters.claude import ClaudeAdapter
from hatch.mcp_host_config.adapters.codex import CodexAdapter
from hatch.mcp_host_config.adapters.cursor import CursorAdapter
from hatch.mcp_host_config.adapters.gemini import GeminiAdapter
from hatch.mcp_host_config.adapters.kiro import KiroAdapter
from hatch.mcp_host_config.adapters.vscode import VSCodeAdapter


class AdapterRegistry:
    """Registry for MCP host configuration adapters.
    
    The registry provides:
    - Host name to adapter mapping
    - Factory method to get adapters by host name
    - Registration of custom adapters
    - List of all supported hosts
    
    Example:
        >>> registry = AdapterRegistry()
        >>> adapter = registry.get_adapter("claude-desktop")
        >>> adapter.host_name
        'claude-desktop'
        
        >>> registry.get_supported_hosts()
        ['claude-code', 'claude-desktop', 'codex', 'cursor', 'gemini', 'kiro', 'vscode']
    """
    
    def __init__(self):
        """Initialize the registry with default adapters."""
        self._adapters: Dict[str, BaseAdapter] = {}
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register all built-in adapters."""
        # Claude variants
        self.register(ClaudeAdapter(variant="desktop"))
        self.register(ClaudeAdapter(variant="code"))
        
        # Other hosts
        self.register(VSCodeAdapter())
        self.register(CursorAdapter())
        self.register(GeminiAdapter())
        self.register(KiroAdapter())
        self.register(CodexAdapter())
    
    def register(self, adapter: BaseAdapter) -> None:
        """Register an adapter instance.
        
        Args:
            adapter: The adapter instance to register
            
        Raises:
            ValueError: If an adapter with the same host name is already registered
        """
        host_name = adapter.host_name
        if host_name in self._adapters:
            raise ValueError(f"Adapter for '{host_name}' is already registered")
        self._adapters[host_name] = adapter
    
    def get_adapter(self, host_name: str) -> BaseAdapter:
        """Get an adapter by host name.
        
        Args:
            host_name: The host identifier (e.g., "claude-desktop", "gemini")
            
        Returns:
            The adapter instance for the specified host
            
        Raises:
            KeyError: If no adapter is registered for the host name
        """
        if host_name not in self._adapters:
            supported = ", ".join(sorted(self._adapters.keys()))
            raise KeyError(f"No adapter registered for '{host_name}'. Supported hosts: {supported}")
        return self._adapters[host_name]
    
    def has_adapter(self, host_name: str) -> bool:
        """Check if an adapter is registered for a host name.
        
        Args:
            host_name: The host identifier to check
            
        Returns:
            True if an adapter is registered, False otherwise
        """
        return host_name in self._adapters
    
    def get_supported_hosts(self) -> List[str]:
        """Get a sorted list of all supported host names.
        
        Returns:
            Sorted list of host name strings
        """
        return sorted(self._adapters.keys())
    
    def unregister(self, host_name: str) -> None:
        """Unregister an adapter by host name.
        
        Args:
            host_name: The host identifier to unregister
            
        Raises:
            KeyError: If no adapter is registered for the host name
        """
        if host_name not in self._adapters:
            raise KeyError(f"No adapter registered for '{host_name}'")
        del self._adapters[host_name]


# Global registry instance for convenience
_default_registry: Optional[AdapterRegistry] = None


def get_default_registry() -> AdapterRegistry:
    """Get the default global adapter registry.
    
    Returns:
        The singleton AdapterRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = AdapterRegistry()
    return _default_registry


def get_adapter(host_name: str) -> BaseAdapter:
    """Get an adapter from the default registry.
    
    This is a convenience function that uses the global registry.
    
    Args:
        host_name: The host identifier (e.g., "claude-desktop", "gemini")
        
    Returns:
        The adapter instance for the specified host
    """
    return get_default_registry().get_adapter(host_name)

