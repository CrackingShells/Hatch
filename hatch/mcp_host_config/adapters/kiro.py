"""Kiro adapter for MCP host configuration.

Kiro has specific features:
- No 'type' field support
- Server enable/disable via 'disabled' field
- Tool management: autoApprove, disabledTools
"""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import KIRO_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class KiroAdapter(BaseAdapter):
    """Adapter for Kiro MCP host.
    
    Kiro is similar to Claude but without the 'type' field:
    - Requires exactly one transport (command XOR url)
    - Has 'disabled' field for toggling server
    - Has 'autoApprove' for auto-approved tools
    - Has 'disabledTools' for disabled tools
    """
    
    @property
    def host_name(self) -> str:
        """Return the host identifier."""
        return "kiro"
    
    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields supported by Kiro."""
        return KIRO_FIELDS
    
    def validate(self, config: MCPServerConfig) -> None:
        """Validate configuration for Kiro.
        
        Like Claude, requires exactly one transport.
        Does not support 'type' field.
        """
        has_command = config.command is not None
        has_url = config.url is not None
        has_http_url = config.httpUrl is not None
        
        # Kiro doesn't support httpUrl
        if has_http_url:
            raise AdapterValidationError(
                "httpUrl is not supported (use 'url' for remote servers)",
                field="httpUrl",
                host_name=self.host_name
            )
        
        # Must have exactly one transport
        if not has_command and not has_url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) must be specified",
                host_name=self.host_name
            )
        
        if has_command and has_url:
            raise AdapterValidationError(
                "Cannot specify both 'command' and 'url' - choose one transport",
                host_name=self.host_name
            )
        
        # 'type' field is not supported by Kiro
        if config.type is not None:
            raise AdapterValidationError(
                "'type' field is not supported by Kiro",
                field="type",
                host_name=self.host_name
            )
    
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Kiro format."""
        self.validate(config)
        return self.filter_fields(config)

