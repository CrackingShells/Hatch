"""
Test suite for MCP CLI discovery and listing commands (Phase 3c).

This module tests the new MCP discovery and listing functionality:
- hatch mcp discover hosts
- hatch mcp discover servers  
- hatch mcp list hosts
- hatch mcp list servers

Tests cover argument parsing, backend integration, output formatting,
and error handling scenarios.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add the parent directory to the path to import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.cli_hatch import (
    main, handle_mcp_discover_hosts, handle_mcp_discover_servers,
    handle_mcp_list_hosts, handle_mcp_list_servers
)
from hatch.mcp_host_config.models import MCPHostType, MCPServerConfig
from hatch.environment_manager import HatchEnvironmentManager
from wobble import regression_test, integration_test


class TestMCPDiscoveryCommands(unittest.TestCase):
    """Test suite for MCP discovery commands."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)
        self.mock_env_manager.get_current_environment.return_value = "test-env"
        self.mock_env_manager.environment_exists.return_value = True
        
    @regression_test
    def test_discover_hosts_argument_parsing(self):
        """Test argument parsing for 'hatch mcp discover hosts' command."""
        test_args = ['hatch', 'mcp', 'discover', 'hosts']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_discover_hosts', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once()
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_discover_servers_argument_parsing(self):
        """Test argument parsing for 'hatch mcp discover servers' command."""
        test_args = ['hatch', 'mcp', 'discover', 'servers', '--env', 'test-env']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_discover_servers', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once()
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_discover_servers_default_environment(self):
        """Test discover servers uses current environment when --env not specified."""
        test_args = ['hatch', 'mcp', 'discover', 'servers']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_class:
                mock_env_manager = MagicMock()
                mock_env_class.return_value = mock_env_manager
                
                with patch('hatch.cli_hatch.handle_mcp_discover_servers', return_value=0) as mock_handler:
                    try:
                        main()
                        # Should be called with env_manager and None (default env)
                        mock_handler.assert_called_once()
                        args = mock_handler.call_args[0]
                        self.assertEqual(len(args), 2)  # env_manager, env_name
                        self.assertIsNone(args[1])  # env_name should be None
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @integration_test(scope="component")
    def test_discover_hosts_backend_integration(self):
        """Test discover hosts integration with MCPHostRegistry."""
        with patch('hatch.mcp_host_config.strategies'):  # Import strategies
            with patch('hatch.cli_hatch.MCPHostRegistry') as mock_registry:
                mock_registry.detect_available_hosts.return_value = [
                    MCPHostType.CLAUDE_DESKTOP,
                    MCPHostType.CURSOR
                ]
                
                # Mock strategy for each host type
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = Path("/test/config.json")
                mock_registry.get_strategy.return_value = mock_strategy
                
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_discover_hosts()
                    
                    self.assertEqual(result, 0)
                    mock_registry.detect_available_hosts.assert_called_once()
                    
                    # Verify output contains expected information
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("Available MCP host platforms:" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_discover_servers_backend_integration(self):
        """Test discover servers integration with environment manager."""
        # Mock packages with MCP servers
        mock_packages = [
            {'name': 'weather-toolkit', 'version': '1.0.0'},
            {'name': 'file-manager', 'version': '2.0.0'},
            {'name': 'regular-package', 'version': '1.5.0'}  # No MCP server
        ]
        
        self.mock_env_manager.list_packages.return_value = mock_packages
        
        # Mock get_package_mcp_server_config to return config for some packages
        def mock_get_config(env_manager, env_name, package_name):
            if package_name in ['weather-toolkit', 'file-manager']:
                return MCPServerConfig(
                    name=f"{package_name}-server",
                    command="python",
                    args=[f"{package_name}.py"],
                    env={}
                )
            else:
                raise ValueError(f"Package '{package_name}' has no MCP server")
        
        with patch('hatch.cli_hatch.get_package_mcp_server_config', side_effect=mock_get_config):
            with patch('builtins.print') as mock_print:
                result = handle_mcp_discover_servers(self.mock_env_manager, "test-env")
                
                self.assertEqual(result, 0)
                self.mock_env_manager.list_packages.assert_called_once_with("test-env")
                
                # Verify output contains MCP servers
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("MCP servers in environment 'test-env':" in call for call in print_calls))
                self.assertTrue(any("weather-toolkit-server:" in call for call in print_calls))
                self.assertTrue(any("file-manager-server:" in call for call in print_calls))
    
    @regression_test
    def test_discover_servers_no_mcp_packages(self):
        """Test discover servers when no packages have MCP servers."""
        mock_packages = [
            {'name': 'regular-package-1', 'version': '1.0.0'},
            {'name': 'regular-package-2', 'version': '2.0.0'}
        ]
        
        self.mock_env_manager.list_packages.return_value = mock_packages
        
        # Mock get_package_mcp_server_config to always raise ValueError
        def mock_get_config(env_manager, env_name, package_name):
            raise ValueError(f"Package '{package_name}' has no MCP server")
        
        with patch('hatch.cli_hatch.get_package_mcp_server_config', side_effect=mock_get_config):
            with patch('builtins.print') as mock_print:
                result = handle_mcp_discover_servers(self.mock_env_manager, "test-env")
                
                self.assertEqual(result, 0)
                
                # Verify appropriate message is shown
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("No MCP servers found in environment 'test-env'" in call for call in print_calls))
    
    @regression_test
    def test_discover_servers_nonexistent_environment(self):
        """Test discover servers with nonexistent environment."""
        self.mock_env_manager.environment_exists.return_value = False
        
        with patch('builtins.print') as mock_print:
            result = handle_mcp_discover_servers(self.mock_env_manager, "nonexistent-env")
            
            self.assertEqual(result, 1)
            
            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Environment 'nonexistent-env' does not exist" in call for call in print_calls))


class TestMCPListCommands(unittest.TestCase):
    """Test suite for MCP list commands."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)
        self.mock_env_manager.get_current_environment.return_value = "test-env"
        self.mock_env_manager.environment_exists.return_value = True
    
    @regression_test
    def test_list_hosts_argument_parsing(self):
        """Test argument parsing for 'hatch mcp list hosts' command."""
        test_args = ['hatch', 'mcp', 'list', 'hosts']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_list_hosts', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once()
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_list_servers_argument_parsing(self):
        """Test argument parsing for 'hatch mcp list servers' command."""
        test_args = ['hatch', 'mcp', 'list', 'servers', '--env', 'production']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_list_servers', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once()
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @integration_test(scope="component")
    def test_list_hosts_formatted_output(self):
        """Test list hosts produces properly formatted output."""
        with patch('hatch.mcp_host_config.strategies'):  # Import strategies
            with patch('hatch.cli_hatch.MCPHostRegistry') as mock_registry:
                mock_registry.detect_available_hosts.return_value = [
                    MCPHostType.CLAUDE_DESKTOP
                ]
                
                # Mock strategy responses
                def mock_get_strategy(host_type):
                    mock_strategy = MagicMock()
                    if host_type == MCPHostType.CLAUDE_DESKTOP:
                        mock_strategy.get_config_path.return_value = Path("/Users/test/.config/claude.json")
                    else:
                        mock_strategy.get_config_path.return_value = None
                    return mock_strategy
                
                mock_registry.get_strategy.side_effect = mock_get_strategy
                
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_list_hosts()
                    
                    self.assertEqual(result, 0)
                    
                    # Verify formatted table output
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("MCP host platforms status:" in call for call in print_calls))
                    self.assertTrue(any("Host Platform" in call for call in print_calls))
                    self.assertTrue(any("claude-desktop" in call for call in print_calls))
                    self.assertTrue(any("Available" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_list_servers_formatted_output(self):
        """Test list servers produces properly formatted table output."""
        # Mock packages with MCP servers
        mock_packages = [
            {'name': 'weather-toolkit', 'version': '1.0.0'},
            {'name': 'file-manager', 'version': '2.1.0'}
        ]
        
        self.mock_env_manager.list_packages.return_value = mock_packages
        
        # Mock get_package_mcp_server_config
        def mock_get_config(env_manager, env_name, package_name):
            return MCPServerConfig(
                name=f"{package_name}-server",
                command="python",
                args=[f"{package_name}.py", "--port", "8080"],
                env={}
            )
        
        with patch('hatch.cli_hatch.get_package_mcp_server_config', side_effect=mock_get_config):
            with patch('builtins.print') as mock_print:
                result = handle_mcp_list_servers(self.mock_env_manager, "test-env")
                
                self.assertEqual(result, 0)
                
                # Verify formatted table output
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("MCP servers in environment 'test-env':" in call for call in print_calls))
                self.assertTrue(any("Server Name" in call for call in print_calls))
                self.assertTrue(any("weather-toolkit-server" in call for call in print_calls))
                self.assertTrue(any("file-manager-server" in call for call in print_calls))


if __name__ == '__main__':
    unittest.main()
