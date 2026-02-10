"""VSCode adapter for MCP host configuration.

VSCode extends Claude's format with:
- envFile: Path to environment file
- inputs: Input variable definitions (VSCode only)
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import VSCODE_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class VSCodeAdapter(BaseAdapter):
    """Adapter for Visual Studio Code MCP host.

    VSCode supports the same base configuration as Claude, plus:
    - envFile: Path to a .env file for environment variables
    - inputs: Array of input variable definitions for prompts

    Like Claude, it requires exactly one transport (command XOR url).
    """

    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "vscode"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by VSCode."""
        return VSCODE_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for VSCode.

        Same rules as Claude: exactly one transport required.
        """
        has_command = config.command is not None
        has_url = config.url is not None
        has_http_url = config.httpUrl is not None

        # VSCode doesn't support httpUrl
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

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for VSCode format."""
        self.validate(config)
        return self.filter_fields(config)
