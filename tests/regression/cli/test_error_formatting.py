"""Regression tests for error formatting infrastructure.

This module tests:
- HatchArgumentParser error formatting
- ValidationError exception class
- format_validation_error utility
- format_info utility

Reference: R13 §4.2.1 (13-error_message_formatting_v0.md) - HatchArgumentParser
Reference: R13 §4.2.2 (13-error_message_formatting_v0.md) - ValidationError
Reference: R13 §4.3 (13-error_message_formatting_v0.md) - Utilities
Reference: R13 §6.1 (13-error_message_formatting_v0.md) - Argparse error catalog
"""

import unittest
import subprocess
import sys


class TestHatchArgumentParser(unittest.TestCase):
    """Tests for HatchArgumentParser error formatting.
    
    Reference: R13 §4.2.1 - Custom ArgumentParser
    Reference: R13 §6.1 - Argparse error catalog
    """

    def test_argparse_error_has_error_prefix(self):
        """Argparse errors should have [ERROR] prefix."""
        from hatch.cli.__main__ import HatchArgumentParser
        import io
        
        parser = HatchArgumentParser(prog="test")
        
        # Capture stderr
        captured = io.StringIO()
        try:
            parser.error("test error message")
        except SystemExit:
            pass
        
        # The error method writes to stderr and exits
        # We need to test via subprocess for proper capture
        result = subprocess.run(
            [sys.executable, "-c", 
             "from hatch.cli.__main__ import HatchArgumentParser; "
             "p = HatchArgumentParser(); p.error('test error')"],
            capture_output=True,
            text=True
        )
        
        self.assertIn("[ERROR]", result.stderr)

    def test_argparse_error_unrecognized_argument(self):
        """Unrecognized argument error should have [ERROR] prefix."""
        result = subprocess.run(
            [sys.executable, "-m", "hatch.cli", "--invalid-arg"],
            capture_output=True,
            text=True
        )
        
        self.assertIn("[ERROR]", result.stderr)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_argparse_error_exit_code_2(self):
        """Argparse errors should exit with code 2."""
        result = subprocess.run(
            [sys.executable, "-m", "hatch.cli", "--invalid-arg"],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 2)

    def test_argparse_error_no_ansi_in_pipe(self):
        """Argparse errors should not have ANSI codes when piped."""
        result = subprocess.run(
            [sys.executable, "-m", "hatch.cli", "--invalid-arg"],
            capture_output=True,
            text=True
        )
        
        # When piped (capture_output=True), stdout is not a TTY
        # so ANSI codes should not be present
        self.assertNotIn("\033[", result.stderr)

    def test_hatch_argument_parser_class_exists(self):
        """HatchArgumentParser class should be importable."""
        from hatch.cli.__main__ import HatchArgumentParser
        import argparse
        
        self.assertTrue(issubclass(HatchArgumentParser, argparse.ArgumentParser))

    def test_hatch_argument_parser_has_error_method(self):
        """HatchArgumentParser should have overridden error method."""
        from hatch.cli.__main__ import HatchArgumentParser
        import argparse
        
        parser = HatchArgumentParser()
        
        # Check that error method is overridden (not the same as base class)
        self.assertIsNot(
            HatchArgumentParser.error,
            argparse.ArgumentParser.error
        )


if __name__ == '__main__':
    unittest.main()
