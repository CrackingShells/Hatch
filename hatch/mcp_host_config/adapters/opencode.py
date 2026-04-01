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
        """Serialize configuration for OpenCode (canonical form).

        Returns a filtered, validated dict using MCPServerConfig field names.
        Structural transforms (command array merge, env→environment rename,
        type derivation, oauth nesting) are applied by the strategy's
        write_configuration() via to_native_format().

        Args:
            config: The MCPServerConfig to serialize

        Returns:
            Filtered dict with MCPServerConfig-canonical field names
        """
        filtered = self.filter_fields(config)
        self.validate_filtered(filtered)
        return filtered

    @staticmethod
    def to_native_format(filtered: Dict[str, Any]) -> Dict[str, Any]:
        """Convert canonical-form dict to OpenCode-native file format.

        Applies OpenCode structural transforms:
        - Derives type: 'local' (command present) or 'remote' (url present)
        - Local: merges command + args into command array, renames env→environment
        - Remote: preserves url and headers as-is
        - Handles enabled, timeout if present
        - OAuth: emits oauth: false or oauth: {clientId, clientSecret, scope}

        Args:
            filtered: Canonical-form dict from serialize()

        Returns:
            Dict in OpenCode's native file format
        """
        result: Dict[str, Any] = {}

        if "command" in filtered:
            result["type"] = "local"
            command = filtered["command"]
            args = filtered.get("args") or []
            result["command"] = [command] + args
            if "env" in filtered:
                result["environment"] = filtered["env"]
        else:
            result["type"] = "remote"
            result["url"] = filtered["url"]
            if "headers" in filtered:
                result["headers"] = filtered["headers"]

        if "enabled" in filtered:
            result["enabled"] = filtered["enabled"]
        if "timeout" in filtered:
            result["timeout"] = filtered["timeout"]

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
