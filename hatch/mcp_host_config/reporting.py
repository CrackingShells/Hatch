"""
User feedback reporting system for MCP configuration operations.

This module provides models and functions for generating and displaying
user-friendly reports about MCP configuration changes, including field-level
operations and conversion summaries.
"""

from typing import Literal, Optional, Any, List
from pydantic import BaseModel, ConfigDict

from .models import MCPServerConfigOmni, MCPHostType, HOST_MODEL_REGISTRY


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


def generate_conversion_report(
    operation: Literal["create", "update", "delete", "migrate"],
    server_name: str,
    target_host: MCPHostType,
    omni: MCPServerConfigOmni,
    source_host: Optional[MCPHostType] = None,
    old_config: Optional[MCPServerConfigOmni] = None,
    dry_run: bool = False
) -> ConversionReport:
    """Generate conversion report for a configuration operation.
    
    Analyzes the conversion from Omni model to host-specific configuration,
    identifying which fields were updated, which are unsupported, and which
    remained unchanged.
    
    Args:
        operation: Type of operation being performed
        server_name: Name of the server being configured
        target_host: Target host for the configuration (MCPHostType enum)
        omni: New/updated configuration (Omni model)
        source_host: Source host (for migrate operation, MCPHostType enum)
        old_config: Existing configuration (for update operation)
        dry_run: Whether this is a dry-run preview
    
    Returns:
        ConversionReport with field-level operations
    """
    # Derive supported fields dynamically from model class
    model_class = HOST_MODEL_REGISTRY[target_host]
    supported_fields = set(model_class.model_fields.keys())
    
    field_operations = []
    set_fields = omni.model_dump(exclude_unset=True)
    
    for field_name, new_value in set_fields.items():
        if field_name in supported_fields:
            # Field is supported by target host
            if old_config:
                # Update operation - check if field changed
                old_fields = old_config.model_dump(exclude_unset=True)
                if field_name in old_fields:
                    old_value = old_fields[field_name]
                    if old_value != new_value:
                        # Field was modified
                        field_operations.append(FieldOperation(
                            field_name=field_name,
                            operation="UPDATED",
                            old_value=old_value,
                            new_value=new_value
                        ))
                    else:
                        # Field unchanged
                        field_operations.append(FieldOperation(
                            field_name=field_name,
                            operation="UNCHANGED",
                            new_value=new_value
                        ))
                else:
                    # Field was added
                    field_operations.append(FieldOperation(
                        field_name=field_name,
                        operation="UPDATED",
                        old_value=None,
                        new_value=new_value
                    ))
            else:
                # Create operation - all fields are new
                field_operations.append(FieldOperation(
                    field_name=field_name,
                    operation="UPDATED",
                    old_value=None,
                    new_value=new_value
                ))
        else:
            # Field is not supported by target host
            field_operations.append(FieldOperation(
                field_name=field_name,
                operation="UNSUPPORTED",
                new_value=new_value
            ))
    
    return ConversionReport(
        operation=operation,
        server_name=server_name,
        source_host=source_host,
        target_host=target_host,
        field_operations=field_operations,
        dry_run=dry_run
    )


def display_report(report: ConversionReport) -> None:
    """Display conversion report to console.
    
    Prints a formatted report showing the operation performed and all
    field-level changes. Uses FieldOperation.__str__() for consistent
    formatting.
    
    Args:
        report: ConversionReport to display
    """
    # Header
    if report.dry_run:
        print(f"[DRY RUN] Preview of changes for server '{report.server_name}':")
    else:
        if report.operation == "create":
            print(f"Server '{report.server_name}' created for host '{report.target_host.value}':")
        elif report.operation == "update":
            print(f"Server '{report.server_name}' updated for host '{report.target_host.value}':")
        elif report.operation == "migrate":
            print(f"Server '{report.server_name}' migrated from '{report.source_host.value}' to '{report.target_host.value}':")
        elif report.operation == "delete":
            print(f"Server '{report.server_name}' deleted from host '{report.target_host.value}':")
    
    # Field operations
    for field_op in report.field_operations:
        print(f"  {field_op}")
    
    # Footer
    if report.dry_run:
        print("\nNo changes were made.")

