"""Cursor adapter for MCP host configuration.

Cursor is similar to VSCode but with limited additional fields:
- envFile: Path to environment file (like VSCode)
- No 'inputs' field support (VSCode only)
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import CURSOR_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class CursorAdapter(BaseAdapter):
    """Adapter for Cursor MCP host.
    
    Cursor is like a simplified VSCode:
    - Supports Claude base fields + envFile
    - Does NOT support inputs (VSCode-only feature)
    - Requires exactly one transport (command XOR url)
    """
    
    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "cursor"
    
    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Cursor."""
        return CURSOR_FIELDS
    
    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for Cursor.
        
        Same rules as Claude: exactly one transport required.
        Warns if 'inputs' is specified (not supported).
        """
        has_command = config.command is not None
        has_url = config.url is not None
        has_http_url = config.httpUrl is not None
        
        # Cursor doesn't support httpUrl
        if has_http_url:
            raise AdapterValidationError(
                "httpUrl is not supported (use 'url' for remote servers)",
                field="httpUrl",
                host_name=self.host_name
            )
        
        # Must have exactly one transport
        if not has_command and not has_url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) must be specified",
                host_name=self.host_name
            )
        
        if has_command and has_url:
            raise AdapterValidationError(
                "Cannot specify both 'command' and 'url' - choose one transport",
                host_name=self.host_name
            )
        
        # Validate type consistency if specified
        if config.type is not None:
            if config.type == "stdio" and not has_command:
                raise AdapterValidationError(
                    "type='stdio' requires 'command' field",
                    field="type",
                    host_name=self.host_name
                )
            if config.type in ("sse", "http") and not has_url:
                raise AdapterValidationError(
                    f"type='{config.type}' requires 'url' field",
                    field="type",
                    host_name=self.host_name
                )
    
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Cursor format."""
        self.validate(config)
        return self.filter_fields(config)

