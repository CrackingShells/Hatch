"""Test fixtures for ResultReporter and ConversionReport integration tests.

This module provides reusable ConversionReport and FieldOperation samples
for testing the CLI reporter infrastructure. Fixtures are defined as Python
objects for type safety and IDE support.

Reference: R05 §4.2 (05-test_definition_v0.md)

Fixture Categories:
    - Single field operation samples (one per operation type)
    - ConversionReport samples (various scenarios)

Usage:
    from tests.test_data.fixtures.cli_reporter_fixtures import (
        REPORT_MIXED_OPERATIONS,
        FIELD_OP_UPDATED,
    )

    def test_all_fields_mapped_no_data_loss(self):
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_MIXED_OPERATIONS)
        assert len(reporter.consequences[0].children) == 4
"""

from hatch.mcp_host_config.reporting import ConversionReport, FieldOperation
from hatch.mcp_host_config.models import MCPHostType

# =============================================================================
# Single Field Operation Samples (one per operation type)
# =============================================================================

FIELD_OP_UPDATED = FieldOperation(
    field_name="command", operation="UPDATED", old_value=None, new_value="python"
)
"""Field operation: UPDATED - field value changed from None to 'python'."""

FIELD_OP_UPDATED_WITH_OLD = FieldOperation(
    field_name="command", operation="UPDATED", old_value="node", new_value="python"
)
"""Field operation: UPDATED - field value changed from 'node' to 'python'."""

FIELD_OP_UNSUPPORTED = FieldOperation(
    field_name="timeout", operation="UNSUPPORTED", new_value=30
)
"""Field operation: UNSUPPORTED - field not supported by target host."""

FIELD_OP_UNCHANGED = FieldOperation(
    field_name="env", operation="UNCHANGED", new_value={}
)
"""Field operation: UNCHANGED - field value remained the same."""


# =============================================================================
# ConversionReport Samples
# =============================================================================

REPORT_SINGLE_UPDATE = ConversionReport(
    operation="create",
    server_name="test-server",
    target_host=MCPHostType.CLAUDE_DESKTOP,
    field_operations=[FIELD_OP_UPDATED],
)
"""ConversionReport: Single field update (create operation)."""

REPORT_MIXED_OPERATIONS = ConversionReport(
    operation="update",
    server_name="weather-server",
    target_host=MCPHostType.CURSOR,
    field_operations=[
        FieldOperation(
            field_name="command",
            operation="UPDATED",
            old_value="node",
            new_value="python",
        ),
        FieldOperation(
            field_name="args",
            operation="UPDATED",
            old_value=[],
            new_value=["server.py"],
        ),
        FieldOperation(
            field_name="env", operation="UNCHANGED", new_value={"API_KEY": "***"}
        ),
        FieldOperation(field_name="timeout", operation="UNSUPPORTED", new_value=60),
    ],
)
"""ConversionReport: Mixed field operations (update operation).

Contains:
- 2 UPDATED fields (command, args)
- 1 UNCHANGED field (env)
- 1 UNSUPPORTED field (timeout)
"""

REPORT_EMPTY_FIELDS = ConversionReport(
    operation="create",
    server_name="minimal-server",
    target_host=MCPHostType.VSCODE,
    field_operations=[],
)
"""ConversionReport: Empty field operations list (edge case)."""

REPORT_ALL_UNSUPPORTED = ConversionReport(
    operation="migrate",
    server_name="legacy-server",
    source_host=MCPHostType.CLAUDE_DESKTOP,
    target_host=MCPHostType.KIRO,
    field_operations=[
        FieldOperation(field_name="trust", operation="UNSUPPORTED", new_value=True),
        FieldOperation(field_name="cwd", operation="UNSUPPORTED", new_value="/app"),
    ],
)
"""ConversionReport: All fields unsupported (migrate operation)."""

REPORT_ALL_UNCHANGED = ConversionReport(
    operation="update",
    server_name="stable-server",
    target_host=MCPHostType.CLAUDE_DESKTOP,
    field_operations=[
        FieldOperation(field_name="command", operation="UNCHANGED", new_value="python"),
        FieldOperation(
            field_name="args", operation="UNCHANGED", new_value=["server.py"]
        ),
    ],
)
"""ConversionReport: All fields unchanged (no-op update)."""

REPORT_DRY_RUN = ConversionReport(
    operation="create",
    server_name="preview-server",
    target_host=MCPHostType.CURSOR,
    field_operations=[
        FieldOperation(
            field_name="command",
            operation="UPDATED",
            old_value=None,
            new_value="python",
        ),
    ],
    dry_run=True,
)
"""ConversionReport: Dry-run mode enabled."""

REPORT_WITH_ERROR = ConversionReport(
    operation="create",
    server_name="failed-server",
    target_host=MCPHostType.VSCODE,
    success=False,
    error_message="Configuration file not found",
    field_operations=[],
)
"""ConversionReport: Failed operation with error message."""
