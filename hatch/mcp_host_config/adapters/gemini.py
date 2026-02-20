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

        DEPRECATED: This method is deprecated and will be removed in v0.9.0.
        Use validate_filtered() instead.

        Gemini requires exactly one transport (command, url, or httpUrl).
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

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate filtered configuration for Gemini.

        Validates only fields that survived filtering (supported by Gemini).
        Does NOT check for unsupported fields like type (already filtered).

        Gemini requires exactly one transport: command, url, or httpUrl.

        Args:
            filtered: Dictionary of filtered fields

        Raises:
            AdapterValidationError: If validation fails
        """
        has_command = "command" in filtered
        has_url = "url" in filtered
        has_http_url = "httpUrl" in filtered

        # Must have exactly one transport (mutual exclusion)
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
        """Serialize configuration for Gemini format.

        Follows the validate-after-filter pattern:
        1. Filter to supported fields
        2. Validate filtered fields
        3. Return filtered (no transformations needed)
        """
        # Filter to supported fields
        filtered = self.filter_fields(config)

        # Validate filtered fields
        self.validate_filtered(filtered)

        # Return filtered (no transformations needed for Gemini)
        return filtered
