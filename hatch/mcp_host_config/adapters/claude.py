"""Claude Desktop/Code adapter for MCP host configuration.

Claude Desktop and Claude Code share the same configuration format:
- Supports 'type' field for transport discrimination
- Mutually exclusive: command XOR url (never both)
- Standard field set: command, args, env, url, headers, type
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import CLAUDE_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class ClaudeAdapter(BaseAdapter):
    """Adapter for Claude Desktop and Claude Code hosts.

    Claude uses a strict validation model:
    - Local servers: command (required), args, env
    - Remote servers: url (required), headers, env
    - Never both command and url

    Supports the 'type' field for explicit transport discrimination.
    """

    def __init__(self, variant: str = "desktop"):
        """Initialize Claude adapter.

        Args:
            variant: Either "desktop" or "code" to specify the Claude variant.
        """
        if variant not in ("desktop", "code"):
            raise ValueError(
                f"Invalid Claude variant: {variant}. Must be 'desktop' or 'code'"
            )
        self._variant = variant

    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return f"claude-{self._variant}"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Claude."""
        return CLAUDE_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for Claude.

        DEPRECATED: This method is deprecated and will be removed in v0.9.0.
        Use validate_filtered() instead.

        Claude requires exactly one transport:
        - stdio (command)
        - sse (url)

        Having both command and url is invalid.
        """
        has_command = config.command is not None
        has_url = config.url is not None
        has_http_url = config.httpUrl is not None

        # Claude doesn't support httpUrl
        if has_http_url:
            raise AdapterValidationError(
                "httpUrl is not supported (use 'url' for remote servers)",
                field="httpUrl",
                host_name=self.host_name,
            )

        # Must have exactly one transport
        if not has_command and not has_url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) must be specified",
                host_name=self.host_name,
            )

        if has_command and has_url:
            raise AdapterValidationError(
                "Cannot specify both 'command' and 'url' - choose one transport",
                host_name=self.host_name,
            )

        # Validate type consistency if specified
        if config.type is not None:
            if config.type == "stdio" and not has_command:
                raise AdapterValidationError(
                    "type='stdio' requires 'command' field",
                    field="type",
                    host_name=self.host_name,
                )
            if config.type in ("sse", "http") and not has_url:
                raise AdapterValidationError(
                    f"type='{config.type}' requires 'url' field",
                    field="type",
                    host_name=self.host_name,
                )

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate filtered configuration for Claude.

        Validates only fields that survived filtering (supported by Claude).
        Does NOT check for unsupported fields like httpUrl (already filtered).

        Claude requires exactly one transport:
        - stdio (command)
        - sse (url)

        Args:
            filtered: Dictionary of filtered fields

        Raises:
            AdapterValidationError: If validation fails
        """
        has_command = "command" in filtered
        has_url = "url" in filtered

        # Must have exactly one transport
        if not has_command and not has_url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) must be specified",
                host_name=self.host_name,
            )

        if has_command and has_url:
            raise AdapterValidationError(
                "Cannot specify both 'command' and 'url' - choose one transport",
                host_name=self.host_name,
            )

        # Validate type consistency if specified
        if "type" in filtered:
            config_type = filtered["type"]
            if config_type == "stdio" and not has_command:
                raise AdapterValidationError(
                    "type='stdio' requires 'command' field",
                    field="type",
                    host_name=self.host_name,
                )
            if config_type in ("sse", "http") and not has_url:
                raise AdapterValidationError(
                    f"type='{config_type}' requires 'url' field",
                    field="type",
                    host_name=self.host_name,
                )

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Claude format.

        Returns a dictionary suitable for Claude's config.json format.

        Follows the validate-after-filter pattern:
        1. Filter to supported fields
        2. Validate filtered fields
        3. Return filtered (no transformations needed)
        """
        # Filter to supported fields
        filtered = self.filter_fields(config)

        # Validate filtered fields
        self.validate_filtered(filtered)

        # Return filtered (no transformations needed for Claude)
        return filtered
