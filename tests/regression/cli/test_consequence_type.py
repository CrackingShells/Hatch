"""Regression tests for ConsequenceType enum.

This module tests:
- ConsequenceType enum completeness (all 16 types defined)
- Tense-aware label properties (prompt_label, result_label)
- Color properties (prompt_color, result_color)
- Irregular verb handling (SET, EXISTS, UNCHANGED)

Reference: R05 §3.2 (05-test_definition_v0.md)
Reference: R06 §3.2 (06-dependency_analysis_v0.md)
Reference: R03 §2 (03-mutation_output_specification_v0.md)
"""

import unittest


class TestConsequenceTypeEnum(unittest.TestCase):
    """Tests for ConsequenceType enum completeness and structure.
    
    Reference: R06 §3.2 - ConsequenceType interface contract
    """

    def test_consequence_type_enum_exists(self):
        """ConsequenceType enum should be importable from cli_utils."""
        from hatch.cli.cli_utils import ConsequenceType
        self.assertTrue(hasattr(ConsequenceType, '__members__'))

    def test_consequence_type_has_all_constructive_types(self):
        """ConsequenceType should have all constructive action types (Green)."""
        from hatch.cli.cli_utils import ConsequenceType
        
        constructive_types = ['CREATE', 'ADD', 'CONFIGURE', 'INSTALL', 'INITIALIZE']
        for type_name in constructive_types:
            self.assertTrue(
                hasattr(ConsequenceType, type_name),
                f"ConsequenceType missing constructive type: {type_name}"
            )

    def test_consequence_type_has_recovery_type(self):
        """ConsequenceType should have RESTORE recovery type (Blue)."""
        from hatch.cli.cli_utils import ConsequenceType
        self.assertTrue(hasattr(ConsequenceType, 'RESTORE'))

    def test_consequence_type_has_all_destructive_types(self):
        """ConsequenceType should have all destructive action types (Red)."""
        from hatch.cli.cli_utils import ConsequenceType
        
        destructive_types = ['REMOVE', 'DELETE', 'CLEAN']
        for type_name in destructive_types:
            self.assertTrue(
                hasattr(ConsequenceType, type_name),
                f"ConsequenceType missing destructive type: {type_name}"
            )

    def test_consequence_type_has_all_modification_types(self):
        """ConsequenceType should have all modification action types (Yellow)."""
        from hatch.cli.cli_utils import ConsequenceType
        
        modification_types = ['SET', 'UPDATE']
        for type_name in modification_types:
            self.assertTrue(
                hasattr(ConsequenceType, type_name),
                f"ConsequenceType missing modification type: {type_name}"
            )

    def test_consequence_type_has_transfer_type(self):
        """ConsequenceType should have SYNC transfer type (Magenta)."""
        from hatch.cli.cli_utils import ConsequenceType
        self.assertTrue(hasattr(ConsequenceType, 'SYNC'))

    def test_consequence_type_has_informational_type(self):
        """ConsequenceType should have VALIDATE informational type (Cyan)."""
        from hatch.cli.cli_utils import ConsequenceType
        self.assertTrue(hasattr(ConsequenceType, 'VALIDATE'))

    def test_consequence_type_has_all_noop_types(self):
        """ConsequenceType should have all no-op action types (Gray)."""
        from hatch.cli.cli_utils import ConsequenceType
        
        noop_types = ['SKIP', 'EXISTS', 'UNCHANGED']
        for type_name in noop_types:
            self.assertTrue(
                hasattr(ConsequenceType, type_name),
                f"ConsequenceType missing no-op type: {type_name}"
            )

    def test_consequence_type_total_count(self):
        """ConsequenceType should have exactly 16 members."""
        from hatch.cli.cli_utils import ConsequenceType
        
        # 5 constructive + 1 recovery + 3 destructive + 2 modification + 
        # 1 transfer + 1 informational + 3 noop = 16
        self.assertEqual(
            len(ConsequenceType), 16,
            f"Expected 16 consequence types, got {len(ConsequenceType)}"
        )


class TestConsequenceTypeProperties(unittest.TestCase):
    """Tests for ConsequenceType tense-aware properties.
    
    Reference: R05 §3.2 - ConsequenceType Behavior test group
    """

    def test_all_types_have_prompt_label(self):
        """All ConsequenceType members should have prompt_label property."""
        from hatch.cli.cli_utils import ConsequenceType
        
        for ct in ConsequenceType:
            self.assertTrue(
                hasattr(ct, 'prompt_label'),
                f"{ct.name} missing prompt_label property"
            )
            self.assertIsInstance(ct.prompt_label, str)
            self.assertTrue(
                len(ct.prompt_label) > 0,
                f"{ct.name}.prompt_label should not be empty"
            )

    def test_all_types_have_result_label(self):
        """All ConsequenceType members should have result_label property."""
        from hatch.cli.cli_utils import ConsequenceType
        
        for ct in ConsequenceType:
            self.assertTrue(
                hasattr(ct, 'result_label'),
                f"{ct.name} missing result_label property"
            )
            self.assertIsInstance(ct.result_label, str)
            self.assertTrue(
                len(ct.result_label) > 0,
                f"{ct.name}.result_label should not be empty"
            )

    def test_all_types_have_prompt_color(self):
        """All ConsequenceType members should have prompt_color property."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        for ct in ConsequenceType:
            self.assertTrue(
                hasattr(ct, 'prompt_color'),
                f"{ct.name} missing prompt_color property"
            )
            self.assertIsInstance(ct.prompt_color, Color)

    def test_all_types_have_result_color(self):
        """All ConsequenceType members should have result_color property."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        for ct in ConsequenceType:
            self.assertTrue(
                hasattr(ct, 'result_color'),
                f"{ct.name} missing result_color property"
            )
            self.assertIsInstance(ct.result_color, Color)

    def test_irregular_verbs_prompt_equals_result(self):
        """Irregular verbs (SET, EXISTS, UNCHANGED) should have same prompt and result labels."""
        from hatch.cli.cli_utils import ConsequenceType
        
        irregular_verbs = [
            ConsequenceType.SET,
            ConsequenceType.EXISTS,
            ConsequenceType.UNCHANGED,
        ]
        
        for ct in irregular_verbs:
            self.assertEqual(
                ct.prompt_label, ct.result_label,
                f"{ct.name} is irregular: prompt_label should equal result_label"
            )

    def test_regular_verbs_result_ends_with_ed(self):
        """Regular verbs should have result_label ending with 'ED'."""
        from hatch.cli.cli_utils import ConsequenceType
        
        # Irregular verbs that don't follow -ED pattern
        irregular = {'SET', 'EXISTS', 'UNCHANGED'}
        
        for ct in ConsequenceType:
            if ct.name not in irregular:
                self.assertTrue(
                    ct.result_label.endswith('ED'),
                    f"{ct.name}.result_label '{ct.result_label}' should end with 'ED'"
                )


class TestConsequenceTypeColorSemantics(unittest.TestCase):
    """Tests for ConsequenceType color semantic correctness.
    
    Reference: R03 §4.3 - Verb-to-Color mapping
    """

    def test_constructive_types_use_green(self):
        """Constructive types should use green colors."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        constructive = [
            ConsequenceType.CREATE,
            ConsequenceType.ADD,
            ConsequenceType.CONFIGURE,
            ConsequenceType.INSTALL,
            ConsequenceType.INITIALIZE,
        ]
        
        for ct in constructive:
            self.assertEqual(
                ct.prompt_color, Color.GREEN_DIM,
                f"{ct.name} prompt_color should be GREEN_DIM"
            )
            self.assertEqual(
                ct.result_color, Color.GREEN,
                f"{ct.name} result_color should be GREEN"
            )

    def test_recovery_type_uses_blue(self):
        """RESTORE should use blue colors."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        self.assertEqual(ConsequenceType.RESTORE.prompt_color, Color.BLUE_DIM)
        self.assertEqual(ConsequenceType.RESTORE.result_color, Color.BLUE)

    def test_destructive_types_use_red(self):
        """Destructive types should use red colors."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        destructive = [
            ConsequenceType.REMOVE,
            ConsequenceType.DELETE,
            ConsequenceType.CLEAN,
        ]
        
        for ct in destructive:
            self.assertEqual(
                ct.prompt_color, Color.RED_DIM,
                f"{ct.name} prompt_color should be RED_DIM"
            )
            self.assertEqual(
                ct.result_color, Color.RED,
                f"{ct.name} result_color should be RED"
            )

    def test_modification_types_use_yellow(self):
        """Modification types should use yellow colors."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        modification = [
            ConsequenceType.SET,
            ConsequenceType.UPDATE,
        ]
        
        for ct in modification:
            self.assertEqual(
                ct.prompt_color, Color.YELLOW_DIM,
                f"{ct.name} prompt_color should be YELLOW_DIM"
            )
            self.assertEqual(
                ct.result_color, Color.YELLOW,
                f"{ct.name} result_color should be YELLOW"
            )

    def test_transfer_type_uses_magenta(self):
        """SYNC should use magenta colors."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        self.assertEqual(ConsequenceType.SYNC.prompt_color, Color.MAGENTA_DIM)
        self.assertEqual(ConsequenceType.SYNC.result_color, Color.MAGENTA)

    def test_informational_type_uses_cyan(self):
        """VALIDATE should use cyan colors."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        self.assertEqual(ConsequenceType.VALIDATE.prompt_color, Color.CYAN_DIM)
        self.assertEqual(ConsequenceType.VALIDATE.result_color, Color.CYAN)

    def test_noop_types_use_gray(self):
        """No-op types should use gray colors (same for prompt and result)."""
        from hatch.cli.cli_utils import ConsequenceType, Color
        
        noop = [
            ConsequenceType.SKIP,
            ConsequenceType.EXISTS,
            ConsequenceType.UNCHANGED,
        ]
        
        for ct in noop:
            self.assertEqual(
                ct.prompt_color, Color.GRAY,
                f"{ct.name} prompt_color should be GRAY"
            )
            self.assertEqual(
                ct.result_color, Color.GRAY,
                f"{ct.name} result_color should be GRAY"
            )


if __name__ == '__main__':
    unittest.main()
