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
import json


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
        """Test list hosts produces properly formatted output for environment-scoped listing."""
        # Setup mock environment manager with test data
        mock_env_manager = MagicMock(spec=HatchEnvironmentManager)
        mock_env_manager.get_current_environment.return_value = "test-env"
        mock_env_manager.environment_exists.return_value = True
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "weather-toolkit",
                    "configured_hosts": {
                        "claude-desktop": {
                            "config_path": "~/.claude/config.json",
                            "configured_at": "2025-09-25T10:00:00"
                        }
                    }
                }
            ]
        }

        with patch('builtins.print') as mock_print:
            result = handle_mcp_list_hosts(mock_env_manager, None, False)

            self.assertEqual(result, 0)

            # Verify environment-scoped output format
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            self.assertIn("Configured hosts for environment 'test-env':", output)
            self.assertIn("claude-desktop (1 packages)", output)
    
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
                print_calls = []
                for call in mock_print.call_args_list:
                    if call[0]:  # Check if args exist
                        print_calls.append(call[0][0])

                self.assertTrue(any("MCP servers in environment 'test-env':" in call for call in print_calls))
                self.assertTrue(any("Server Name" in call for call in print_calls))
                self.assertTrue(any("weather-toolkit-server" in call for call in print_calls))
                self.assertTrue(any("file-manager-server" in call for call in print_calls))


class TestMCPListHostsEnvironmentScoped(unittest.TestCase):
    """Test suite for environment-scoped list hosts functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)
        self.mock_env_manager.get_current_environment.return_value = "test-env"
        self.mock_env_manager.environment_exists.return_value = True
        # Configure the mock to have the get_environment_data method
        self.mock_env_manager.get_environment_data = MagicMock()

        # Load test fixture data
        fixture_path = Path(__file__).parent / "test_data" / "fixtures" / "environment_host_configs.json"
        with open(fixture_path, 'r') as f:
            self.test_data = json.load(f)

    @regression_test
    def test_list_hosts_environment_scoped_basic(self):
        """Test list hosts shows only hosts configured in specified environment.

        Validates:
        - Reads from environment data (not system detection)
        - Shows only hosts with configured packages in target environment
        - Displays host count information correctly
        - Uses environment manager for data source
        """
        # Setup: Mock environment with 2 packages using different hosts
        self.mock_env_manager.get_environment_data.return_value = self.test_data["multi_host_environment"]

        with patch('builtins.print') as mock_print:
            # Action: Call handle_mcp_list_hosts with env_manager and env_name
            result = handle_mcp_list_hosts(self.mock_env_manager, "test-env", False)

            # Assert: Success exit code
            self.assertEqual(result, 0)

            # Assert: Environment manager methods called correctly
            self.mock_env_manager.environment_exists.assert_called_with("test-env")
            self.mock_env_manager.get_environment_data.assert_called_with("test-env")

            # Assert: Output contains both hosts with correct package counts
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = ' '.join(print_calls)

            self.assertIn("Configured hosts for environment 'test-env':", output)
            self.assertIn("claude-desktop (2 packages)", output)
            self.assertIn("cursor (1 packages)", output)

    @regression_test
    def test_list_hosts_empty_environment(self):
        """Test list hosts with environment containing no packages.

        Validates:
        - Handles empty environment gracefully
        - Displays appropriate message for no configured hosts
        - Returns success exit code (0)
        - Does not attempt system detection
        """
        # Setup: Mock environment with no packages
        self.mock_env_manager.get_environment_data.return_value = self.test_data["empty_environment"]

        with patch('builtins.print') as mock_print:
            # Action: Call handle_mcp_list_hosts
            result = handle_mcp_list_hosts(self.mock_env_manager, "empty-env", False)

            # Assert: Success exit code
            self.assertEqual(result, 0)

            # Assert: Appropriate message displayed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            self.assertIn("No configured hosts for environment 'empty-env'", output)

    @regression_test
    def test_list_hosts_packages_no_host_tracking(self):
        """Test list hosts with packages that have no configured_hosts data.

        Validates:
        - Handles packages without configured_hosts gracefully
        - Displays appropriate message for no host configurations
        - Maintains backward compatibility with older environment data
        """
        # Setup: Mock environment with packages lacking configured_hosts
        self.mock_env_manager.get_environment_data.return_value = self.test_data["packages_no_host_tracking"]

        with patch('builtins.print') as mock_print:
            # Action: Call handle_mcp_list_hosts
            result = handle_mcp_list_hosts(self.mock_env_manager, "legacy-env", False)

            # Assert: Success exit code
            self.assertEqual(result, 0)

            # Assert: Handles missing configured_hosts keys without error
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            self.assertIn("No configured hosts for environment 'legacy-env'", output)


class TestMCPListHostsCLIIntegration(unittest.TestCase):
    """Test suite for CLI argument processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)
        self.mock_env_manager.get_current_environment.return_value = "current-env"
        self.mock_env_manager.environment_exists.return_value = True
        # Configure the mock to have the get_environment_data method
        self.mock_env_manager.get_environment_data = MagicMock(return_value={"packages": []})

    @regression_test
    def test_list_hosts_env_argument_parsing(self):
        """Test --env argument processing for list hosts command.

        Validates:
        - Accepts --env argument correctly
        - Passes environment name to handler function
        - Uses current environment when --env not specified
        - Validates environment exists before processing
        """
        # Test case 1: hatch mcp list hosts --env project-alpha
        with patch('builtins.print'):
            result = handle_mcp_list_hosts(self.mock_env_manager, "project-alpha", False)
            self.assertEqual(result, 0)
            self.mock_env_manager.environment_exists.assert_called_with("project-alpha")
            self.mock_env_manager.get_environment_data.assert_called_with("project-alpha")

        # Reset mocks
        self.mock_env_manager.reset_mock()

        # Test case 2: hatch mcp list hosts (uses current environment)
        with patch('builtins.print'):
            result = handle_mcp_list_hosts(self.mock_env_manager, None, False)
            self.assertEqual(result, 0)
            self.mock_env_manager.get_current_environment.assert_called_once()
            self.mock_env_manager.environment_exists.assert_called_with("current-env")

    @regression_test
    def test_list_hosts_detailed_flag_parsing(self):
        """Test --detailed flag processing for list hosts command.

        Validates:
        - Accepts --detailed flag correctly
        - Passes detailed flag to handler function
        - Default behavior when flag not specified
        """
        # Load test data with detailed information
        fixture_path = Path(__file__).parent / "test_data" / "fixtures" / "environment_host_configs.json"
        with open(fixture_path, 'r') as f:
            test_data = json.load(f)

        self.mock_env_manager.get_environment_data.return_value = test_data["single_host_environment"]

        with patch('builtins.print') as mock_print:
            # Test: hatch mcp list hosts --detailed
            result = handle_mcp_list_hosts(self.mock_env_manager, "test-env", True)

            # Assert: detailed=True passed to handler
            self.assertEqual(result, 0)

            # Assert: Detailed output includes config paths and timestamps
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            self.assertIn("Config path:", output)
            self.assertIn("Configured at:", output)


class TestMCPListHostsEnvironmentManagerIntegration(unittest.TestCase):
    """Test suite for environment manager integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)
        # Configure the mock to have the get_environment_data method
        self.mock_env_manager.get_environment_data = MagicMock()

    @integration_test(scope="component")
    def test_list_hosts_reads_environment_data(self):
        """Test list hosts reads actual environment data via environment manager.

        Validates:
        - Calls environment manager methods correctly
        - Processes configured_hosts data from packages
        - Aggregates hosts across multiple packages
        - Handles environment resolution (current vs specified)
        """
        # Setup: Real environment manager with test data
        fixture_path = Path(__file__).parent / "test_data" / "fixtures" / "environment_host_configs.json"
        with open(fixture_path, 'r') as f:
            test_data = json.load(f)

        self.mock_env_manager.get_current_environment.return_value = "test-env"
        self.mock_env_manager.environment_exists.return_value = True
        self.mock_env_manager.get_environment_data.return_value = test_data["multi_host_environment"]

        with patch('builtins.print'):
            # Action: Call list hosts functionality
            result = handle_mcp_list_hosts(self.mock_env_manager, None, False)

            # Assert: Correct environment manager method calls
            self.mock_env_manager.get_current_environment.assert_called_once()
            self.mock_env_manager.environment_exists.assert_called_with("test-env")
            self.mock_env_manager.get_environment_data.assert_called_with("test-env")

            # Assert: Success result
            self.assertEqual(result, 0)

    @integration_test(scope="component")
    def test_list_hosts_environment_validation(self):
        """Test list hosts validates environment existence.

        Validates:
        - Checks environment exists before processing
        - Returns appropriate error for non-existent environment
        - Provides helpful error message with available environments
        """
        # Setup: Environment manager with known environments
        self.mock_env_manager.environment_exists.return_value = False
        self.mock_env_manager.list_environments.return_value = ["env1", "env2", "env3"]

        with patch('builtins.print') as mock_print:
            # Action: Call list hosts with non-existent environment
            result = handle_mcp_list_hosts(self.mock_env_manager, "non-existent", False)

            # Assert: Error message includes available environments
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = ' '.join(print_calls)
            self.assertIn("Environment 'non-existent' does not exist", output)
            self.assertIn("Available environments: env1, env2, env3", output)

            # Assert: Non-zero exit code
            self.assertEqual(result, 1)


class TestMCPDiscoverHostsUnchanged(unittest.TestCase):
    """Test suite for discover hosts unchanged behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)

    @regression_test
    def test_discover_hosts_system_detection_unchanged(self):
        """Test discover hosts continues to use system detection.

        Validates:
        - Uses host strategy detection (not environment data)
        - Shows availability status for detected hosts
        - Behavior unchanged from previous implementation
        - No environment dependency
        """
        # Setup: Mock host strategies with available hosts
        with patch('hatch.mcp_host_config.strategies'):  # Import strategies
            with patch('hatch.cli_hatch.MCPHostRegistry') as mock_registry:
                mock_registry.detect_available_hosts.return_value = [
                    MCPHostType.CLAUDE_DESKTOP,
                    MCPHostType.CURSOR
                ]

                # Mock strategy for each host type
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = Path("~/.claude/config.json")
                mock_registry.get_strategy.return_value = mock_strategy

                with patch('builtins.print') as mock_print:
                    # Action: Call handle_mcp_discover_hosts
                    result = handle_mcp_discover_hosts()

                    # Assert: Host strategy detection called
                    mock_registry.detect_available_hosts.assert_called_once()

                    # Assert: No environment manager calls (discover hosts is environment-independent)
                    # Note: discover hosts doesn't use environment manager at all

                    # Assert: Availability-focused output format
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    output = ' '.join(print_calls)
                    self.assertIn("Available MCP host platforms:", output)
                    self.assertIn("Available", output)

                    # Assert: Success result
                    self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
