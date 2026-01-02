"""
Test suite for MCP host configuration manager.

This module tests the core configuration manager with consolidated models
and integration with backup system.
"""

import unittest
import sys
from pathlib import Path
import tempfile
import json
import os

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
from hatch.mcp_host_config.host_management import MCPHostConfigurationManager, MCPHostRegistry, register_host_strategy
from hatch.mcp_host_config.models import MCPHostType, MCPServerConfig, HostConfiguration, ConfigurationResult, SyncResult
from hatch.mcp_host_config.strategies import MCPHostStrategy


class TestMCPHostConfigurationManager(unittest.TestCase):
    """Test suite for MCP host configuration manager."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_data_loader = MCPHostConfigTestDataLoader()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_config_path = Path(self.temp_dir) / "test_config.json"
        
        # Clear registry before each test
        MCPHostRegistry._strategies.clear()
        MCPHostRegistry._instances.clear()
        
        # Store temp_config_path for strategy access
        temp_config_path = self.temp_config_path

        # Register test strategy
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class TestStrategy(MCPHostStrategy):
            def get_config_path(self):
                return temp_config_path

            def is_host_available(self):
                return True

            def read_configuration(self):
                if temp_config_path.exists():
                    with open(temp_config_path, 'r') as f:
                        data = json.load(f)

                    servers = {}
                    if "mcpServers" in data:
                        for name, config in data["mcpServers"].items():
                            servers[name] = MCPServerConfig(**config)

                    return HostConfiguration(servers=servers)
                else:
                    return HostConfiguration(servers={})

            def write_configuration(self, config, no_backup=False):
                try:
                    # Convert MCPServerConfig objects to dict
                    servers_dict = {}
                    for name, server_config in config.servers.items():
                        servers_dict[name] = server_config.model_dump(exclude_none=True)

                    # Create configuration data
                    config_data = {"mcpServers": servers_dict}

                    # Write to file
                    with open(temp_config_path, 'w') as f:
                        json.dump(config_data, f, indent=2)

                    return True
                except Exception:
                    return False

            def validate_server_config(self, server_config):
                return True
        
        self.manager = MCPHostConfigurationManager()
        self.temp_config_path = self.temp_config_path
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up temp files
        if self.temp_config_path.exists():
            self.temp_config_path.unlink()
        os.rmdir(self.temp_dir)
        
        # Clear registry after each test
        MCPHostRegistry._strategies.clear()
        MCPHostRegistry._instances.clear()
    
    @regression_test
    def test_configure_server_success(self):
        """Test successful server configuration."""
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        # Add name attribute for the manager to use
        server_config.name = "test_server"

        result = self.manager.configure_server(
            server_config=server_config,
            hostname="claude-desktop"
        )

        self.assertIsInstance(result, ConfigurationResult)
        if not result.success:
            print(f"Configuration failed: {result.error_message}")
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)
        self.assertEqual(result.hostname, "claude-desktop")
        self.assertEqual(result.server_name, "test_server")

        # Verify configuration was written
        self.assertTrue(self.temp_config_path.exists())

        # Verify configuration content
        with open(self.temp_config_path, 'r') as f:
            config_data = json.load(f)

        self.assertIn("mcpServers", config_data)
        self.assertIn("test_server", config_data["mcpServers"])
        self.assertEqual(config_data["mcpServers"]["test_server"]["command"], "python")
    
    @regression_test
    def test_configure_server_unknown_host_type(self):
        """Test configuration with unknown host type."""
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        server_config.name = "test_server"

        # Clear registry to simulate unknown host type
        MCPHostRegistry._strategies.clear()

        result = self.manager.configure_server(
            server_config=server_config,
            hostname="claude-desktop"
        )

        self.assertIsInstance(result, ConfigurationResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Unknown host type", result.error_message)
    
    @regression_test
    def test_configure_server_validation_failure(self):
        """Test configuration with validation failure."""
        # Create server config that will fail validation at the strategy level
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        server_config.name = "test_server"

        # Override the test strategy to always fail validation
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class FailingValidationStrategy(MCPHostStrategy):
            def get_config_path(self):
                return self.temp_config_path

            def is_host_available(self):
                return True

            def read_configuration(self):
                return HostConfiguration(servers={})

            def write_configuration(self, config, no_backup=False):
                return True

            def validate_server_config(self, server_config):
                return False  # Always fail validation

        result = self.manager.configure_server(
            server_config=server_config,
            hostname="claude-desktop"
        )

        self.assertIsInstance(result, ConfigurationResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Server configuration invalid", result.error_message)
    
    @regression_test
    def test_remove_server_success(self):
        """Test successful server removal."""
        # First configure a server
        server_config_data = self.test_data_loader.load_mcp_server_config("local")
        server_config = MCPServerConfig(**server_config_data)
        server_config.name = "test_server"

        self.manager.configure_server(
            server_config=server_config,
            hostname="claude-desktop"
        )

        # Verify server exists
        with open(self.temp_config_path, 'r') as f:
            config_data = json.load(f)
        self.assertIn("test_server", config_data["mcpServers"])

        # Remove server
        result = self.manager.remove_server(
            server_name="test_server",
            hostname="claude-desktop"
        )

        self.assertIsInstance(result, ConfigurationResult)
        self.assertTrue(result.success)
        self.assertIsNone(result.error_message)

        # Verify server was removed
        with open(self.temp_config_path, 'r') as f:
            config_data = json.load(f)
        self.assertNotIn("test_server", config_data["mcpServers"])
    
    @regression_test
    def test_remove_server_not_found(self):
        """Test removing non-existent server."""
        result = self.manager.remove_server(
            server_name="nonexistent_server",
            hostname="claude-desktop"
        )

        self.assertIsInstance(result, ConfigurationResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Server 'nonexistent_server' not found", result.error_message)
    
    @regression_test
    def test_sync_environment_to_hosts_success(self):
        """Test successful environment synchronization."""
        from hatch.mcp_host_config.models import EnvironmentData, EnvironmentPackageEntry, PackageHostConfiguration
        from datetime import datetime

        # Create test environment data
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

        env_data = EnvironmentData(
            name="test_env",
            description="Test environment",
            created_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            packages=[package]
        )

        # Sync environment to hosts
        result = self.manager.sync_environment_to_hosts(
            env_data=env_data,
            target_hosts=["claude-desktop"]
        )

        self.assertIsInstance(result, SyncResult)
        self.assertTrue(result.success)
        self.assertEqual(result.servers_synced, 1)
        self.assertEqual(result.hosts_updated, 1)
        self.assertEqual(len(result.results), 1)

        # Verify configuration was written
        self.assertTrue(self.temp_config_path.exists())

        # Verify configuration content
        with open(self.temp_config_path, 'r') as f:
            config_data = json.load(f)

        self.assertIn("mcpServers", config_data)
        self.assertIn("test-package", config_data["mcpServers"])
        self.assertEqual(config_data["mcpServers"]["test-package"]["command"], "python")

    @regression_test
    def test_sync_environment_to_hosts_no_servers(self):
        """Test environment synchronization with no servers."""
        from hatch.mcp_host_config.models import EnvironmentData
        from datetime import datetime

        # Create empty environment data
        env_data = EnvironmentData(
            name="empty_env",
            description="Empty environment",
            created_at=datetime.fromisoformat("2025-09-21T10:00:00.000000"),
            packages=[]
        )

        # Sync environment to hosts
        result = self.manager.sync_environment_to_hosts(
            env_data=env_data,
            target_hosts=["claude-desktop"]
        )

        self.assertIsInstance(result, SyncResult)
        self.assertTrue(result.success)  # Success even with no servers
        self.assertEqual(result.servers_synced, 0)
        self.assertEqual(result.hosts_updated, 1)
        self.assertEqual(len(result.results), 1)

        # Verify result message
        self.assertEqual(result.results[0].error_message, "No servers to sync")


if __name__ == '__main__':
    unittest.main()
