"""
Test suite for MCP CLI package management enhancements.

This module tests the enhanced package management commands with MCP host
configuration integration following CrackingShells testing standards.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import wobble
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wobble.decorators import regression_test, integration_test
except ImportError:
    # Fallback decorators if wobble is not available
    def regression_test(func):
        return func
    
    def integration_test(scope="component"):
        def decorator(func):
            return func
        return decorator

from hatch.cli_hatch import parse_host_list, request_confirmation
from hatch.mcp_host_config import MCPHostType


class TestMCPCLIPackageManagement(unittest.TestCase):
    """Test suite for MCP CLI package management enhancements."""

    @regression_test
    def test_parse_host_list_comma_separated(self):
        """Test parsing comma-separated host list."""
        hosts = parse_host_list("claude-desktop,cursor,vscode")
        expected = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR, MCPHostType.VSCODE]
        self.assertEqual(hosts, expected)

    @regression_test
    def test_parse_host_list_single_host(self):
        """Test parsing single host."""
        hosts = parse_host_list("claude-desktop")
        expected = [MCPHostType.CLAUDE_DESKTOP]
        self.assertEqual(hosts, expected)

    @regression_test
    def test_parse_host_list_empty(self):
        """Test parsing empty host list."""
        hosts = parse_host_list("")
        self.assertEqual(hosts, [])

    @regression_test
    def test_parse_host_list_none(self):
        """Test parsing None host list."""
        hosts = parse_host_list(None)
        self.assertEqual(hosts, [])

    @regression_test
    def test_parse_host_list_all(self):
        """Test parsing 'all' host list."""
        with patch('hatch.cli_hatch.MCPHostRegistry.detect_available_hosts') as mock_detect:
            mock_detect.return_value = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR]
            hosts = parse_host_list("all")
            expected = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR]
            self.assertEqual(hosts, expected)
            mock_detect.assert_called_once()

    @regression_test
    def test_parse_host_list_invalid_host(self):
        """Test parsing invalid host raises ValueError."""
        with self.assertRaises(ValueError) as context:
            parse_host_list("invalid-host")
        
        self.assertIn("Unknown host 'invalid-host'", str(context.exception))
        self.assertIn("Available:", str(context.exception))

    @regression_test
    def test_parse_host_list_mixed_valid_invalid(self):
        """Test parsing mixed valid and invalid hosts."""
        with self.assertRaises(ValueError) as context:
            parse_host_list("claude-desktop,invalid-host,cursor")
        
        self.assertIn("Unknown host 'invalid-host'", str(context.exception))

    @regression_test
    def test_parse_host_list_whitespace_handling(self):
        """Test parsing host list with whitespace."""
        hosts = parse_host_list(" claude-desktop , cursor , vscode ")
        expected = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR, MCPHostType.VSCODE]
        self.assertEqual(hosts, expected)

    @regression_test
    def test_request_confirmation_auto_approve(self):
        """Test confirmation with auto-approve flag."""
        result = request_confirmation("Test message?", auto_approve=True)
        self.assertTrue(result)

    @regression_test
    def test_request_confirmation_user_yes(self):
        """Test confirmation with user saying yes."""
        with patch('builtins.input', return_value='y'):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertTrue(result)

    @regression_test
    def test_request_confirmation_user_yes_full(self):
        """Test confirmation with user saying 'yes'."""
        with patch('builtins.input', return_value='yes'):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertTrue(result)

    @regression_test
    def test_request_confirmation_user_no(self):
        """Test confirmation with user saying no."""
        with patch('builtins.input', return_value='n'):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertFalse(result)

    @regression_test
    def test_request_confirmation_user_no_full(self):
        """Test confirmation with user saying 'no'."""
        with patch('builtins.input', return_value='no'):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertFalse(result)

    @regression_test
    def test_request_confirmation_user_empty(self):
        """Test confirmation with user pressing enter (default no)."""
        with patch('builtins.input', return_value=''):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertFalse(result)

    @integration_test(scope="component")
    def test_package_add_argument_parsing(self):
        """Test package add command argument parsing with MCP flags."""
        from hatch.cli_hatch import main
        import argparse
        
        # Mock argparse to capture parsed arguments
        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'package'
            mock_args.pkg_command = 'add'
            mock_args.package_path_or_name = 'test-package'
            mock_args.host = 'claude-desktop,cursor'
            mock_args.no_mcp_config = False
            mock_args.env = None
            mock_args.version = None
            mock_args.force_download = False
            mock_args.refresh_registry = False
            mock_args.auto_approve = False
            mock_parse.return_value = mock_args
            
            # Mock environment manager to avoid actual operations
            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
                mock_env_manager.return_value.add_package_to_environment.return_value = True
                mock_env_manager.return_value.get_current_environment.return_value = "default"
                
                # Mock MCP manager
                with patch('hatch.cli_hatch.MCPHostConfigurationManager'):
                    with patch('builtins.print') as mock_print:
                        result = main()
                        
                        # Should succeed
                        self.assertEqual(result, 0)
                        
                        # Should print success message
                        mock_print.assert_any_call("Successfully added package: test-package")

    @integration_test(scope="component")
    def test_package_sync_argument_parsing(self):
        """Test package sync command argument parsing."""
        from hatch.cli_hatch import main
        import argparse
        
        # Mock argparse to capture parsed arguments
        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'package'
            mock_args.pkg_command = 'sync'
            mock_args.package_name = 'test-package'
            mock_args.host = 'claude-desktop,cursor'
            mock_args.env = None
            mock_args.dry_run = False
            mock_args.auto_approve = False
            mock_args.no_backup = False
            mock_parse.return_value = mock_args
            
            # Mock environment manager
            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
                mock_env_manager.return_value.get_current_environment.return_value = "default"
                mock_env_manager.return_value.list_packages.return_value = [
                    {'name': 'test-package', 'version': '1.0.0'}
                ]
                
                # Mock MCP manager
                with patch('hatch.cli_hatch.MCPHostConfigurationManager'):
                    with patch('builtins.print') as mock_print:
                        result = main()
                        
                        # Should succeed
                        self.assertEqual(result, 0)
                        
                        # Should print sync message
                        mock_print.assert_any_call("Synchronizing MCP servers for package 'test-package' to hosts: ['claude-desktop', 'cursor']")

    @integration_test(scope="component")
    def test_package_sync_package_not_found(self):
        """Test package sync when package doesn't exist."""
        from hatch.cli_hatch import main
        import argparse
        
        # Mock argparse to capture parsed arguments
        with patch('argparse.ArgumentParser.parse_args') as mock_parse:
            mock_args = MagicMock()
            mock_args.command = 'package'
            mock_args.pkg_command = 'sync'
            mock_args.package_name = 'nonexistent-package'
            mock_args.host = 'claude-desktop'
            mock_args.env = None
            mock_parse.return_value = mock_args
            
            # Mock environment manager with empty package list
            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
                mock_env_manager.return_value.get_current_environment.return_value = "default"
                mock_env_manager.return_value.list_packages.return_value = []
                
                with patch('builtins.print') as mock_print:
                    result = main()
                    
                    # Should fail
                    self.assertEqual(result, 1)
                    
                    # Should print error message
                    mock_print.assert_any_call("Package 'nonexistent-package' not found in environment 'default'")


if __name__ == '__main__':
    unittest.main()
