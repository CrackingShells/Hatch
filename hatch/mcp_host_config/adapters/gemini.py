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

        # Must have exactly one transport (mutual exclusion)
        # Count how many transports are present
        transport_count = sum([has_command, has_url, has_http_url])

        if transport_count == 0:
            raise AdapterValidationError(
                "At least one transport must be specified: 'command', 'url', or 'httpUrl'",
                host_name=self.host_name,
            )

        if transport_count > 1:
            raise AdapterValidationError(
                "Only one transport allowed: command, url, or httpUrl (not multiple)",
                host_name=self.host_name,
            )

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Gemini format."""
        self.validate(config)
        return self.filter_fields(config)
