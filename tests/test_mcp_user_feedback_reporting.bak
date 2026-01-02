"""
Test suite for MCP user feedback reporting system.

This module tests the FieldOperation and ConversionReport models,
generate_conversion_report() function, and display_report() function.
"""

import unittest
import sys
from pathlib import Path
from io import StringIO

# Add the parent directory to the path to import wobble
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wobble.decorators import regression_test
except ImportError:
    # Fallback decorator if wobble is not available
    def regression_test(func):
        return func

from hatch.mcp_host_config.reporting import (
    FieldOperation,
    ConversionReport,
    generate_conversion_report,
    display_report
)
from hatch.mcp_host_config.models import (
    MCPServerConfigOmni,
    MCPHostType
)


class TestFieldOperation(unittest.TestCase):
    """Test suite for FieldOperation model."""
    
    @regression_test
    def test_field_operation_updated_str_representation(self):
        """Test UPDATED operation string representation."""
        field_op = FieldOperation(
            field_name="command",
            operation="UPDATED",
            old_value="old_command",
            new_value="new_command"
        )
        
        result = str(field_op)
        
        # Verify ASCII arrow used (not Unicode)
        self.assertIn("-->", result)
        self.assertNotIn("→", result)
        
        # Verify format
        self.assertEqual(result, "command: UPDATED 'old_command' --> 'new_command'")
    
    @regression_test
    def test_field_operation_updated_with_none_old_value(self):
        """Test UPDATED operation with None old_value (field added)."""
        field_op = FieldOperation(
            field_name="timeout",
            operation="UPDATED",
            old_value=None,
            new_value=30000
        )
        
        result = str(field_op)
        
        # Verify None is displayed
        self.assertEqual(result, "timeout: UPDATED None --> 30000")
    
    @regression_test
    def test_field_operation_unsupported_str_representation(self):
        """Test UNSUPPORTED operation string representation."""
        field_op = FieldOperation(
            field_name="envFile",
            operation="UNSUPPORTED",
            new_value=".env"
        )
        
        result = str(field_op)
        
        # Verify format
        self.assertEqual(result, "envFile: UNSUPPORTED")
    
    @regression_test
    def test_field_operation_unchanged_str_representation(self):
        """Test UNCHANGED operation string representation."""
        field_op = FieldOperation(
            field_name="name",
            operation="UNCHANGED",
            new_value="my-server"
        )
        
        result = str(field_op)
        
        # Verify format
        self.assertEqual(result, "name: UNCHANGED 'my-server'")


class TestConversionReport(unittest.TestCase):
    """Test suite for ConversionReport model."""
    
    @regression_test
    def test_conversion_report_create_operation(self):
        """Test ConversionReport with create operation."""
        report = ConversionReport(
            operation="create",
            server_name="my-server",
            target_host=MCPHostType.GEMINI,
            field_operations=[
                FieldOperation(field_name="command", operation="UPDATED", old_value=None, new_value="python")
            ]
        )
        
        self.assertEqual(report.operation, "create")
        self.assertEqual(report.server_name, "my-server")
        self.assertEqual(report.target_host, MCPHostType.GEMINI)
        self.assertTrue(report.success)
        self.assertIsNone(report.error_message)
        self.assertEqual(len(report.field_operations), 1)
        self.assertFalse(report.dry_run)
    
    @regression_test
    def test_conversion_report_update_operation(self):
        """Test ConversionReport with update operation."""
        report = ConversionReport(
            operation="update",
            server_name="my-server",
            target_host=MCPHostType.VSCODE,
            field_operations=[
                FieldOperation(field_name="command", operation="UPDATED", old_value="old", new_value="new"),
                FieldOperation(field_name="name", operation="UNCHANGED", new_value="my-server")
            ]
        )
        
        self.assertEqual(report.operation, "update")
        self.assertEqual(len(report.field_operations), 2)
    
    @regression_test
    def test_conversion_report_migrate_operation(self):
        """Test ConversionReport with migrate operation."""
        report = ConversionReport(
            operation="migrate",
            server_name="my-server",
            source_host=MCPHostType.GEMINI,
            target_host=MCPHostType.VSCODE,
            field_operations=[]
        )
        
        self.assertEqual(report.operation, "migrate")
        self.assertEqual(report.source_host, MCPHostType.GEMINI)
        self.assertEqual(report.target_host, MCPHostType.VSCODE)


class TestGenerateConversionReport(unittest.TestCase):
    """Test suite for generate_conversion_report() function."""
    
    @regression_test
    def test_generate_report_create_operation_all_supported(self):
        """Test generate_conversion_report for create with all supported fields."""
        omni = MCPServerConfigOmni(
            name="gemini-server",
            command="npx",
            args=["-y", "server"],
            cwd="/path/to/dir",
            timeout=30000
        )
        
        report = generate_conversion_report(
            operation="create",
            server_name="gemini-server",
            target_host=MCPHostType.GEMINI,
            omni=omni
        )
        
        # Verify all fields are UPDATED (create operation)
        self.assertEqual(report.operation, "create")
        self.assertEqual(report.server_name, "gemini-server")
        self.assertEqual(report.target_host, MCPHostType.GEMINI)
        
        # All set fields should be UPDATED
        updated_ops = [op for op in report.field_operations if op.operation == "UPDATED"]
        self.assertEqual(len(updated_ops), 5)  # name, command, args, cwd, timeout
        
        # No unsupported fields
        unsupported_ops = [op for op in report.field_operations if op.operation == "UNSUPPORTED"]
        self.assertEqual(len(unsupported_ops), 0)
    
    @regression_test
    def test_generate_report_create_operation_with_unsupported(self):
        """Test generate_conversion_report with unsupported fields."""
        omni = MCPServerConfigOmni(
            name="gemini-server",
            command="python",
            cwd="/path/to/dir",  # Gemini field
            envFile=".env"  # VS Code field (unsupported by Gemini)
        )
        
        report = generate_conversion_report(
            operation="create",
            server_name="gemini-server",
            target_host=MCPHostType.GEMINI,
            omni=omni
        )
        
        # Verify Gemini fields are UPDATED
        updated_ops = [op for op in report.field_operations if op.operation == "UPDATED"]
        updated_fields = {op.field_name for op in updated_ops}
        self.assertIn("name", updated_fields)
        self.assertIn("command", updated_fields)
        self.assertIn("cwd", updated_fields)
        
        # Verify VS Code field is UNSUPPORTED
        unsupported_ops = [op for op in report.field_operations if op.operation == "UNSUPPORTED"]
        self.assertEqual(len(unsupported_ops), 1)
        self.assertEqual(unsupported_ops[0].field_name, "envFile")
    
    @regression_test
    def test_generate_report_update_operation(self):
        """Test generate_conversion_report for update operation."""
        old_config = MCPServerConfigOmni(
            name="my-server",
            command="python",
            args=["old.py"]
        )
        
        new_omni = MCPServerConfigOmni(
            name="my-server",
            command="python",
            args=["new.py"]
        )
        
        report = generate_conversion_report(
            operation="update",
            server_name="my-server",
            target_host=MCPHostType.GEMINI,
            omni=new_omni,
            old_config=old_config
        )
        
        # Verify name and command are UNCHANGED
        unchanged_ops = [op for op in report.field_operations if op.operation == "UNCHANGED"]
        unchanged_fields = {op.field_name for op in unchanged_ops}
        self.assertIn("name", unchanged_fields)
        self.assertIn("command", unchanged_fields)
        
        # Verify args is UPDATED
        updated_ops = [op for op in report.field_operations if op.operation == "UPDATED"]
        self.assertEqual(len(updated_ops), 1)
        self.assertEqual(updated_ops[0].field_name, "args")
        self.assertEqual(updated_ops[0].old_value, ["old.py"])
        self.assertEqual(updated_ops[0].new_value, ["new.py"])
    
    @regression_test
    def test_generate_report_dynamic_field_derivation(self):
        """Test that generate_conversion_report uses dynamic field derivation."""
        omni = MCPServerConfigOmni(
            name="test-server",
            command="python"
        )
        
        # Generate report for Gemini
        report_gemini = generate_conversion_report(
            operation="create",
            server_name="test-server",
            target_host=MCPHostType.GEMINI,
            omni=omni
        )
        
        # All fields should be UPDATED (no unsupported)
        unsupported_ops = [op for op in report_gemini.field_operations if op.operation == "UNSUPPORTED"]
        self.assertEqual(len(unsupported_ops), 0)


class TestDisplayReport(unittest.TestCase):
    """Test suite for display_report() function."""
    
    @regression_test
    def test_display_report_create_operation(self):
        """Test display_report for create operation."""
        report = ConversionReport(
            operation="create",
            server_name="my-server",
            target_host=MCPHostType.GEMINI,
            field_operations=[
                FieldOperation(field_name="command", operation="UPDATED", old_value=None, new_value="python")
            ]
        )
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        display_report(report)
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # Verify header
        self.assertIn("Server 'my-server' created for host", output)
        self.assertIn("gemini", output.lower())
        
        # Verify field operation displayed
        self.assertIn("command: UPDATED", output)
    
    @regression_test
    def test_display_report_update_operation(self):
        """Test display_report for update operation."""
        report = ConversionReport(
            operation="update",
            server_name="my-server",
            target_host=MCPHostType.VSCODE,
            field_operations=[
                FieldOperation(field_name="args", operation="UPDATED", old_value=["old.py"], new_value=["new.py"])
            ]
        )
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        display_report(report)
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # Verify header
        self.assertIn("Server 'my-server' updated for host", output)
    
    @regression_test
    def test_display_report_dry_run(self):
        """Test display_report for dry-run mode."""
        report = ConversionReport(
            operation="create",
            server_name="my-server",
            target_host=MCPHostType.GEMINI,
            field_operations=[],
            dry_run=True
        )
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        display_report(report)
        
        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()
        
        # Verify dry-run header and footer
        self.assertIn("[DRY RUN]", output)
        self.assertIn("Preview of changes", output)
        self.assertIn("No changes were made", output)


if __name__ == '__main__':
    unittest.main()

