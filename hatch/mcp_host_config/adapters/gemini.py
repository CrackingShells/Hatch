"""Gemini CLI adapter for MCP host configuration.

Gemini has unique features:
- Triple transport: command (stdio), url (SSE), httpUrl (HTTP streaming)
- Multiple transports can coexist (not mutually exclusive)
- No 'type' field support
- Rich OAuth configuration
- Working directory, timeout, trust settings
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import GEMINI_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class GeminiAdapter(BaseAdapter):
    """Adapter for Gemini CLI MCP host.
    
    Gemini is unique among MCP hosts:
    - Supports THREE transport types (stdio, SSE, HTTP streaming)
    - Transports are NOT mutually exclusive (can have multiple)
    - Does NOT support 'type' field
    - Has rich configuration: OAuth, timeout, trust, tool filtering
    """
    
    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "gemini"
    
    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Gemini."""
        return GEMINI_FIELDS
    
    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for Gemini.
        
        Gemini is flexible:
        - At least one transport is required (command, url, or httpUrl)
        - Multiple transports are allowed
        - 'type' field is not supported
        """
        has_command = config.command is not None
        has_url = config.url is not None
        has_http_url = config.httpUrl is not None
        
        # Must have at least one transport
        if not has_command and not has_url and not has_http_url:
            raise AdapterValidationError(
                "At least one transport must be specified: 'command', 'url', or 'httpUrl'",
                host_name=self.host_name
            )
        
        # 'type' field is not supported by Gemini
        if config.type is not None:
            raise AdapterValidationError(
                "'type' field is not supported by Gemini CLI",
                field="type",
                host_name=self.host_name
            )
        
        # Validate includeTools and excludeTools are mutually exclusive
        if config.includeTools is not None and config.excludeTools is not None:
            raise AdapterValidationError(
                "Cannot specify both 'includeTools' and 'excludeTools'",
                host_name=self.host_name
            )
    
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Gemini format."""
        self.validate(config)
        return self.filter_fields(config)

