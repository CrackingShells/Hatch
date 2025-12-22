"""Tests for Kiro MCP backup integration.

This module tests the integration between KiroHostStrategy and the backup system,
ensuring that Kiro configurations are properly backed up during write operations.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from wobble.decorators import regression_test

from hatch.mcp_host_config.strategies import KiroHostStrategy
from hatch.mcp_host_config.models import HostConfiguration, MCPServerConfig
from hatch.mcp_host_config.backup import MCPHostConfigBackupManager, BackupResult


class TestKiroBackupIntegration(unittest.TestCase):
    """Test Kiro backup integration with host strategy."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_kiro_backup_"))
        self.config_dir = self.temp_dir / ".kiro" / "settings"
        self.config_dir.mkdir(parents=True)
        self.config_file = self.config_dir / "mcp.json"
        
        self.backup_dir = self.temp_dir / "backups"
        self.backup_manager = MCPHostConfigBackupManager(backup_root=self.backup_dir)
        
        self.strategy = KiroHostStrategy()
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @regression_test
    def test_write_configuration_creates_backup_by_default(self):
        """Test that write_configuration creates backup by default when file exists."""
        # Create initial configuration
        initial_config = {
            "mcpServers": {
                "existing-server": {
                    "command": "uvx",
                    "args": ["existing-package"]
                }
            },
            "otherSettings": {
                "theme": "dark"
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(initial_config, f, indent=2)
        
        # Create new configuration to write
        server_config = MCPServerConfig(
            command="uvx",
            args=["new-package"]
        )
        host_config = HostConfiguration(servers={"new-server": server_config})
        
        # Mock the strategy's get_config_path to return our test file
        # Mock the backup manager creation to use our test backup manager
        with patch.object(self.strategy, 'get_config_path', return_value=self.config_file), \
             patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager', return_value=self.backup_manager):
            # Write configuration (should create backup)
            result = self.strategy.write_configuration(host_config, no_backup=False)
        
        # Verify write succeeded
        self.assertTrue(result)
        
        # Verify backup was created
        backups = self.backup_manager.list_backups("kiro")
        self.assertEqual(len(backups), 1)
        
        # Verify backup contains original content
        backup_content = json.loads(backups[0].file_path.read_text())
        self.assertEqual(backup_content, initial_config)
        
        # Verify new configuration was written
        new_content = json.loads(self.config_file.read_text())
        self.assertIn("new-server", new_content["mcpServers"])
        self.assertEqual(new_content["otherSettings"], {"theme": "dark"})  # Preserved
    
    @regression_test
    def test_write_configuration_skips_backup_when_requested(self):
        """Test that write_configuration skips backup when no_backup=True."""
        # Create initial configuration
        initial_config = {
            "mcpServers": {
                "existing-server": {
                    "command": "uvx",
                    "args": ["existing-package"]
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(initial_config, f, indent=2)
        
        # Create new configuration to write
        server_config = MCPServerConfig(
            command="uvx",
            args=["new-package"]
        )
        host_config = HostConfiguration(servers={"new-server": server_config})
        
        # Mock the strategy's get_config_path to return our test file
        # Mock the backup manager creation to use our test backup manager
        with patch.object(self.strategy, 'get_config_path', return_value=self.config_file), \
             patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager', return_value=self.backup_manager):
            # Write configuration with no_backup=True
            result = self.strategy.write_configuration(host_config, no_backup=True)
        
        # Verify write succeeded
        self.assertTrue(result)
        
        # Verify no backup was created
        backups = self.backup_manager.list_backups("kiro")
        self.assertEqual(len(backups), 0)
        
        # Verify new configuration was written
        new_content = json.loads(self.config_file.read_text())
        self.assertIn("new-server", new_content["mcpServers"])
    
    @regression_test
    def test_write_configuration_no_backup_for_new_file(self):
        """Test that no backup is created when writing to a new file."""
        # Ensure config file doesn't exist
        self.assertFalse(self.config_file.exists())
        
        # Create configuration to write
        server_config = MCPServerConfig(
            command="uvx",
            args=["new-package"]
        )
        host_config = HostConfiguration(servers={"new-server": server_config})
        
        # Mock the strategy's get_config_path to return our test file
        # Mock the backup manager creation to use our test backup manager
        with patch.object(self.strategy, 'get_config_path', return_value=self.config_file), \
             patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager', return_value=self.backup_manager):
            # Write configuration
            result = self.strategy.write_configuration(host_config, no_backup=False)
        
        # Verify write succeeded
        self.assertTrue(result)
        
        # Verify no backup was created (file didn't exist)
        backups = self.backup_manager.list_backups("kiro")
        self.assertEqual(len(backups), 0)
        
        # Verify configuration was written
        self.assertTrue(self.config_file.exists())
        new_content = json.loads(self.config_file.read_text())
        self.assertIn("new-server", new_content["mcpServers"])
    
    @regression_test
    def test_backup_failure_prevents_write(self):
        """Test that backup failure prevents configuration write."""
        # Create initial configuration
        initial_config = {
            "mcpServers": {
                "existing-server": {
                    "command": "uvx",
                    "args": ["existing-package"]
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(initial_config, f, indent=2)
        
        # Create new configuration to write
        server_config = MCPServerConfig(
            command="uvx",
            args=["new-package"]
        )
        host_config = HostConfiguration(servers={"new-server": server_config})
        
        # Mock backup manager to fail
        with patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_manager.create_backup.return_value = BackupResult(
                success=False,
                error_message="Backup failed"
            )
            mock_backup_class.return_value = mock_backup_manager
            
            # Mock the strategy's get_config_path to return our test file
            with patch.object(self.strategy, 'get_config_path', return_value=self.config_file):
                # Write configuration (should fail due to backup failure)
                result = self.strategy.write_configuration(host_config, no_backup=False)
        
        # Verify write failed
        self.assertFalse(result)
        
        # Verify original configuration is unchanged
        current_content = json.loads(self.config_file.read_text())
        self.assertEqual(current_content, initial_config)
    
    @regression_test
    def test_kiro_hostname_supported_in_backup_system(self):
        """Test that 'kiro' hostname is supported by the backup system."""
        # Create test configuration file
        test_config = {
            "mcpServers": {
                "test-server": {
                    "command": "uvx",
                    "args": ["test-package"]
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Test backup creation with 'kiro' hostname
        result = self.backup_manager.create_backup(self.config_file, "kiro")
        
        # Verify backup succeeded
        self.assertTrue(result.success)
        self.assertIsNotNone(result.backup_path)
        self.assertTrue(result.backup_path.exists())
        
        # Verify backup filename format
        expected_pattern = r"mcp\.json\.kiro\.\d{8}_\d{6}_\d{6}"
        import re
        self.assertRegex(result.backup_path.name, expected_pattern)
        
        # Verify backup content
        backup_content = json.loads(result.backup_path.read_text())
        self.assertEqual(backup_content, test_config)


if __name__ == '__main__':
    unittest.main()