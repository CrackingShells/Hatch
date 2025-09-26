"""
Test suite for MCP environment integration.

This module tests the integration between environment data and MCP host configuration
with the corrected data structure.
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch
import json

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

from test_data_utils import MCPHostConfigTestDataLoader
from hatch.mcp_host_config.models import (
    MCPServerConfig, EnvironmentData, EnvironmentPackageEntry,
    PackageHostConfiguration, MCPHostType
)
from hatch.environment_manager import HatchEnvironmentManager


class TestMCPEnvironmentIntegration(unittest.TestCase):
    """Test suite for MCP environment integration with corrected structure."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_data_loader = MCPHostConfigTestDataLoader()
    
    @regression_test
    def test_environment_data_validation_success(self):
        """Test successful environment data validation."""
        env_data = self.test_data_loader.load_corrected_environment_data("simple")
        environment = EnvironmentData(**env_data)
        
        self.assertEqual(environment.name, "test_environment")
        self.assertEqual(len(environment.packages), 1)
        
        package = environment.packages[0]
        self.assertEqual(package.name, "weather-toolkit")
        self.assertEqual(package.version, "1.0.0")
        self.assertIn("claude-desktop", package.configured_hosts)
        
        host_config = package.configured_hosts["claude-desktop"]
        self.assertIsInstance(host_config, PackageHostConfiguration)
        self.assertIsInstance(host_config.server_config, MCPServerConfig)
    
    @regression_test
    def test_environment_data_multi_host_validation(self):
        """Test environment data validation with multiple hosts."""
        env_data = self.test_data_loader.load_corrected_environment_data("multi_host")
        environment = EnvironmentData(**env_data)
        
        self.assertEqual(environment.name, "multi_host_environment")
        self.assertEqual(len(environment.packages), 1)
        
        package = environment.packages[0]
        self.assertEqual(package.name, "file-manager")
        self.assertEqual(len(package.configured_hosts), 2)
        self.assertIn("claude-desktop", package.configured_hosts)
        self.assertIn("cursor", package.configured_hosts)
        
        # Verify both host configurations
        claude_config = package.configured_hosts["claude-desktop"]
        cursor_config = package.configured_hosts["cursor"]
        
        self.assertIsInstance(claude_config, PackageHostConfiguration)
        self.assertIsInstance(cursor_config, PackageHostConfiguration)
        
        # Verify server configurations are different for different hosts
        self.assertEqual(claude_config.server_config.command, "/usr/local/bin/python")
        self.assertEqual(cursor_config.server_config.command, "python")
    
    @regression_test
    def test_package_host_configuration_validation(self):
        """Test package host configuration validation."""
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        
        host_config = PackageHostConfiguration(
            config_path="~/test/config.json",
            configured_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            last_synced=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            server_config=server_config
        )
        
        self.assertEqual(host_config.config_path, "~/test/config.json")
        self.assertIsInstance(host_config.server_config, MCPServerConfig)
        self.assertEqual(host_config.server_config.command, "python")
        self.assertEqual(len(host_config.server_config.args), 3)
    
    @regression_test
    def test_environment_package_entry_validation_success(self):
        """Test successful environment package entry validation."""
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        
        host_config = PackageHostConfiguration(
            config_path="~/test/config.json",
            configured_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            last_synced=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            server_config=server_config
        )
        
        package = EnvironmentPackageEntry(
            name="test-package",
            version="1.0.0",
            type="hatch",
            source="github:user/test-package",
            installed_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            configured_hosts={"claude-desktop": host_config}
        )
        
        self.assertEqual(package.name, "test-package")
        self.assertEqual(package.version, "1.0.0")
        self.assertEqual(package.type, "hatch")
        self.assertEqual(len(package.configured_hosts), 1)
        self.assertIn("claude-desktop", package.configured_hosts)
    
    @regression_test
    def test_environment_package_entry_invalid_host_name(self):
        """Test environment package entry validation with invalid host name."""
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        
        host_config = PackageHostConfiguration(
            config_path="~/test/config.json",
            configured_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            last_synced=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            server_config=server_config
        )
        
        with self.assertRaises(Exception) as context:
            EnvironmentPackageEntry(
                name="test-package",
                version="1.0.0",
                type="hatch",
                source="github:user/test-package",
                installed_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
                configured_hosts={"invalid-host": host_config}  # Invalid host name
            )
        
        self.assertIn("Unsupported host", str(context.exception))
    
    @regression_test
    def test_environment_package_entry_invalid_package_name(self):
        """Test environment package entry validation with invalid package name."""
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        
        host_config = PackageHostConfiguration(
            config_path="~/test/config.json",
            configured_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            last_synced=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            server_config=server_config
        )
        
        with self.assertRaises(Exception) as context:
            EnvironmentPackageEntry(
                name="invalid@package!name",  # Invalid characters
                version="1.0.0",
                type="hatch",
                source="github:user/test-package",
                installed_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
                configured_hosts={"claude-desktop": host_config}
            )
        
        self.assertIn("Invalid package name format", str(context.exception))
    
    @regression_test
    def test_environment_data_get_mcp_packages(self):
        """Test getting MCP packages from environment data."""
        env_data = self.test_data_loader.load_corrected_environment_data("multi_host")
        environment = EnvironmentData(**env_data)
        
        mcp_packages = environment.get_mcp_packages()
        
        self.assertEqual(len(mcp_packages), 1)
        self.assertEqual(mcp_packages[0].name, "file-manager")
        self.assertEqual(len(mcp_packages[0].configured_hosts), 2)
    
    @regression_test
    def test_environment_data_serialization_roundtrip(self):
        """Test environment data serialization and deserialization."""
        env_data = self.test_data_loader.load_corrected_environment_data("simple")
        environment = EnvironmentData(**env_data)
        
        # Serialize and deserialize
        serialized = environment.model_dump()
        roundtrip_environment = EnvironmentData(**serialized)
        
        self.assertEqual(environment.name, roundtrip_environment.name)
        self.assertEqual(len(environment.packages), len(roundtrip_environment.packages))
        
        original_package = environment.packages[0]
        roundtrip_package = roundtrip_environment.packages[0]
        
        self.assertEqual(original_package.name, roundtrip_package.name)
        self.assertEqual(original_package.version, roundtrip_package.version)
        self.assertEqual(len(original_package.configured_hosts), len(roundtrip_package.configured_hosts))
        
        # Verify host configuration roundtrip
        original_host_config = original_package.configured_hosts["claude-desktop"]
        roundtrip_host_config = roundtrip_package.configured_hosts["claude-desktop"]
        
        self.assertEqual(original_host_config.config_path, roundtrip_host_config.config_path)
        self.assertEqual(original_host_config.server_config.command, roundtrip_host_config.server_config.command)
    
    @regression_test
    def test_corrected_environment_structure_single_server_per_package(self):
        """Test that corrected environment structure enforces single server per package."""
        env_data = self.test_data_loader.load_corrected_environment_data("simple")
        environment = EnvironmentData(**env_data)
        
        # Verify single server per package constraint
        for package in environment.packages:
            # Each package should have one server configuration per host
            for host_name, host_config in package.configured_hosts.items():
                self.assertIsInstance(host_config, PackageHostConfiguration)
                self.assertIsInstance(host_config.server_config, MCPServerConfig)
                
                # The server configuration should be for this specific package
                # (In real usage, the server would be the package's MCP server)
    
    @regression_test
    def test_environment_data_json_serialization(self):
        """Test JSON serialization compatibility."""
        import json
        
        env_data = self.test_data_loader.load_corrected_environment_data("simple")
        environment = EnvironmentData(**env_data)
        
        # Test JSON serialization
        json_str = environment.model_dump_json()
        self.assertIsInstance(json_str, str)
        
        # Test JSON deserialization
        parsed_data = json.loads(json_str)
        roundtrip_environment = EnvironmentData(**parsed_data)
        
        self.assertEqual(environment.name, roundtrip_environment.name)
        self.assertEqual(len(environment.packages), len(roundtrip_environment.packages))


class TestMCPHostTypeIntegration(unittest.TestCase):
    """Test suite for MCP host type integration."""
    
    @regression_test
    def test_mcp_host_type_enum_values(self):
        """Test MCP host type enum values."""
        # Verify all expected host types are available
        expected_hosts = [
            "claude-desktop", "claude-code", "vscode", 
            "cursor", "lmstudio", "gemini"
        ]
        
        for host_name in expected_hosts:
            host_type = MCPHostType(host_name)
            self.assertEqual(host_type.value, host_name)
    
    @regression_test
    def test_mcp_host_type_invalid_value(self):
        """Test MCP host type with invalid value."""
        with self.assertRaises(ValueError):
            MCPHostType("invalid-host")


class TestEnvironmentManagerHostSync(unittest.TestCase):
    """Test suite for EnvironmentManager host synchronization methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)

        # Load test fixture data
        fixture_path = Path(__file__).parent / "test_data" / "fixtures" / "host_sync_scenarios.json"
        with open(fixture_path, 'r') as f:
            self.test_data = json.load(f)

    @regression_test
    def test_remove_package_host_configuration_success(self):
        """Test successful removal of host from package tracking.

        Validates:
        - Removes specified host from package's configured_hosts
        - Updates environments.json file via _save_environments()
        - Returns True when removal occurs
        - Logs successful removal with package/host details
        """
        # Setup: Environment with package having configured_hosts for multiple hosts
        env_manager = HatchEnvironmentManager()
        env_manager._environments = {
            "test-env": self.test_data["remove_server_scenario"]["before"]
        }

        with patch.object(env_manager, '_save_environments') as mock_save:
            with patch.object(env_manager, 'logger') as mock_logger:
                # Action: remove_package_host_configuration(env_name, package_name, hostname)
                result = env_manager.remove_package_host_configuration("test-env", "weather-toolkit", "cursor")

                # Assert: Host removed from package, environments.json updated, returns True
                self.assertTrue(result)
                mock_save.assert_called_once()
                mock_logger.info.assert_called_with("Removed host cursor from package weather-toolkit in env test-env")

                # Verify host was actually removed
                packages = env_manager._environments["test-env"]["packages"]
                weather_pkg = next(pkg for pkg in packages if pkg["name"] == "weather-toolkit")
                self.assertNotIn("cursor", weather_pkg["configured_hosts"])
                self.assertIn("claude-desktop", weather_pkg["configured_hosts"])

    @regression_test
    def test_remove_package_host_configuration_not_found(self):
        """Test removal when package or host not found.

        Validates:
        - Returns False when environment doesn't exist
        - Returns False when package not found in environment
        - Returns False when host not in package's configured_hosts
        - No changes to environments.json when nothing to remove
        """
        env_manager = HatchEnvironmentManager()
        env_manager._environments = {
            "test-env": self.test_data["remove_server_scenario"]["before"]
        }

        with patch.object(env_manager, '_save_environments') as mock_save:
            # Test scenarios: missing env, missing package, missing host

            # Missing environment
            result = env_manager.remove_package_host_configuration("missing-env", "weather-toolkit", "cursor")
            self.assertFalse(result)

            # Missing package
            result = env_manager.remove_package_host_configuration("test-env", "missing-package", "cursor")
            self.assertFalse(result)

            # Missing host
            result = env_manager.remove_package_host_configuration("test-env", "weather-toolkit", "missing-host")
            self.assertFalse(result)

            # Assert: No file changes when nothing to remove
            mock_save.assert_not_called()

    @regression_test
    def test_clear_host_from_all_packages_all_envs(self):
        """Test host removal across multiple environments.

        Validates:
        - Iterates through all environments in _environments
        - Removes hostname from all packages' configured_hosts
        - Returns correct count of updated package entries
        - Calls _save_environments() only once after all updates
        """
        # Setup: Multiple environments with packages using same host
        env_manager = HatchEnvironmentManager()
        env_manager._environments = self.test_data["remove_host_scenario"]["multi_environment_before"]

        with patch.object(env_manager, '_save_environments') as mock_save:
            with patch.object(env_manager, 'logger') as mock_logger:
                # Action: clear_host_from_all_packages_all_envs(hostname)
                updates_count = env_manager.clear_host_from_all_packages_all_envs("cursor")

                # Assert: Host removed from all packages, correct count returned
                self.assertEqual(updates_count, 2)  # 2 packages had cursor configured
                mock_save.assert_called_once()

                # Verify cursor was removed from all packages
                for env_name, env_data in env_manager._environments.items():
                    for pkg in env_data["packages"]:
                        configured_hosts = pkg.get("configured_hosts", {})
                        self.assertNotIn("cursor", configured_hosts)


class TestEnvironmentManagerHostSyncErrorHandling(unittest.TestCase):
    """Test suite for error handling and edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = HatchEnvironmentManager()

    @regression_test
    def test_remove_operations_exception_handling(self):
        """Test exception handling in remove operations.

        Validates:
        - Catches and logs exceptions during removal operations
        - Returns False/0 on exceptions rather than crashing
        - Provides meaningful error messages in logs
        - Maintains environment file integrity on errors
        """
        # Setup: Mock scenarios that raise exceptions
        # Create environment with package that has the host, so _save_environments will be called
        self.env_manager._environments = {
            "test-env": {
                "packages": [
                    {
                        "name": "test-pkg",
                        "configured_hosts": {
                            "test-host": {"config_path": "test"}
                        }
                    }
                ]
            }
        }

        with patch.object(self.env_manager, '_save_environments', side_effect=Exception("File error")):
            with patch.object(self.env_manager, 'logger') as mock_logger:
                # Action: Call remove methods with exception-inducing conditions
                result = self.env_manager.remove_package_host_configuration("test-env", "test-pkg", "test-host")

                # Assert: Graceful error handling, no crashes, appropriate returns
                self.assertFalse(result)
                mock_logger.error.assert_called()


class TestCLIHostMutationSync(unittest.TestCase):
    """Test suite for CLI integration with environment tracking."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_env_manager = MagicMock(spec=HatchEnvironmentManager)

    @integration_test(scope="component")
    def test_remove_server_updates_environment(self):
        """Test that remove server updates current environment tracking.

        Validates:
        - CLI remove server calls environment manager update method
        - Updates only current environment (not all environments)
        - Passes correct parameters (env_name, server_name, hostname)
        - Maintains existing CLI behavior and exit codes
        """
        from hatch.cli_hatch import handle_mcp_remove_server
        from hatch.mcp_host_config import MCPHostConfigurationManager

        # Setup: Environment with server configured on host
        self.mock_env_manager.get_current_environment.return_value = "test-env"

        with patch.object(MCPHostConfigurationManager, 'remove_server') as mock_remove:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = None
            mock_remove.return_value = mock_result

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print'):
                    # Action: hatch mcp remove server <server> --host <host>
                    result = handle_mcp_remove_server(
                        self.mock_env_manager, "test-server", "claude-desktop",
                        None, False, False, True
                    )

                    # Assert: Environment manager method called with correct parameters
                    self.mock_env_manager.get_current_environment.assert_called_once()
                    self.mock_env_manager.remove_package_host_configuration.assert_called_with(
                        "test-env", "test-server", "claude-desktop"
                    )

                    # Assert: Success exit code
                    self.assertEqual(result, 0)

    @integration_test(scope="component")
    def test_remove_host_updates_all_environments(self):
        """Test that remove host updates all environment tracking.

        Validates:
        - CLI remove host calls global environment update method
        - Updates ALL environments (not just current)
        - Passes correct hostname parameter
        - Reports number of updates performed to user
        """
        from hatch.cli_hatch import handle_mcp_remove_host
        from hatch.mcp_host_config import MCPHostConfigurationManager

        # Setup: Multiple environments with packages using the host
        with patch.object(MCPHostConfigurationManager, 'remove_host_configuration') as mock_remove:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = None
            mock_remove.return_value = mock_result

            self.mock_env_manager.clear_host_from_all_packages_all_envs.return_value = 3

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print') as mock_print:
                    # Action: hatch mcp remove host <host>
                    result = handle_mcp_remove_host(
                        self.mock_env_manager, "cursor", False, False, True
                    )

                    # Assert: Global environment update method called
                    self.mock_env_manager.clear_host_from_all_packages_all_envs.assert_called_with("cursor")

                    # Assert: User informed of update count
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    output = ' '.join(print_calls)
                    self.assertIn("Updated 3 package entries across environments", output)

                    # Assert: Success exit code
                    self.assertEqual(result, 0)


if __name__ == '__main__':
    unittest.main()
