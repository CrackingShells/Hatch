"""
Codex MCP Host Strategy Tests

Tests for CodexHostStrategy implementation including path resolution,
configuration read/write, TOML handling, and host detection.
"""

import unittest
import tempfile
import tomllib
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from wobble.decorators import regression_test

from hatch.mcp_host_config.strategies import CodexHostStrategy
from hatch.mcp_host_config.models import MCPServerConfig, HostConfiguration

# Import test data loader from local tests module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_data_utils import MCPHostConfigTestDataLoader


class TestCodexHostStrategy(unittest.TestCase):
    """Test suite for CodexHostStrategy implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.strategy = CodexHostStrategy()
        self.test_data_loader = MCPHostConfigTestDataLoader()
    
    @regression_test
    def test_codex_config_path_resolution(self):
        """Test Codex configuration path resolution."""
        config_path = self.strategy.get_config_path()
        
        # Verify path structure (use normalized path for cross-platform compatibility)
        self.assertIsNotNone(config_path)
        normalized_path = str(config_path).replace('\\', '/')
        self.assertTrue(normalized_path.endswith('.codex/config.toml'))
        self.assertEqual(config_path.name, 'config.toml')
        self.assertEqual(config_path.suffix, '.toml')  # Verify TOML extension
    
    @regression_test
    def test_codex_config_key(self):
        """Test Codex configuration key."""
        config_key = self.strategy.get_config_key()
        # Codex uses underscore, not camelCase
        self.assertEqual(config_key, "mcp_servers")
        self.assertNotEqual(config_key, "mcpServers")  # Verify different from other hosts
    
    @regression_test
    def test_codex_server_config_validation_stdio(self):
        """Test Codex STDIO server configuration validation."""
        # Test local server validation
        local_config = MCPServerConfig(
            command="npx",
            args=["-y", "package"]
        )
        self.assertTrue(self.strategy.validate_server_config(local_config))
    
    @regression_test
    def test_codex_server_config_validation_http(self):
        """Test Codex HTTP server configuration validation."""
        # Test remote server validation
        remote_config = MCPServerConfig(
            url="https://api.example.com/mcp"
        )
        self.assertTrue(self.strategy.validate_server_config(remote_config))
    
    @patch('pathlib.Path.exists')
    @regression_test
    def test_codex_host_availability_detection(self, mock_exists):
        """Test Codex host availability detection."""
        # Test when Codex directory exists
        mock_exists.return_value = True
        self.assertTrue(self.strategy.is_host_available())
        
        # Test when Codex directory doesn't exist
        mock_exists.return_value = False
        self.assertFalse(self.strategy.is_host_available())
    
    @regression_test
    def test_codex_read_configuration_success(self):
        """Test successful Codex TOML configuration reading."""
        # Load test data
        test_toml_path = Path(__file__).parent.parent / "test_data" / "codex" / "valid_config.toml"
        
        with patch.object(self.strategy, 'get_config_path', return_value=test_toml_path):
            config = self.strategy.read_configuration()
            
            # Verify configuration was read
            self.assertIsInstance(config, HostConfiguration)
            self.assertIn('context7', config.servers)
            
            # Verify server details
            server = config.servers['context7']
            self.assertEqual(server.command, 'npx')
            self.assertEqual(server.args, ['-y', '@upstash/context7-mcp'])
            
            # Verify nested env section was parsed correctly
            self.assertIsNotNone(server.env)
            self.assertEqual(server.env.get('MY_VAR'), 'value')
    
    @regression_test
    def test_codex_read_configuration_file_not_exists(self):
        """Test Codex configuration reading when file doesn't exist."""
        non_existent_path = Path("/non/existent/path/config.toml")
        
        with patch.object(self.strategy, 'get_config_path', return_value=non_existent_path):
            config = self.strategy.read_configuration()
            
            # Should return empty configuration without error
            self.assertIsInstance(config, HostConfiguration)
            self.assertEqual(len(config.servers), 0)
    
    @regression_test
    def test_codex_write_configuration_preserves_features(self):
        """Test that write_configuration preserves [features] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            
            # Create initial config with features section
            initial_toml = """[features]
rmcp_client = true

[mcp_servers.existing]
command = "old-command"
"""
            config_path.write_text(initial_toml)
            
            # Create new configuration to write
            new_config = HostConfiguration(servers={
                'new-server': MCPServerConfig(
                    command='new-command',
                    args=['--test']
                )
            })
            
            # Write configuration
            with patch.object(self.strategy, 'get_config_path', return_value=config_path):
                success = self.strategy.write_configuration(new_config, no_backup=True)
                self.assertTrue(success)
            
            # Read back and verify features section preserved
            with open(config_path, 'rb') as f:
                result_data = tomllib.load(f)
            
            # Verify features section preserved
            self.assertIn('features', result_data)
            self.assertTrue(result_data['features'].get('rmcp_client'))
            
            # Verify new server added
            self.assertIn('mcp_servers', result_data)
            self.assertIn('new-server', result_data['mcp_servers'])
            self.assertEqual(result_data['mcp_servers']['new-server']['command'], 'new-command')


if __name__ == '__main__':
    unittest.main()

