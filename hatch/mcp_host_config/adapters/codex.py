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

        DEPRECATED: This method is deprecated and will be removed in v0.9.0.
        Use validate_filtered() instead.

        Codex requires exactly one transport (command XOR url).
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

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate filtered configuration for Codex.

        Validates only fields that survived filtering (supported by Codex).
        Does NOT check for unsupported fields like httpUrl or type (already filtered).

        Codex requires exactly one transport (command XOR url).

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

    def apply_transformations(self, filtered: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Codex-specific field transformations.

        Codex uses different field names than the universal schema:
        - args → arguments
        - headers → http_headers
        - includeTools → enabled_tools (for cross-host sync from Gemini)
        - excludeTools → disabled_tools (for cross-host sync from Gemini)

        Args:
            filtered: Dictionary of validated, filtered fields

        Returns:
            Transformed dictionary with Codex field names
        """
        result = filtered.copy()

        # Apply field mappings
        for universal_name, codex_name in CODEX_FIELD_MAPPINGS.items():
            if universal_name in result:
                result[codex_name] = result.pop(universal_name)

        return result

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Codex format.

        Follows the validate-after-filter pattern:
        1. Filter to supported fields
        2. Validate filtered fields
        3. Transform fields (apply field mappings)
        4. Return transformed

        Applies field mappings:
        - args → arguments
        - headers → http_headers
        """
        # Filter to supported fields
        filtered = self.filter_fields(config)

        # Validate filtered fields
        self.validate_filtered(filtered)

        # Transform fields (apply field mappings)
        transformed = self.apply_transformations(filtered)

        return transformed
