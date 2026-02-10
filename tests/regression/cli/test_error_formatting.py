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

        # Verify parser class exists
        HatchArgumentParser(prog="test")

        # Test via subprocess for proper stderr capture
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from hatch.cli.__main__ import HatchArgumentParser; "
                "p = HatchArgumentParser(); p.error('test error')",
            ],
            capture_output=True,
            text=True,
        )

        self.assertIn("[ERROR]", result.stderr)

    def test_argparse_error_unrecognized_argument(self):
        """Unrecognized argument error should have [ERROR] prefix."""
        result = subprocess.run(
            [sys.executable, "-m", "hatch.cli", "--invalid-arg"],
            capture_output=True,
            text=True,
        )

        self.assertIn("[ERROR]", result.stderr)
        self.assertIn("unrecognized arguments", result.stderr)

    def test_argparse_error_exit_code_2(self):
        """Argparse errors should exit with code 2."""
        result = subprocess.run(
            [sys.executable, "-m", "hatch.cli", "--invalid-arg"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)

    def test_argparse_error_no_ansi_in_pipe(self):
        """Argparse errors should not have ANSI codes when piped."""
        result = subprocess.run(
            [sys.executable, "-m", "hatch.cli", "--invalid-arg"],
            capture_output=True,
            text=True,
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

        # Verify parser class exists
        HatchArgumentParser()

        # Check that error method is overridden (not the same as base class)
        self.assertIsNot(HatchArgumentParser.error, argparse.ArgumentParser.error)


if __name__ == "__main__":
    unittest.main()


class TestValidationError(unittest.TestCase):
    """Tests for ValidationError exception class.

    Reference: R13 §4.2.2 - ValidationError interface
    Reference: R13 §7.2 - ValidationError contract
    """

    def test_validation_error_attributes(self):
        """ValidationError should have message, field, and suggestion attributes."""
        from hatch.cli.cli_utils import ValidationError

        error = ValidationError(
            "Test message", field="--host", suggestion="Use valid host"
        )

        self.assertEqual(error.message, "Test message")
        self.assertEqual(error.field, "--host")
        self.assertEqual(error.suggestion, "Use valid host")

    def test_validation_error_str_returns_message(self):
        """ValidationError str() should return message."""
        from hatch.cli.cli_utils import ValidationError

        error = ValidationError("Test message")
        self.assertEqual(str(error), "Test message")

    def test_validation_error_optional_field(self):
        """ValidationError field should be optional."""
        from hatch.cli.cli_utils import ValidationError

        error = ValidationError("Test message")
        self.assertIsNone(error.field)

    def test_validation_error_optional_suggestion(self):
        """ValidationError suggestion should be optional."""
        from hatch.cli.cli_utils import ValidationError

        error = ValidationError("Test message")
        self.assertIsNone(error.suggestion)

    def test_validation_error_is_exception(self):
        """ValidationError should be an Exception subclass."""
        from hatch.cli.cli_utils import ValidationError

        self.assertTrue(issubclass(ValidationError, Exception))

    def test_validation_error_can_be_raised(self):
        """ValidationError should be raisable."""
        from hatch.cli.cli_utils import ValidationError

        with self.assertRaises(ValidationError) as context:
            raise ValidationError("Test error", field="--host")

        self.assertEqual(context.exception.message, "Test error")
        self.assertEqual(context.exception.field, "--host")


class TestFormatValidationError(unittest.TestCase):
    """Tests for format_validation_error utility.

    Reference: R13 §4.3 - format_validation_error
    """

    def test_format_validation_error_basic(self):
        """format_validation_error should print [ERROR] prefix."""
        from hatch.cli.cli_utils import ValidationError, format_validation_error
        import io
        import sys

        error = ValidationError("Test error message")

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_validation_error(error)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("Test error message", output)

    def test_format_validation_error_with_field(self):
        """format_validation_error should print field if provided."""
        from hatch.cli.cli_utils import ValidationError, format_validation_error
        import io
        import sys

        error = ValidationError("Test error", field="--host")

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_validation_error(error)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertIn("Field: --host", output)

    def test_format_validation_error_with_suggestion(self):
        """format_validation_error should print suggestion if provided."""
        from hatch.cli.cli_utils import ValidationError, format_validation_error
        import io
        import sys

        error = ValidationError("Test error", suggestion="Use valid host")

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_validation_error(error)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertIn("Suggestion: Use valid host", output)

    def test_format_validation_error_full(self):
        """format_validation_error should print all fields when provided."""
        from hatch.cli.cli_utils import ValidationError, format_validation_error
        import io
        import sys

        error = ValidationError(
            "Invalid host 'vsc'",
            field="--host",
            suggestion="Supported hosts: claude-desktop, vscode",
        )

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_validation_error(error)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertIn("[ERROR]", output)
        self.assertIn("Invalid host 'vsc'", output)
        self.assertIn("Field: --host", output)
        self.assertIn("Suggestion: Supported hosts: claude-desktop, vscode", output)

    def test_format_validation_error_no_color_in_non_tty(self):
        """format_validation_error should not include ANSI codes when not in TTY."""
        from hatch.cli.cli_utils import ValidationError, format_validation_error
        import io
        import sys

        error = ValidationError("Test error")

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_validation_error(error)
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertNotIn("\033[", output)


class TestFormatInfo(unittest.TestCase):
    """Tests for format_info utility.

    Reference: R13-B §B.6.2 - Operation cancelled normalization
    """

    def test_format_info_basic(self):
        """format_info should print [INFO] prefix."""
        from hatch.cli.cli_utils import format_info
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_info("Operation cancelled")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertIn("[INFO]", output)
        self.assertIn("Operation cancelled", output)

    def test_format_info_no_color_in_non_tty(self):
        """format_info should not include ANSI codes when not in TTY."""
        from hatch.cli.cli_utils import format_info
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_info("Test message")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue()
        self.assertNotIn("\033[", output)

    def test_format_info_output_format(self):
        """format_info output should match expected format."""
        from hatch.cli.cli_utils import format_info
        import io
        import sys

        captured = io.StringIO()
        sys.stdout = captured
        try:
            format_info("Test message")
        finally:
            sys.stdout = sys.__stdout__

        output = captured.getvalue().strip()
        self.assertEqual(output, "[INFO] Test message")
