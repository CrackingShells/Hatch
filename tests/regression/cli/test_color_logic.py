"""Regression tests for Color enum and color enable/disable logic.

This module tests:
- Color enum completeness (all 14 values defined)
- Color enable/disable decision logic (TTY, NO_COLOR)

Reference: R05 §3.4 (05-test_definition_v0.md)

Test Groups:
    TestColorEnum: Color enum completeness and ANSI code format
    TestColorsEnabled: Color enable/disable decision logic
"""

import os
import sys
import unittest
from unittest.mock import patch


class TestColorEnum(unittest.TestCase):
    """Tests for Color enum completeness and structure.
    
    Reference: R06 §3.1 - Color interface contract
    """

    def test_color_enum_exists(self):
        """Color enum should be importable from cli_utils."""
        from hatch.cli.cli_utils import Color
        self.assertTrue(hasattr(Color, '__members__'))

    def test_color_enum_has_bright_colors(self):
        """Color enum should have all 6 bright colors for results."""
        from hatch.cli.cli_utils import Color
        
        bright_colors = ['GREEN', 'RED', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN']
        for color_name in bright_colors:
            self.assertTrue(
                hasattr(Color, color_name),
                f"Color enum missing bright color: {color_name}"
            )

    def test_color_enum_has_dim_colors(self):
        """Color enum should have all 6 dim colors for prompts."""
        from hatch.cli.cli_utils import Color
        
        dim_colors = [
            'GREEN_DIM', 'RED_DIM', 'YELLOW_DIM',
            'BLUE_DIM', 'MAGENTA_DIM', 'CYAN_DIM'
        ]
        for color_name in dim_colors:
            self.assertTrue(
                hasattr(Color, color_name),
                f"Color enum missing dim color: {color_name}"
            )

    def test_color_enum_has_utility_colors(self):
        """Color enum should have GRAY and RESET utility colors."""
        from hatch.cli.cli_utils import Color
        
        self.assertTrue(hasattr(Color, 'GRAY'), "Color enum missing GRAY")
        self.assertTrue(hasattr(Color, 'RESET'), "Color enum missing RESET")

    def test_color_enum_total_count(self):
        """Color enum should have exactly 14 members."""
        from hatch.cli.cli_utils import Color
        
        # 6 bright + 6 dim + GRAY + RESET = 14
        self.assertEqual(len(Color), 14, f"Expected 14 colors, got {len(Color)}")

    def test_color_values_are_ansi_codes(self):
        """Color values should be ANSI escape sequences."""
        from hatch.cli.cli_utils import Color
        
        for color in Color:
            self.assertTrue(
                color.value.startswith('\033['),
                f"{color.name} value should start with ANSI escape: {repr(color.value)}"
            )
            self.assertTrue(
                color.value.endswith('m'),
                f"{color.name} value should end with 'm': {repr(color.value)}"
            )

    def test_reset_clears_formatting(self):
        """RESET should be the standard ANSI reset code."""
        from hatch.cli.cli_utils import Color
        
        self.assertEqual(Color.RESET.value, '\033[0m')


class TestColorsEnabled(unittest.TestCase):
    """Tests for color enable/disable decision logic.
    
    Reference: R05 §3.4 - Color Enable/Disable Logic test group
    """

    def test_colors_disabled_when_no_color_set(self):
        """Colors should be disabled when NO_COLOR=1."""
        from hatch.cli.cli_utils import _colors_enabled
        
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            self.assertFalse(_colors_enabled())

    def test_colors_disabled_when_no_color_truthy(self):
        """Colors should be disabled when NO_COLOR=true."""
        from hatch.cli.cli_utils import _colors_enabled
        
        with patch.dict(os.environ, {'NO_COLOR': 'true'}):
            self.assertFalse(_colors_enabled())

    def test_colors_enabled_when_no_color_empty(self):
        """Colors should be enabled when NO_COLOR is empty string (if TTY)."""
        from hatch.cli.cli_utils import _colors_enabled
        
        with patch.dict(os.environ, {'NO_COLOR': ''}, clear=False):
            with patch.object(sys.stdout, 'isatty', return_value=True):
                self.assertTrue(_colors_enabled())

    def test_colors_enabled_when_no_color_unset(self):
        """Colors should be enabled when NO_COLOR is not set (if TTY)."""
        from hatch.cli.cli_utils import _colors_enabled
        
        env_without_no_color = {k: v for k, v in os.environ.items() if k != 'NO_COLOR'}
        with patch.dict(os.environ, env_without_no_color, clear=True):
            with patch.object(sys.stdout, 'isatty', return_value=True):
                self.assertTrue(_colors_enabled())

    def test_colors_disabled_when_not_tty(self):
        """Colors should be disabled when stdout is not a TTY."""
        from hatch.cli.cli_utils import _colors_enabled
        
        env_without_no_color = {k: v for k, v in os.environ.items() if k != 'NO_COLOR'}
        with patch.dict(os.environ, env_without_no_color, clear=True):
            with patch.object(sys.stdout, 'isatty', return_value=False):
                self.assertFalse(_colors_enabled())

    def test_colors_enabled_when_tty_and_no_no_color(self):
        """Colors should be enabled when TTY and NO_COLOR not set."""
        from hatch.cli.cli_utils import _colors_enabled
        
        env_without_no_color = {k: v for k, v in os.environ.items() if k != 'NO_COLOR'}
        with patch.dict(os.environ, env_without_no_color, clear=True):
            with patch.object(sys.stdout, 'isatty', return_value=True):
                self.assertTrue(_colors_enabled())


if __name__ == '__main__':
    unittest.main()
