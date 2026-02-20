"""Regression tests for CLI reporter infrastructure.

This package contains regression tests for the CLI UX normalization components:
- ResultReporter state management and data integrity
- ConsequenceType enum contracts
- Color enable/disable logic
- Consequence dataclass invariants

These tests focus on behavioral contracts rather than output format strings,
ensuring the infrastructure works correctly regardless of UX iteration.

Test Groups:
    test_result_reporter.py: ResultReporter state management, Consequence nesting
    test_consequence_type.py: ConsequenceType enum completeness and properties
    test_color_logic.py: Color enum and enable/disable decision logic
"""
