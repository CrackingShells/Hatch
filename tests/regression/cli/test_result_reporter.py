"""Regression tests for Consequence dataclass and ResultReporter class.

This module tests:
- Consequence dataclass invariants and nesting support
- ResultReporter state management and consequence tracking
- ResultReporter mode flags (dry_run, command_name)

Reference: R05 §3.3 (05-test_definition_v0.md) - Nested Consequence Invariants
Reference: R05 §3.2 (05-test_definition_v0.md) - ResultReporter State Management
Reference: R06 §3.3, §3.4 (06-dependency_analysis_v0.md)
"""

import unittest


class TestConsequence(unittest.TestCase):
    """Tests for Consequence dataclass invariants.
    
    Reference: R06 §3.3 - Consequence interface contract
    Reference: R04 §5.1 - Consequence data model invariants
    """

    def test_consequence_dataclass_exists(self):
        """Consequence dataclass should be importable from cli_utils."""
        from hatch.cli.cli_utils import Consequence
        self.assertTrue(hasattr(Consequence, '__dataclass_fields__'))

    def test_consequence_accepts_type_and_message(self):
        """Consequence should accept type and message arguments."""
        from hatch.cli.cli_utils import Consequence, ConsequenceType
        
        c = Consequence(type=ConsequenceType.CREATE, message="Test resource")
        self.assertEqual(c.type, ConsequenceType.CREATE)
        self.assertEqual(c.message, "Test resource")

    def test_consequence_accepts_children_list(self):
        """Consequence should accept children list argument."""
        from hatch.cli.cli_utils import Consequence, ConsequenceType
        
        child1 = Consequence(type=ConsequenceType.UPDATE, message="field1: a → b")
        child2 = Consequence(type=ConsequenceType.SKIP, message="field2: unsupported")
        
        parent = Consequence(
            type=ConsequenceType.CONFIGURE,
            message="Server 'test'",
            children=[child1, child2]
        )
        
        self.assertEqual(len(parent.children), 2)
        self.assertEqual(parent.children[0], child1)
        self.assertEqual(parent.children[1], child2)

    def test_consequence_default_children_is_empty_list(self):
        """Consequence should have empty list as default children."""
        from hatch.cli.cli_utils import Consequence, ConsequenceType
        
        c = Consequence(type=ConsequenceType.CREATE, message="Test")
        self.assertEqual(c.children, [])
        self.assertIsInstance(c.children, list)

    def test_consequence_children_are_consequence_instances(self):
        """Children should be Consequence instances."""
        from hatch.cli.cli_utils import Consequence, ConsequenceType
        
        child = Consequence(type=ConsequenceType.UPDATE, message="child")
        parent = Consequence(
            type=ConsequenceType.CONFIGURE,
            message="parent",
            children=[child]
        )
        
        self.assertIsInstance(parent.children[0], Consequence)

    def test_consequence_children_default_not_shared(self):
        """Each Consequence should have its own children list (no shared mutable default)."""
        from hatch.cli.cli_utils import Consequence, ConsequenceType
        
        c1 = Consequence(type=ConsequenceType.CREATE, message="First")
        c2 = Consequence(type=ConsequenceType.CREATE, message="Second")
        
        # Modify c1's children
        c1.children.append(Consequence(type=ConsequenceType.UPDATE, message="child"))
        
        # c2's children should still be empty
        self.assertEqual(len(c2.children), 0)


class TestResultReporter(unittest.TestCase):
    """Tests for ResultReporter state management.
    
    Reference: R05 §3.2 - ResultReporter State Management test group
    Reference: R06 §3.4 - ResultReporter interface contract
    """

    def test_result_reporter_exists(self):
        """ResultReporter class should be importable from cli_utils."""
        from hatch.cli.cli_utils import ResultReporter
        self.assertTrue(callable(ResultReporter))

    def test_result_reporter_accepts_command_name(self):
        """ResultReporter should accept command_name argument."""
        from hatch.cli.cli_utils import ResultReporter
        
        reporter = ResultReporter(command_name="hatch env create")
        self.assertEqual(reporter.command_name, "hatch env create")

    def test_result_reporter_command_name_stored(self):
        """ResultReporter should store command_name correctly."""
        from hatch.cli.cli_utils import ResultReporter
        
        reporter = ResultReporter("test-cmd")
        self.assertEqual(reporter.command_name, "test-cmd")

    def test_result_reporter_dry_run_default_false(self):
        """ResultReporter dry_run should default to False."""
        from hatch.cli.cli_utils import ResultReporter
        
        reporter = ResultReporter("test")
        self.assertFalse(reporter.dry_run)

    def test_result_reporter_dry_run_stored(self):
        """ResultReporter should store dry_run flag correctly."""
        from hatch.cli.cli_utils import ResultReporter
        
        reporter = ResultReporter("test", dry_run=True)
        self.assertTrue(reporter.dry_run)

    def test_result_reporter_empty_consequences(self):
        """Empty reporter should have empty consequences list."""
        from hatch.cli.cli_utils import ResultReporter
        
        reporter = ResultReporter("test")
        self.assertEqual(reporter.consequences, [])
        self.assertIsInstance(reporter.consequences, list)

    def test_result_reporter_add_consequence(self):
        """ResultReporter.add() should add consequence to list."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        
        reporter = ResultReporter("test")
        reporter.add(ConsequenceType.CREATE, "Environment 'dev'")
        
        self.assertEqual(len(reporter.consequences), 1)

    def test_result_reporter_consequences_tracked_in_order(self):
        """Consequences should be tracked in order of add() calls."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        
        reporter = ResultReporter("test")
        reporter.add(ConsequenceType.CREATE, "First")
        reporter.add(ConsequenceType.REMOVE, "Second")
        reporter.add(ConsequenceType.UPDATE, "Third")
        
        self.assertEqual(len(reporter.consequences), 3)
        self.assertEqual(reporter.consequences[0].message, "First")
        self.assertEqual(reporter.consequences[1].message, "Second")
        self.assertEqual(reporter.consequences[2].message, "Third")

    def test_result_reporter_consequence_data_preserved(self):
        """Consequence type and message should be preserved."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        
        reporter = ResultReporter("test")
        reporter.add(ConsequenceType.CONFIGURE, "Server 'weather'")
        
        c = reporter.consequences[0]
        self.assertEqual(c.type, ConsequenceType.CONFIGURE)
        self.assertEqual(c.message, "Server 'weather'")

    def test_result_reporter_add_with_children(self):
        """ResultReporter.add() should support children argument."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType, Consequence
        
        reporter = ResultReporter("test")
        children = [
            Consequence(type=ConsequenceType.UPDATE, message="field1"),
            Consequence(type=ConsequenceType.SKIP, message="field2"),
        ]
        reporter.add(ConsequenceType.CONFIGURE, "Server", children=children)
        
        self.assertEqual(len(reporter.consequences[0].children), 2)


if __name__ == '__main__':
    unittest.main()


class TestConversionReportIntegration(unittest.TestCase):
    """Tests for ConversionReport → ResultReporter integration.
    
    Reference: R05 §3.5 - ConversionReport Integration test group
    Reference: R06 §3.5 - add_from_conversion_report interface
    Reference: R04 §1.2 - field operation → ConsequenceType mapping
    """

    def test_add_from_conversion_report_method_exists(self):
        """ResultReporter should have add_from_conversion_report method."""
        from hatch.cli.cli_utils import ResultReporter
        
        reporter = ResultReporter("test")
        self.assertTrue(hasattr(reporter, 'add_from_conversion_report'))
        self.assertTrue(callable(reporter.add_from_conversion_report))

    def test_updated_maps_to_update_type(self):
        """FieldOperation 'UPDATED' should map to ConsequenceType.UPDATE."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_SINGLE_UPDATE
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_SINGLE_UPDATE)
        
        # Should have one resource consequence with one child
        self.assertEqual(len(reporter.consequences), 1)
        self.assertEqual(len(reporter.consequences[0].children), 1)
        self.assertEqual(reporter.consequences[0].children[0].type, ConsequenceType.UPDATE)

    def test_unsupported_maps_to_skip_type(self):
        """FieldOperation 'UNSUPPORTED' should map to ConsequenceType.SKIP."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_ALL_UNSUPPORTED
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_ALL_UNSUPPORTED)
        
        # All children should be SKIP type
        for child in reporter.consequences[0].children:
            self.assertEqual(child.type, ConsequenceType.SKIP)

    def test_unchanged_maps_to_unchanged_type(self):
        """FieldOperation 'UNCHANGED' should map to ConsequenceType.UNCHANGED."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_ALL_UNCHANGED
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_ALL_UNCHANGED)
        
        # All children should be UNCHANGED type
        for child in reporter.consequences[0].children:
            self.assertEqual(child.type, ConsequenceType.UNCHANGED)

    def test_field_name_preserved_in_mapping(self):
        """Field name should be preserved in consequence message."""
        from hatch.cli.cli_utils import ResultReporter
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_SINGLE_UPDATE
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_SINGLE_UPDATE)
        
        child_message = reporter.consequences[0].children[0].message
        self.assertIn("command", child_message)

    def test_old_new_values_preserved(self):
        """Old and new values should be preserved in consequence message."""
        from hatch.cli.cli_utils import ResultReporter
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_MIXED_OPERATIONS
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_MIXED_OPERATIONS)
        
        # Find the command field child (first one with UPDATED)
        command_child = reporter.consequences[0].children[0]
        self.assertIn("node", command_child.message)  # old value
        self.assertIn("python", command_child.message)  # new value

    def test_all_fields_mapped_no_data_loss(self):
        """All field operations should be mapped (no data loss)."""
        from hatch.cli.cli_utils import ResultReporter
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_MIXED_OPERATIONS
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_MIXED_OPERATIONS)
        
        # REPORT_MIXED_OPERATIONS has 4 field operations
        self.assertEqual(len(reporter.consequences[0].children), 4)

    def test_empty_conversion_report_handled(self):
        """Empty ConversionReport should not raise exception."""
        from hatch.cli.cli_utils import ResultReporter
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_EMPTY_FIELDS
        
        reporter = ResultReporter("test")
        # Should not raise
        reporter.add_from_conversion_report(REPORT_EMPTY_FIELDS)
        
        # Should have resource consequence with no children
        self.assertEqual(len(reporter.consequences), 1)
        self.assertEqual(len(reporter.consequences[0].children), 0)

    def test_resource_consequence_type_from_operation(self):
        """Resource consequence type should be derived from report.operation."""
        from hatch.cli.cli_utils import ResultReporter, ConsequenceType
        from tests.test_data.fixtures.cli_reporter_fixtures import (
            REPORT_SINGLE_UPDATE,  # operation="create"
            REPORT_MIXED_OPERATIONS,  # operation="update"
        )
        
        reporter1 = ResultReporter("test")
        reporter1.add_from_conversion_report(REPORT_SINGLE_UPDATE)
        # "create" operation should map to CONFIGURE (for MCP server creation)
        self.assertIn(
            reporter1.consequences[0].type,
            [ConsequenceType.CONFIGURE, ConsequenceType.CREATE]
        )
        
        reporter2 = ResultReporter("test")
        reporter2.add_from_conversion_report(REPORT_MIXED_OPERATIONS)
        # "update" operation should map to CONFIGURE or UPDATE
        self.assertIn(
            reporter2.consequences[0].type,
            [ConsequenceType.CONFIGURE, ConsequenceType.UPDATE]
        )

    def test_server_name_in_resource_message(self):
        """Server name should appear in resource consequence message."""
        from hatch.cli.cli_utils import ResultReporter
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_MIXED_OPERATIONS
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_MIXED_OPERATIONS)
        
        self.assertIn("weather-server", reporter.consequences[0].message)

    def test_target_host_in_resource_message(self):
        """Target host should appear in resource consequence message."""
        from hatch.cli.cli_utils import ResultReporter
        from tests.test_data.fixtures.cli_reporter_fixtures import REPORT_MIXED_OPERATIONS
        
        reporter = ResultReporter("test")
        reporter.add_from_conversion_report(REPORT_MIXED_OPERATIONS)
        
        self.assertIn("cursor", reporter.consequences[0].message.lower())
