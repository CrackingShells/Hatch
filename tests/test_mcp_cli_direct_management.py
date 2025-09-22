"""
Test suite for MCP CLI direct management commands (Phase 3e).

This module tests the new MCP direct management functionality:
- hatch mcp configure
- hatch mcp remove

Tests cover argument parsing, server configuration, output formatting,
and error handling scenarios.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the parent directory to the path to import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.cli_hatch import (
    main, handle_mcp_configure, handle_mcp_remove, parse_env_vars, parse_headers
)
from hatch.mcp_host_config.models import MCPHostType, MCPServerConfig
from wobble import regression_test, integration_test


class TestMCPConfigureCommand(unittest.TestCase):
    """Test suite for MCP configure command."""
    
    @regression_test
    def test_configure_argument_parsing_basic(self):
        """Test basic argument parsing for 'hatch mcp configure' command."""
        test_args = ['hatch', 'mcp', 'configure', 'claude-desktop', 'weather-server', 'python', 'weather.py']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_configure', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with(
                            'claude-desktop', 'weather-server', 'python', ['weather.py'],
                            None, None, None, False, False, False
                        )
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_configure_argument_parsing_with_options(self):
        """Test argument parsing with environment variables and options."""
        test_args = [
            'hatch', 'mcp', 'configure', 'cursor', 'file-server', 'node', 'server.js', 'arg1', 'arg2',
            '--env', 'API_KEY=secret', '--env', 'DEBUG=true',
            '--url', 'http://localhost:8080',
            '--headers', 'Authorization=Bearer token',
            '--no-backup', '--dry-run', '--auto-approve'
        ]
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_configure', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with(
                            'cursor', 'file-server', 'node', ['server.js', 'arg1', 'arg2'],
                            ['API_KEY=secret', 'DEBUG=true'], 'http://localhost:8080',
                            ['Authorization=Bearer token'], True, True, True
                        )
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_parse_env_vars(self):
        """Test environment variable parsing utility."""
        # Valid environment variables
        env_list = ['API_KEY=secret', 'DEBUG=true', 'PORT=8080']
        result = parse_env_vars(env_list)
        
        expected = {
            'API_KEY': 'secret',
            'DEBUG': 'true',
            'PORT': '8080'
        }
        self.assertEqual(result, expected)
        
        # Empty list
        self.assertEqual(parse_env_vars(None), {})
        self.assertEqual(parse_env_vars([]), {})
        
        # Invalid format (should be skipped with warning)
        with patch('builtins.print') as mock_print:
            result = parse_env_vars(['INVALID_FORMAT', 'VALID=value'])
            self.assertEqual(result, {'VALID': 'value'})
            mock_print.assert_called()
    
    @regression_test
    def test_parse_headers(self):
        """Test HTTP headers parsing utility."""
        # Valid headers
        headers_list = ['Authorization=Bearer token', 'Content-Type=application/json']
        result = parse_headers(headers_list)
        
        expected = {
            'Authorization': 'Bearer token',
            'Content-Type': 'application/json'
        }
        self.assertEqual(result, expected)
        
        # Empty list
        self.assertEqual(parse_headers(None), {})
        self.assertEqual(parse_headers([]), {})
    
    @integration_test(scope="component")
    def test_configure_invalid_host(self):
        """Test configure command with invalid host type."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_configure('invalid-host', 'test-server', 'python', ['test.py'])
            
            self.assertEqual(result, 1)
            
            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Invalid host 'invalid-host'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_configure_dry_run(self):
        """Test configure command dry run functionality."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_configure(
                'claude-desktop', 'weather-server', 'python', ['weather.py'],
                env=['API_KEY=secret'], url=None,
                dry_run=True
            )
            
            self.assertEqual(result, 0)
            
            # Verify dry run output
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("[DRY RUN] Would configure MCP server 'weather-server'" in call for call in print_calls))
            self.assertTrue(any("[DRY RUN] Command: python" in call for call in print_calls))
            self.assertTrue(any("[DRY RUN] Environment:" in call for call in print_calls))
            # URL should not be present for local server configuration
    
    @integration_test(scope="component")
    def test_configure_successful(self):
        """Test successful MCP server configuration."""
        from hatch.mcp_host_config.host_management import ConfigurationResult

        mock_result = ConfigurationResult(
            success=True,
            hostname='claude-desktop',
            server_name='weather-server',
            backup_path=Path('/test/backup.json')
        )

        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.configure_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_configure(
                        'claude-desktop', 'weather-server', 'python', ['weather.py'],
                        auto_approve=True
                    )

                    self.assertEqual(result, 0)
                    mock_manager.configure_server.assert_called_once()

                    # Verify success message
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("[SUCCESS] Successfully configured MCP server 'weather-server'" in call for call in print_calls))
                    self.assertTrue(any("Backup created:" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_configure_failed(self):
        """Test failed MCP server configuration."""
        from hatch.mcp_host_config.host_management import ConfigurationResult
        
        mock_result = ConfigurationResult(
            success=False,
            hostname='claude-desktop',
            server_name='weather-server',
            error_message='Configuration validation failed'
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.configure_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_configure(
                        'claude-desktop', 'weather-server', 'python', ['weather.py'],
                        auto_approve=True
                    )
                    
                    self.assertEqual(result, 1)
                    
                    # Verify error message
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("[ERROR] Failed to configure MCP server 'weather-server'" in call for call in print_calls))
                    self.assertTrue(any("Configuration validation failed" in call for call in print_calls))


class TestMCPRemoveCommand(unittest.TestCase):
    """Test suite for MCP remove command."""
    
    @regression_test
    def test_remove_argument_parsing(self):
        """Test argument parsing for 'hatch mcp remove' command."""
        test_args = ['hatch', 'mcp', 'remove', 'vscode', 'old-server', '--no-backup', '--auto-approve']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_remove', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with('vscode', 'old-server', True, False, True)
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @integration_test(scope="component")
    def test_remove_invalid_host(self):
        """Test remove command with invalid host type."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_remove('invalid-host', 'test-server')
            
            self.assertEqual(result, 1)
            
            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Invalid host 'invalid-host'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_remove_dry_run(self):
        """Test remove command dry run functionality."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_remove('claude-desktop', 'old-server', no_backup=True, dry_run=True)
            
            self.assertEqual(result, 0)
            
            # Verify dry run output
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("[DRY RUN] Would remove MCP server 'old-server'" in call for call in print_calls))
            self.assertTrue(any("[DRY RUN] Backup: Disabled" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_remove_successful(self):
        """Test successful MCP server removal."""
        from hatch.mcp_host_config.host_management import ConfigurationResult
        
        mock_result = ConfigurationResult(
            success=True,
            hostname='claude-desktop',
            server_name='old-server',
            backup_path=Path('/test/backup.json')
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.remove_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_remove('claude-desktop', 'old-server', auto_approve=True)
                    
                    self.assertEqual(result, 0)
                    mock_manager.remove_server.assert_called_once()
                    
                    # Verify success message
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("[SUCCESS] Successfully removed MCP server 'old-server'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_remove_failed(self):
        """Test failed MCP server removal."""
        from hatch.mcp_host_config.host_management import ConfigurationResult
        
        mock_result = ConfigurationResult(
            success=False,
            hostname='claude-desktop',
            server_name='old-server',
            error_message='Server not found in configuration'
        )
        
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.remove_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_remove('claude-desktop', 'old-server', auto_approve=True)
                    
                    self.assertEqual(result, 1)
                    
                    # Verify error message
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("[ERROR] Failed to remove MCP server 'old-server'" in call for call in print_calls))
                    self.assertTrue(any("Server not found in configuration" in call for call in print_calls))


if __name__ == '__main__':
    unittest.main()
