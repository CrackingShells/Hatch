"""
Codex MCP Backup Integration Tests

Tests for Codex TOML backup integration including backup creation,
restoration, and the no_backup parameter.
"""

import unittest
import tempfile
import tomllib
from pathlib import Path

from wobble.decorators import regression_test

from hatch.mcp_host_config.strategies import CodexHostStrategy
from hatch.mcp_host_config.models import MCPServerConfig, HostConfiguration
from hatch.mcp_host_config.backup import MCPHostConfigBackupManager, BackupInfo


class TestCodexBackupIntegration(unittest.TestCase):
    """Test suite for Codex backup integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.strategy = CodexHostStrategy()
    
    @regression_test
    def test_write_configuration_creates_backup_by_default(self):
        """Test that write_configuration creates backup by default when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            backup_dir = Path(tmpdir) / "backups"
            
            # Create initial config
            initial_toml = """[mcp_servers.old-server]
command = "old-command"
"""
            config_path.write_text(initial_toml)
            
            # Create new configuration
            new_config = HostConfiguration(servers={
                'new-server': MCPServerConfig(
                    command='new-command',
                    args=['--test']
                )
            })
            
            # Patch paths
            from unittest.mock import patch
            with patch.object(self.strategy, 'get_config_path', return_value=config_path):
                with patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager') as MockBackupManager:
                    # Create a real backup manager with custom backup dir
                    real_backup_manager = MCPHostConfigBackupManager(backup_root=backup_dir)
                    MockBackupManager.return_value = real_backup_manager
                    
                    # Write configuration (should create backup)
                    success = self.strategy.write_configuration(new_config, no_backup=False)
                    self.assertTrue(success)
                    
                    # Verify backup was created
                    backup_files = list(backup_dir.glob('codex/*.toml.*'))
                    self.assertGreater(len(backup_files), 0, "Backup file should be created")
    
    @regression_test
    def test_write_configuration_skips_backup_when_requested(self):
        """Test that write_configuration skips backup when no_backup=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            backup_dir = Path(tmpdir) / "backups"
            
            # Create initial config
            initial_toml = """[mcp_servers.old-server]
command = "old-command"
"""
            config_path.write_text(initial_toml)
            
            # Create new configuration
            new_config = HostConfiguration(servers={
                'new-server': MCPServerConfig(
                    command='new-command'
                )
            })
            
            # Patch paths
            from unittest.mock import patch
            with patch.object(self.strategy, 'get_config_path', return_value=config_path):
                with patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager') as MockBackupManager:
                    real_backup_manager = MCPHostConfigBackupManager(backup_root=backup_dir)
                    MockBackupManager.return_value = real_backup_manager
                    
                    # Write configuration with no_backup=True
                    success = self.strategy.write_configuration(new_config, no_backup=True)
                    self.assertTrue(success)
                    
                    # Verify no backup was created
                    if backup_dir.exists():
                        backup_files = list(backup_dir.glob('codex/*.toml.*'))
                        self.assertEqual(len(backup_files), 0, "No backup should be created when no_backup=True")
    
    @regression_test
    def test_write_configuration_no_backup_for_new_file(self):
        """Test that no backup is created when writing to a new file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            backup_dir = Path(tmpdir) / "backups"
            
            # Don't create initial file - this is a new file
            
            # Create new configuration
            new_config = HostConfiguration(servers={
                'new-server': MCPServerConfig(
                    command='new-command'
                )
            })
            
            # Patch paths
            from unittest.mock import patch
            with patch.object(self.strategy, 'get_config_path', return_value=config_path):
                with patch('hatch.mcp_host_config.strategies.MCPHostConfigBackupManager') as MockBackupManager:
                    real_backup_manager = MCPHostConfigBackupManager(backup_root=backup_dir)
                    MockBackupManager.return_value = real_backup_manager
                    
                    # Write configuration to new file
                    success = self.strategy.write_configuration(new_config, no_backup=False)
                    self.assertTrue(success)
                    
                    # Verify file was created
                    self.assertTrue(config_path.exists())
                    
                    # Verify no backup was created (nothing to backup)
                    if backup_dir.exists():
                        backup_files = list(backup_dir.glob('codex/*.toml.*'))
                        self.assertEqual(len(backup_files), 0, "No backup for new file")
    
    @regression_test
    def test_codex_hostname_supported_in_backup_system(self):
        """Test that 'codex' hostname is supported by the backup system."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            backup_dir = Path(tmpdir) / "backups"
            
            # Create a config file
            config_path.write_text("[mcp_servers.test]\ncommand = 'test'\n")
            
            # Create backup manager
            backup_manager = MCPHostConfigBackupManager(backup_root=backup_dir)
            
            # Create backup with 'codex' hostname - should not raise validation error
            result = backup_manager.create_backup(config_path, 'codex')
            
            # Verify backup succeeded
            self.assertTrue(result.success, "Backup with 'codex' hostname should succeed")
            self.assertIsNotNone(result.backup_path)
            
            # Verify backup filename follows pattern
            backup_filename = result.backup_path.name
            self.assertTrue(backup_filename.startswith('config.toml.codex.'))


if __name__ == '__main__':
    unittest.main()

