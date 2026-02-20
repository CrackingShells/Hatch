"""
User feedback reporting system for MCP configuration operations.

This module provides models and functions for generating and displaying
user-friendly reports about MCP configuration changes, including field-level
operations and conversion summaries.
"""

from typing import Literal, Optional, Any, List
from pydantic import BaseModel, ConfigDict

from .models import MCPServerConfig, MCPHostType
from .adapters import get_adapter


class FieldOperation(BaseModel):
    """Single field operation in a conversion.

    Represents a single field-level change during MCP configuration conversion,
    including the operation type (UPDATED, UNSUPPORTED, UNCHANGED) and values.
    """

    field_name: str
    operation: Literal["UPDATED", "UNSUPPORTED", "UNCHANGED"]
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    def __str__(self) -> str:
        """Return formatted string representation for console output.

        Uses ASCII arrow (-->) for terminal compatibility instead of Unicode.
        """
        if self.operation == "UPDATED":
            return f"{self.field_name}: UPDATED {repr(self.old_value)} --> {repr(self.new_value)}"
        elif self.operation == "UNSUPPORTED":
            return f"{self.field_name}: UNSUPPORTED"
        elif self.operation == "UNCHANGED":
            return f"{self.field_name}: UNCHANGED {repr(self.new_value)}"
        return f"{self.field_name}: {self.operation}"


class ConversionReport(BaseModel):
    """Complete conversion report for a configuration operation.

    Contains metadata about the operation (create, update, delete, migrate)
    and a list of field-level operations that occurred during conversion.
    """

    model_config = ConfigDict(validate_assignment=False)

    operation: Literal["create", "update", "delete", "migrate"]
    server_name: str
    source_host: Optional[MCPHostType] = None
    target_host: MCPHostType
    success: bool = True
    error_message: Optional[str] = None
    field_operations: List[FieldOperation] = []
    dry_run: bool = False


def _get_adapter_host_name(host_type: MCPHostType) -> str:
    """Map MCPHostType to adapter host name.

    Claude has two variants (desktop/code) sharing the same adapter,
    so we need explicit mapping.
    """
    mapping = {
        MCPHostType.CLAUDE_DESKTOP: "claude-desktop",
        MCPHostType.CLAUDE_CODE: "claude-code",
        MCPHostType.VSCODE: "vscode",
        MCPHostType.CURSOR: "cursor",
        MCPHostType.LMSTUDIO: "lmstudio",
        MCPHostType.GEMINI: "gemini",
        MCPHostType.KIRO: "kiro",
        MCPHostType.CODEX: "codex",
    }
    return mapping.get(host_type, host_type.value)


def generate_conversion_report(
    operation: Literal["create", "update", "delete", "migrate"],
    server_name: str,
    target_host: MCPHostType,
    config: MCPServerConfig,
    source_host: Optional[MCPHostType] = None,
    old_config: Optional[MCPServerConfig] = None,
    dry_run: bool = False,
) -> ConversionReport:
    """Generate conversion report for a configuration operation.

    Analyzes the configuration against the target host's adapter,
    identifying which fields were updated, which are unsupported, and which
    remained unchanged.

    Fields in the adapter's excluded set (e.g., 'name' from EXCLUDED_ALWAYS)
    are internal metadata and are completely omitted from field operations.
    They will not appear as UPDATED, UNCHANGED, or UNSUPPORTED.

    Args:
        operation: Type of operation being performed
        server_name: Name of the server being configured
        target_host: Target host for the configuration (MCPHostType enum)
        config: New/updated configuration (unified MCPServerConfig)
        source_host: Source host (for migrate operation, MCPHostType enum)
        old_config: Existing configuration (for update operation)
        dry_run: Whether this is a dry-run preview

    Returns:
        ConversionReport with field-level operations
    """
    # Get supported and excluded fields from adapter
    adapter_host_name = _get_adapter_host_name(target_host)
    adapter = get_adapter(adapter_host_name)
    supported_fields = adapter.get_supported_fields()
    excluded_fields = adapter.get_excluded_fields()

    field_operations = []
    set_fields = config.model_dump(exclude_unset=True)

    for field_name, new_value in set_fields.items():
        # Skip metadata fields (e.g., 'name') - they should never appear in reports
        if field_name in excluded_fields:
            continue

        if field_name in supported_fields:
            # Field is supported by target host
            if old_config:
                # Update operation - check if field changed
                old_fields = old_config.model_dump(exclude_unset=True)
                if field_name in old_fields:
                    old_value = old_fields[field_name]
                    if old_value != new_value:
                        # Field was modified
                        field_operations.append(
                            FieldOperation(
                                field_name=field_name,
                                operation="UPDATED",
                                old_value=old_value,
                                new_value=new_value,
                            )
                        )
                    else:
                        # Field unchanged
                        field_operations.append(
                            FieldOperation(
                                field_name=field_name,
                                operation="UNCHANGED",
                                new_value=new_value,
                            )
                        )
                else:
                    # Field was added
                    field_operations.append(
                        FieldOperation(
                            field_name=field_name,
                            operation="UPDATED",
                            old_value=None,
                            new_value=new_value,
                        )
                    )
            else:
                # Create operation - all fields are new
                field_operations.append(
                    FieldOperation(
                        field_name=field_name,
                        operation="UPDATED",
                        old_value=None,
                        new_value=new_value,
                    )
                )
        else:
            # Field is not supported by target host
            field_operations.append(
                FieldOperation(
                    field_name=field_name, operation="UNSUPPORTED", new_value=new_value
                )
            )

    return ConversionReport(
        operation=operation,
        server_name=server_name,
        source_host=source_host,
        target_host=target_host,
        field_operations=field_operations,
        dry_run=dry_run,
    )


def display_report(report: ConversionReport) -> None:
    """Display conversion report to console.

    .. deprecated::
        Use ``ResultReporter.add_from_conversion_report()`` instead.
        This function will be removed in a future version.

    Prints a formatted report showing the operation performed and all
    field-level changes. Uses FieldOperation.__str__() for consistent
    formatting.

    Args:
        report: ConversionReport to display
    """
    import warnings

    warnings.warn(
        "display_report() is deprecated. Use ResultReporter.add_from_conversion_report() instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Header
    if report.dry_run:
        print(f"[DRY RUN] Preview of changes for server '{report.server_name}':")
    else:
        if report.operation == "create":
            print(
                f"Server '{report.server_name}' created for host '{report.target_host.value}':"
            )
        elif report.operation == "update":
            print(
                f"Server '{report.server_name}' updated for host '{report.target_host.value}':"
            )
        elif report.operation == "migrate":
            print(
                f"Server '{report.server_name}' migrated from '{report.source_host.value}' to '{report.target_host.value}':"
            )
        elif report.operation == "delete":
            print(
                f"Server '{report.server_name}' deleted from host '{report.target_host.value}':"
            )

    # Field operations
    for field_op in report.field_operations:
        print(f"  {field_op}")

    # Footer
    if report.dry_run:
        print("\nNo changes were made.")
