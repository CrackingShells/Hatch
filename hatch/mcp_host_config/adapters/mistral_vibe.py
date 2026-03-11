"""Mistral Vibe adapter for MCP host configuration.

Mistral Vibe uses TOML `[[mcp_servers]]` entries with an explicit `transport`
field instead of the Claude-style `type` discriminator.
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import MISTRAL_VIBE_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class MistralVibeAdapter(BaseAdapter):
    """Adapter for Mistral Vibe MCP server configuration."""

    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "mistral-vibe"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Mistral Vibe."""
        return MISTRAL_VIBE_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        """Deprecated compatibility wrapper for legacy adapter tests."""
        self.validate_filtered(self.filter_fields(config))

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate Mistral Vibe transport rules on filtered fields."""
        has_command = "command" in filtered
        has_url = "url" in filtered
        transport_count = sum([has_command, has_url])

        if transport_count == 0:
            raise AdapterValidationError(
                "Either 'command' or 'url' must be specified",
                host_name=self.host_name,
            )

        if transport_count > 1:
            raise AdapterValidationError(
                "Cannot specify multiple transports - choose exactly one of 'command' or 'url'",
                host_name=self.host_name,
            )

        transport = filtered.get("transport")
        if transport == "stdio" and not has_command:
            raise AdapterValidationError(
                "transport='stdio' requires 'command' field",
                field="transport",
                host_name=self.host_name,
            )
        if transport in ("http", "streamable-http") and not has_url:
            raise AdapterValidationError(
                f"transport='{transport}' requires 'url' field",
                field="transport",
                host_name=self.host_name,
            )

    def apply_transformations(
        self, filtered: Dict[str, Any], transport_hint: str | None = None
    ) -> Dict[str, Any]:
        """Apply Mistral Vibe field/value transformations."""
        result = dict(filtered)

        transport = (
            result.get("transport") or transport_hint or self._infer_transport(result)
        )
        result["transport"] = transport

        return result

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Mistral Vibe format."""
        filtered = self.filter_fields(config)

        # Support cross-host sync hints without advertising these as native fields.
        if (
            "command" not in filtered
            and "url" not in filtered
            and config.httpUrl is not None
        ):
            filtered["url"] = config.httpUrl

        transport_hint = self._infer_transport(filtered, config=config)
        if transport_hint is not None:
            filtered["transport"] = transport_hint

        self.validate_filtered(filtered)
        return self.apply_transformations(filtered)

    def _infer_transport(
        self, filtered: Dict[str, Any], config: MCPServerConfig | None = None
    ) -> str | None:
        """Infer Vibe transport from canonical MCP fields."""
        if "transport" in filtered:
            return filtered["transport"]
        if "command" in filtered:
            return "stdio"

        config_type = config.type if config is not None else None
        if config_type == "stdio":
            return "stdio"
        if config_type == "http":
            return "http"
        if config_type == "sse":
            return "streamable-http"

        if config is not None and config.httpUrl is not None:
            return "http"
        if "url" in filtered:
            return "streamable-http"

        return None
