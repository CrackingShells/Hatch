"""
Test suite for MCP environment integration.

This module tests the integration between environment data and MCP host configuration
with the corrected data structure.
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

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


if __name__ == '__main__':
    unittest.main()
