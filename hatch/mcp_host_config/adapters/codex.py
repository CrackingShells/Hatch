"""Codex CLI adapter for MCP host configuration.

Codex CLI has unique features:
- No 'type' field support
- Field name mappings: args→arguments, headers→http_headers
- Rich configuration: timeouts, env_vars, tool management, bearer tokens
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import CODEX_FIELDS, CODEX_FIELD_MAPPINGS
from hatch.mcp_host_config.models import MCPServerConfig


class CodexAdapter(BaseAdapter):
    """Adapter for Codex CLI MCP host.

    Codex uses different field names than other hosts:
    - 'args' → 'arguments'
    - 'headers' → 'http_headers'

    Codex also has:
    - Working directory support (cwd)
    - Timeout configuration (startup_timeout_sec, tool_timeout_sec)
    - Server enable/disable (enabled)
    - Tool filtering (enabled_tools, disabled_tools)
    - Bearer token support (bearer_token_env_var)
    """

    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "codex"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Codex."""
        return CODEX_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for Codex.

        Codex requires exactly one transport (command XOR url).
        Does not support 'type' field.
        """
        has_command = config.command is not None
        has_url = config.url is not None
        has_http_url = config.httpUrl is not None

        # Codex doesn't support httpUrl
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

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Codex format.

        Applies field mappings:
        - args → arguments
        - headers → http_headers
        """
        self.validate(config)

        # Get base filtered fields
        result = self.filter_fields(config)

        # Apply field mappings
        for universal_name, codex_name in CODEX_FIELD_MAPPINGS.items():
            if universal_name in result:
                result[codex_name] = result.pop(universal_name)

        return result
