"""
Kiro MCP Host Strategy Tests

Tests for KiroHostStrategy implementation including path resolution,
configuration read/write, and host detection.
"""

import unittest
import json
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from wobble.decorators import regression_test

from hatch.mcp_host_config.strategies import KiroHostStrategy
from hatch.mcp_host_config.models import MCPServerConfig, HostConfiguration

# Import test data loader from local tests module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from test_data_utils import MCPHostConfigTestDataLoader


class TestKiroHostStrategy(unittest.TestCase):
    """Test suite for KiroHostStrategy implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.strategy = KiroHostStrategy()
        self.test_data_loader = MCPHostConfigTestDataLoader()
    
    @regression_test
    def test_kiro_config_path_resolution(self):
        """Test Kiro configuration path resolution."""
        config_path = self.strategy.get_config_path()
        
        # Verify path structure (use normalized path for cross-platform compatibility)
        self.assertIsNotNone(config_path)
        normalized_path = str(config_path).replace('\\', '/')
        self.assertTrue(normalized_path.endswith('.kiro/settings/mcp.json'))
        self.assertEqual(config_path.name, 'mcp.json')
    
    @regression_test
    def test_kiro_config_key(self):
        """Test Kiro configuration key."""
        config_key = self.strategy.get_config_key()
        self.assertEqual(config_key, "mcpServers")
    
    @regression_test
    def test_kiro_server_config_validation(self):
        """Test Kiro server configuration validation."""
        # Test local server validation
        local_config = MCPServerConfig(
            command="auggie",
            args=["--mcp"]
        )
        self.assertTrue(self.strategy.validate_server_config(local_config))
        
        # Test remote server validation
        remote_config = MCPServerConfig(
            url="https://api.example.com/mcp"
        )
        self.assertTrue(self.strategy.validate_server_config(remote_config))
        
        # Test invalid configuration (should raise ValidationError during creation)
        with self.assertRaises(Exception):  # Pydantic ValidationError
            invalid_config = MCPServerConfig()
            self.strategy.validate_server_config(invalid_config)
    
    @patch('pathlib.Path.exists')
    @regression_test
    def test_kiro_host_availability_detection(self, mock_exists):
        """Test Kiro host availability detection."""
        # Test when Kiro directory exists
        mock_exists.return_value = True
        self.assertTrue(self.strategy.is_host_available())
        
        # Test when Kiro directory doesn't exist
        mock_exists.return_value = False
        self.assertFalse(self.strategy.is_host_available())
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('json.load')
    @regression_test
    def test_kiro_read_configuration_success(self, mock_json_load, mock_exists, mock_file):
        """Test successful Kiro configuration reading."""
        # Mock file exists and JSON content
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "mcpServers": {
                "augment": {
                    "command": "auggie",
                    "args": ["--mcp", "-m", "default"],
                    "autoApprove": ["codebase-retrieval"]
                }
            }
        }
        
        config = self.strategy.read_configuration()
        
        # Verify configuration structure
        self.assertIsInstance(config, HostConfiguration)
        self.assertIn("augment", config.servers)
        
        server = config.servers["augment"]
        self.assertEqual(server.command, "auggie")
        self.assertEqual(len(server.args), 3)
    
    @patch('pathlib.Path.exists')
    @regression_test
    def test_kiro_read_configuration_file_not_exists(self, mock_exists):
        """Test Kiro configuration reading when file doesn't exist."""
        mock_exists.return_value = False
        
        config = self.strategy.read_configuration()
        
        # Should return empty configuration
        self.assertIsInstance(config, HostConfiguration)
        self.assertEqual(len(config.servers), 0)
    
    @patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager')
    @patch('hatch.mcp_host_config.strategies.AtomicFileOperations')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('json.load')
    @regression_test
    def test_kiro_write_configuration_success(self, mock_json_load, mock_mkdir, 
                                            mock_exists, mock_file, mock_atomic_ops_class, mock_backup_manager_class):
        """Test successful Kiro configuration writing."""
        # Mock existing file with other settings
        mock_exists.return_value = True
        mock_json_load.return_value = {
            "otherSettings": {"theme": "dark"},
            "mcpServers": {}
        }
        
        # Mock backup and atomic operations
        mock_backup_manager = MagicMock()
        mock_backup_manager_class.return_value = mock_backup_manager
        
        mock_atomic_ops = MagicMock()
        mock_atomic_ops_class.return_value = mock_atomic_ops
        
        # Create test configuration
        server_config = MCPServerConfig(
            command="auggie",
            args=["--mcp"]
        )
        config = HostConfiguration(servers={"test-server": server_config})
        
        result = self.strategy.write_configuration(config)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify atomic write was called
        mock_atomic_ops.atomic_write_with_backup.assert_called_once()
        
        # Verify configuration structure in the call
        call_args = mock_atomic_ops.atomic_write_with_backup.call_args
        written_data = call_args[1]['data']  # keyword argument 'data'
        self.assertIn("otherSettings", written_data)  # Preserved
        self.assertIn("mcpServers", written_data)     # Updated
        self.assertIn("test-server", written_data["mcpServers"])
    
    @patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager')
    @patch('hatch.mcp_host_config.strategies.AtomicFileOperations')
    @patch('builtins.open', new_callable=mock_open)
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @regression_test
    def test_kiro_write_configuration_new_file(self, mock_mkdir, mock_exists, 
                                             mock_file, mock_atomic_ops_class, mock_backup_manager_class):
        """Test Kiro configuration writing when file doesn't exist."""
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        # Mock backup and atomic operations
        mock_backup_manager = MagicMock()
        mock_backup_manager_class.return_value = mock_backup_manager
        
        mock_atomic_ops = MagicMock()
        mock_atomic_ops_class.return_value = mock_atomic_ops
        
        # Create test configuration
        server_config = MCPServerConfig(
            command="auggie",
            args=["--mcp"]
        )
        config = HostConfiguration(servers={"new-server": server_config})
        
        result = self.strategy.write_configuration(config)
        
        # Verify success
        self.assertTrue(result)
        
        # Verify directory creation was attempted
        mock_mkdir.assert_called_once()
        
        # Verify atomic write was called
        mock_atomic_ops.atomic_write_with_backup.assert_called_once()
        
        # Verify configuration structure
        call_args = mock_atomic_ops.atomic_write_with_backup.call_args
        written_data = call_args[1]['data']  # keyword argument 'data'
        self.assertIn("mcpServers", written_data)
        self.assertIn("new-server", written_data["mcpServers"])


if __name__ == '__main__':
    unittest.main()