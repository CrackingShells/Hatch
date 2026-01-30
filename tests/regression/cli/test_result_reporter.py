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
