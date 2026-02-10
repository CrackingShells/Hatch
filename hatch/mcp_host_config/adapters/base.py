"""Base adapter class for MCP host configurations.

This module defines the abstract BaseAdapter class that all host-specific
adapters must implement. The adapter pattern allows for:
- Host-specific validation rules
- Host-specific serialization format
- Unified interface across all hosts
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, FrozenSet, Optional

from hatch.mcp_host_config.models import MCPServerConfig
from hatch.mcp_host_config.fields import EXCLUDED_ALWAYS


class AdapterValidationError(Exception):
    """Raised when adapter validation fails.

    Attributes:
        message: Human-readable error message
        field: The field that caused the error (if applicable)
        host_name: The host adapter that raised the error
    """

    def __init__(
        self, message: str, field: Optional[str] = None, host_name: Optional[str] = None
    ):
        self.message = message
        self.field = field
        self.host_name = host_name
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with optional context."""
        parts = []
        if self.host_name:
            parts.append(f"[{self.host_name}]")
        if self.field:
            parts.append(f"Field '{self.field}':")
        parts.append(self.message)
        return " ".join(parts)


class BaseAdapter(ABC):
    """Abstract base class for host-specific MCP configuration adapters.

    Each host (Claude Desktop, VSCode, Gemini, etc.) has different requirements
    for MCP server configuration. Adapters handle:

    1. **Validation**: Host-specific rules (e.g., "command and url are mutually
       exclusive" for Claude, but not for Gemini which supports triple transport)

    2. **Serialization**: Converting MCPServerConfig to the host's expected format
       (field names, structure, excluded fields)

    3. **Field Support**: Declaring which fields the host supports

    Subclasses must implement:
        - host_name: The identifier for this host
        - get_supported_fields(): Fields this host accepts
        - validate(): Host-specific validation logic
        - serialize(): Convert config to host format

    Example:
        >>> class ClaudeAdapter(BaseAdapter):
        ...     @property
        ...     def host_name(self) -> str:
        ...         return "claude-desktop"
        ...
        ...     def get_supported_fields(self) -> FrozenSet[str]:
        ...         return frozenset({"command", "args", "env", "url", "headers", "type"})
        ...
        ...     def validate(self, config: MCPServerConfig) -> None:
        ...         if config.command and config.url:
        ...             raise AdapterValidationError("Cannot have both command and url")
        ...
        ...     def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        ...         return {k: v for k, v in config.model_dump().items() if v is not None}
    """

    @property
    @abstractmethod
    def host_name(self) -> str:
        """Return the identifier for this host.

        Returns:
            Host identifier string (e.g., "claude-desktop", "vscode", "gemini")
        """
        ...

    @abstractmethod
    def get_supported_fields(self) -> FrozenSet[str]:
        """Return the set of fields supported by this host.

        Returns:
            FrozenSet of field names that this host accepts.
            Fields not in this set will be filtered during serialization.
        """
        ...

    @abstractmethod
    def validate(self, config: MCPServerConfig) -> None:
        """Validate the configuration for this host.

        This method should check host-specific rules and raise
        AdapterValidationError if the configuration is invalid.

        Args:
            config: The MCPServerConfig to validate

        Raises:
            AdapterValidationError: If validation fails
        """
        ...

    @abstractmethod
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize the configuration for this host.

        This method should convert the MCPServerConfig to the format
        expected by the host's configuration file.

        Args:
            config: The MCPServerConfig to serialize

        Returns:
            Dictionary in the host's expected format
        """
        ...

    def get_excluded_fields(self) -> FrozenSet[str]:
        """Return fields that should always be excluded from serialization.

        By default, returns EXCLUDED_ALWAYS (e.g., 'name' which is Hatch metadata).
        Subclasses can override to add host-specific exclusions.

        Returns:
            FrozenSet of field names to exclude
        """
        return EXCLUDED_ALWAYS

    def filter_fields(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Filter config to only include supported, non-excluded, non-None fields.

        This is a helper method for serialization that:
        1. Gets all fields from the config
        2. Filters to only supported fields
        3. Removes excluded fields
        4. Removes None values

        Args:
            config: The MCPServerConfig to filter

        Returns:
            Dictionary with only valid fields for this host
        """
        supported = self.get_supported_fields()
        excluded = self.get_excluded_fields()

        result = {}
        for field, value in config.model_dump(exclude_none=True).items():
            if field in supported and field not in excluded:
                result[field] = value

        return result
