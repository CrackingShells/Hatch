"""Integration tests for CLI reporter infrastructure.

This package contains integration tests for CLI handler → ResultReporter flow:
- Handler creates ResultReporter with correct command name
- Handler adds consequences before confirmation prompt
- Dry-run flag propagates correctly
- ConversionReport integration in MCP handlers

These tests verify component communication and data flow integrity
across the CLI reporting system.

Test Groups:
    test_cli_reporter_integration.py: Handler → ResultReporter integration
"""
