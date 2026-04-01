"""Augment Code adapter for MCP host configuration.

Augment Code (auggie CLI + extensions) uses the same field set as Claude:
command/args/env for stdio, url/headers for sse/http, with optional type discriminator.
Config file: ~/.augment/settings.json, root key: mcpServers.
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import AUGMENT_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class AugmentAdapter(BaseAdapter):
    """Adapter for Augment Code MCP host.

    Augment Code uses the same configuration format as Claude:
    - Supports 'type' field for transport discrimination
    - Requires exactly one transport (command XOR url)
    """

    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "augment"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Augment Code."""
        return AUGMENT_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for Augment Code.

        DEPRECATED: This method is deprecated and will be removed in v0.9.0.
        Use validate_filtered() instead.
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
        """Validate filtered configuration for Augment Code.

        Validates only fields that survived filtering (supported by Augment).
        Augment Code requires exactly one transport (command XOR url).

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
        """Serialize configuration for Augment Code format.

        Follows the validate-after-filter pattern:
        1. Filter to supported fields
        2. Validate filtered fields
        3. Return filtered (no transformations needed)
        """
        filtered = self.filter_fields(config)
        self.validate_filtered(filtered)
        return filtered
