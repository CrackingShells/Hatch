"""
Test suite for hatch --version command implementation.

This module tests the version command functionality:
- Version retrieval from importlib.metadata
- Error handling for PackageNotFoundError
- CLI version display format
- Import safety after removing __version__
- No conflicts with existing flags

Tests follow CrackingShells testing standards using wobble framework.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.cli_hatch import main, get_hatch_version

try:
    from wobble.decorators import regression_test, integration_test
except ImportError:
    # Fallback decorators if wobble not available
    def regression_test(func):
        return func
    
    def integration_test(scope="component"):
        def decorator(func):
            return func
        return decorator


class TestVersionCommand(unittest.TestCase):
    """Test suite for hatch --version command implementation."""
    
    @regression_test
    def test_get_hatch_version_retrieves_from_metadata(self):
        """Test get_hatch_version() retrieves version from importlib.metadata."""
        with patch('hatch.cli_hatch.version', return_value='0.7.0-dev.3') as mock_version:
            result = get_hatch_version()

            self.assertEqual(result, '0.7.0-dev.3')
            mock_version.assert_called_once_with('hatch')

    @regression_test
    def test_get_hatch_version_handles_package_not_found(self):
        """Test get_hatch_version() handles PackageNotFoundError gracefully."""
        from importlib.metadata import PackageNotFoundError

        with patch('hatch.cli_hatch.version', side_effect=PackageNotFoundError()):
            result = get_hatch_version()

            self.assertEqual(result, 'unknown (development mode)')
    
    @integration_test(scope="component")
    def test_version_command_displays_correct_format(self):
        """Test version command displays correct format via CLI."""
        test_args = ['hatch', '--version']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.get_hatch_version', return_value='0.7.0-dev.3'):
                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    with self.assertRaises(SystemExit) as cm:
                        main()
                    
                    # argparse action='version' exits with code 0
                    self.assertEqual(cm.exception.code, 0)
                    
                    # Verify output format: "hatch 0.7.0-dev.3"
                    output = mock_stdout.getvalue().strip()
                    self.assertRegex(output, r'hatch\s+0\.7\.0-dev\.3')
    
    @integration_test(scope="component")
    def test_import_hatch_without_version_attribute(self):
        """Test that importing hatch module works without __version__ attribute."""
        try:
            import hatch
            
            # Import should succeed
            self.assertIsNotNone(hatch)
            
            # __version__ should not exist (removed in implementation)
            self.assertFalse(hasattr(hatch, '__version__'),
                            "hatch.__version__ should not exist after cleanup")
            
        except ImportError as e:
            self.fail(f"Failed to import hatch module: {e}")
    
    @regression_test
    def test_no_conflict_with_package_version_flag(self):
        """Test that --version (Hatch) doesn't conflict with -v (package version)."""
        # Test package add command with -v flag (package version specification)
        test_args = ['hatch', 'package', 'add', 'test-package', '-v', '1.0.0']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env:
                mock_env_instance = MagicMock()
                mock_env.return_value = mock_env_instance
                mock_env_instance.add_package_to_environment.return_value = True
                
                try:
                    main()
                except SystemExit as e:
                    # Should execute successfully (exit code 0)
                    self.assertEqual(e.code, 0)
                
                # Verify package add was called with version argument
                mock_env_instance.add_package_to_environment.assert_called_once()
                call_args = mock_env_instance.add_package_to_environment.call_args
                
                # Version argument should be '1.0.0'
                self.assertEqual(call_args[0][2], '1.0.0')  # Third positional arg is version


if __name__ == '__main__':
    unittest.main()

