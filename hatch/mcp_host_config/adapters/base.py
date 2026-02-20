"""Base adapter class for MCP host configurations.

This module defines the abstract BaseAdapter class that all host-specific
adapters must implement. The adapter pattern allows for:
- Host-specific validation rules
- Host-specific serialization format
- Unified interface across all hosts

Migration Note (v0.8.0):
    The adapter architecture has been refactored to follow a validate-after-filter
    pattern. Adapters now implement validate_filtered() instead of validate().
    This change fixes cross-host sync failures by ensuring validation only checks
    fields that the target host actually supports.

    Old validate() methods are deprecated and will be removed in v0.9.0.
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

    Architecture Pattern (validate-after-filter):
        The standard implementation follows: filter → validate → transform

        1. Filter: Remove unsupported fields (filter_fields)
        2. Validate: Check logical constraints on remaining fields (validate_filtered)
        3. Transform: Apply field mappings if needed (apply_transformations)

        This pattern ensures validation only checks fields the host actually supports,
        preventing false rejections during cross-host sync operations.

    Subclasses must implement:
        - host_name: The identifier for this host
        - get_supported_fields(): Fields this host accepts
        - validate_filtered(): Host-specific validation logic (NEW PATTERN)
        - serialize(): Convert config to host format

    Subclasses may override:
        - apply_transformations(): Field name/value transformations (default: no-op)
        - get_excluded_fields(): Additional fields to exclude (default: EXCLUDED_ALWAYS)

    Deprecated methods:
        - validate(): Old validation pattern, will be removed in v0.9.0
          Use validate_filtered() instead

    Example (new pattern):
        >>> class ClaudeAdapter(BaseAdapter):
        ...     @property
        ...     def host_name(self) -> str:
        ...         return "claude-desktop"
        ...
        ...     def get_supported_fields(self) -> FrozenSet[str]:
        ...         return frozenset({"command", "args", "env", "url", "headers", "type"})
        ...
        ...     def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        ...         # Only validate fields that survived filtering
        ...         has_command = 'command' in filtered
        ...         has_url = 'url' in filtered
        ...         if has_command and has_url:
        ...             raise AdapterValidationError("Cannot have both command and url")
        ...         if not has_command and not has_url:
        ...             raise AdapterValidationError("Must have either command or url")
        ...
        ...     def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        ...         filtered = self.filter_fields(config)
        ...         self.validate_filtered(filtered)
        ...         return filtered  # No transformations needed for Claude
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
    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate ONLY the fields that survived filtering.

        This method validates logical constraints on filtered fields.
        It should NOT check for unsupported fields (already filtered out).

        Validation responsibilities:
        - Transport mutual exclusion (command XOR url, or host-specific rules)
        - Type consistency (e.g., type='stdio' requires command)
        - Business rules (e.g., exactly one transport method)
        - Field value constraints (e.g., non-empty strings)

        What NOT to validate:
        - Presence of unsupported fields (handled by filter_fields)
        - Fields in EXCLUDED_ALWAYS (handled by filter_fields)

        Args:
            filtered: Dictionary of filtered fields (only supported, non-excluded, non-None)

        Raises:
            AdapterValidationError: If validation fails

        Example:
            >>> def validate_filtered(self, filtered: Dict[str, Any]) -> None:
            ...     # Check transport mutual exclusion
            ...     has_command = 'command' in filtered
            ...     has_url = 'url' in filtered
            ...     if has_command and has_url:
            ...         raise AdapterValidationError("Cannot have both command and url")
            ...     if not has_command and not has_url:
            ...         raise AdapterValidationError("Must have either command or url")
        """
        ...

    def apply_transformations(self, filtered: Dict[str, Any]) -> Dict[str, Any]:
        """Apply host-specific field transformations.

        This hook method allows adapters to transform field names or values
        after filtering and validation. The default implementation is a no-op
        (returns filtered unchanged).

        Override this method for hosts that require field mappings, such as:
        - Codex: args → arguments, headers → http_headers
        - Cross-host sync: includeTools → enabled_tools (Gemini to Codex)

        Args:
            filtered: Dictionary of validated, filtered fields

        Returns:
            Transformed dictionary ready for serialization

        Example:
            >>> def apply_transformations(self, filtered: Dict[str, Any]) -> Dict[str, Any]:
            ...     result = filtered.copy()
            ...     if 'args' in result:
            ...         result['arguments'] = result.pop('args')
            ...     return result
        """
        return filtered

    @abstractmethod
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize the configuration for this host.

        This method should convert the MCPServerConfig to the format
        expected by the host's configuration file.

        Standard implementation pattern:
            1. Filter fields: filtered = self.filter_fields(config)
            2. Validate filtered: self.validate_filtered(filtered)
            3. Transform fields: transformed = self.apply_transformations(filtered)
            4. Return transformed

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
