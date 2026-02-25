"""OpenCode adapter for MCP host configuration.

OpenCode uses a discriminated-union format with structural differences
from the universal schema:
- 'type' field is 'local' or 'remote' (not 'stdio'/'sse'/'http')
- 'command' is an array: [executable, ...args] (not a string)
- 'env' is renamed to 'environment'
- OAuth is nested under an 'oauth' key, or set to false to disable
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import OPENCODE_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class OpenCodeAdapter(BaseAdapter):
    """Adapter for OpenCode MCP host.

    OpenCode uses a discriminated-union format where transport type is
    derived from configuration presence:
    - Local (stdio): command string + args list merged into command array,
      env renamed to environment, type set to 'local'
    - Remote (sse): url preserved, headers preserved, type set to 'remote'

    OAuth configuration is nested:
    - opencode_oauth_disable=True serializes as oauth: false
    - oauth_clientId/clientSecret/opencode_oauth_scope serialize as
      oauth: {clientId, clientSecret, scope} (omitting null values)
    """

    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "opencode"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by OpenCode."""
        return OPENCODE_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for OpenCode.

        DEPRECATED: This method is deprecated and will be removed in v0.9.0.
        Use validate_filtered() instead.

        OpenCode requires exactly one transport (command XOR url).
        """
        has_command = config.command is not None
        has_url = config.url is not None

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
        """Validate filtered configuration for OpenCode.

        Validates only fields that survived filtering (supported by OpenCode).
        OpenCode requires exactly one transport (command XOR url).

        Args:
            filtered: Dictionary of filtered fields

        Raises:
            AdapterValidationError: If validation fails
        """
        has_command = "command" in filtered
        has_url = "url" in filtered

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
        """Serialize configuration to OpenCode format.

        OpenCode structural transforms:
        1. Filter to supported fields
        2. Validate transport mutual exclusion
        3. Build output dict with OpenCode-native structure:
           - Derive type: 'local' (command present) or 'remote' (url present)
           - Local: merge command + args into command array, rename env→environment
           - Remote: preserve url and headers as-is
           - Both: include enabled, timeout if set
           - OAuth: emit oauth: false if disabled, or oauth: {...} object if configured

        Args:
            config: The MCPServerConfig to serialize

        Returns:
            Dictionary in OpenCode's expected format
        """
        # Filter to supported fields
        filtered = self.filter_fields(config)

        # Validate transport mutual exclusion
        self.validate_filtered(filtered)

        result: Dict[str, Any] = {}

        if "command" in filtered:
            # Local transport: derive type, merge command+args, rename env
            result["type"] = "local"
            command = filtered["command"]
            args = filtered.get("args") or []
            result["command"] = [command] + args
            if "env" in filtered:
                result["environment"] = filtered["env"]
        else:
            # Remote transport: derive type, preserve url and headers
            result["type"] = "remote"
            result["url"] = filtered["url"]
            if "headers" in filtered:
                result["headers"] = filtered["headers"]

        # Optional shared fields
        if "enabled" in filtered:
            result["enabled"] = filtered["enabled"]
        if "timeout" in filtered:
            result["timeout"] = filtered["timeout"]

        # OAuth configuration
        if filtered.get("opencode_oauth_disable"):
            result["oauth"] = False
        else:
            oauth: Dict[str, Any] = {}
            if filtered.get("oauth_clientId"):
                oauth["clientId"] = filtered["oauth_clientId"]
            if filtered.get("oauth_clientSecret"):
                oauth["clientSecret"] = filtered["oauth_clientSecret"]
            if filtered.get("opencode_oauth_scope"):
                oauth["scope"] = filtered["opencode_oauth_scope"]
            if oauth:
                result["oauth"] = oauth

        return result
