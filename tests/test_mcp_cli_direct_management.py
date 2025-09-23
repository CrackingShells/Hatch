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
    main, handle_mcp_configure, handle_mcp_remove, handle_mcp_remove_server,
    handle_mcp_remove_host, parse_env_vars, parse_headers
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
        """Test argument parsing for 'hatch mcp remove server' command."""
        test_args = ['hatch', 'mcp', 'remove', 'server', 'old-server', '--host', 'vscode', '--no-backup', '--auto-approve']

        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_remove_server', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with('old-server', 'vscode', None, True, False, True)
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


class TestMCPRemoveServerCommand(unittest.TestCase):
    """Test suite for MCP remove server command (new object-action pattern)."""

    @regression_test
    def test_remove_server_argument_parsing(self):
        """Test argument parsing for 'hatch mcp remove server' command."""
        test_args = ['hatch', 'mcp', 'remove', 'server', 'test-server', '--host', 'claude-desktop', '--no-backup']

        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_remove_server', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with('test-server', 'claude-desktop', None, True, False, False)
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)

    @integration_test(scope="component")
    def test_remove_server_multi_host(self):
        """Test remove server from multiple hosts."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.remove_server.return_value = MagicMock(success=True, backup_path=None)
            mock_manager_class.return_value = mock_manager

            with patch('builtins.print') as mock_print:
                result = handle_mcp_remove_server('test-server', 'claude-desktop,cursor', auto_approve=True)

                self.assertEqual(result, 0)
                self.assertEqual(mock_manager.remove_server.call_count, 2)

                # Verify success messages
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("[SUCCESS] Successfully removed 'test-server' from 'claude-desktop'" in call for call in print_calls))
                self.assertTrue(any("[SUCCESS] Successfully removed 'test-server' from 'cursor'" in call for call in print_calls))

    @integration_test(scope="component")
    def test_remove_server_no_host_specified(self):
        """Test remove server with no host specified."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_remove_server('test-server')

            self.assertEqual(result, 1)

            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Must specify either --host or --env" in call for call in print_calls))

    @integration_test(scope="component")
    def test_remove_server_dry_run(self):
        """Test remove server dry run functionality."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_remove_server('test-server', 'claude-desktop', dry_run=True)

            self.assertEqual(result, 0)

            # Verify dry run output
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("[DRY RUN] Would remove MCP server 'test-server' from hosts: claude-desktop" in call for call in print_calls))


class TestMCPRemoveHostCommand(unittest.TestCase):
    """Test suite for MCP remove host command."""

    @regression_test
    def test_remove_host_argument_parsing(self):
        """Test argument parsing for 'hatch mcp remove host' command."""
        test_args = ['hatch', 'mcp', 'remove', 'host', 'claude-desktop', '--auto-approve']

        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_remove_host', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with('claude-desktop', False, False, True)
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)

    @integration_test(scope="component")
    def test_remove_host_successful(self):
        """Test successful host configuration removal."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = Path("/test/backup.json")
            mock_manager.remove_host_configuration.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            with patch('builtins.print') as mock_print:
                result = handle_mcp_remove_host('claude-desktop', auto_approve=True)

                self.assertEqual(result, 0)
                mock_manager.remove_host_configuration.assert_called_once_with(
                    hostname='claude-desktop', no_backup=False
                )

                # Verify success message
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("[SUCCESS] Successfully removed host configuration for 'claude-desktop'" in call for call in print_calls))

    @integration_test(scope="component")
    def test_remove_host_invalid_host(self):
        """Test remove host with invalid host type."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_remove_host('invalid-host')

            self.assertEqual(result, 1)

            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Invalid host 'invalid-host'" in call for call in print_calls))

    @integration_test(scope="component")
    def test_remove_host_dry_run(self):
        """Test remove host dry run functionality."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_remove_host('claude-desktop', dry_run=True)

            self.assertEqual(result, 0)

            # Verify dry run output
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("[DRY RUN] Would remove entire host configuration for 'claude-desktop'" in call for call in print_calls))


if __name__ == '__main__':
    unittest.main()
