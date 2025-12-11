"""Tests for MCPHostConfigBackupManager.

This module contains tests for the MCP host configuration backup functionality,
including backup creation, restoration, and management with host-agnostic design.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, Mock

from wobble.decorators import regression_test, integration_test, slow_test
from test_data_utils import MCPBackupTestDataLoader

from hatch.mcp_host_config.backup import (
    MCPHostConfigBackupManager, 
    BackupInfo, 
    BackupResult,
    BackupError
)


class TestMCPHostConfigBackupManager(unittest.TestCase):
    """Test MCPHostConfigBackupManager core functionality with host-agnostic design."""
    
    def setUp(self):
        """Set up test environment with host-agnostic configurations."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_mcp_backup_"))
        self.backup_root = self.temp_dir / "backups"
        self.config_dir = self.temp_dir / "configs"
        self.config_dir.mkdir(parents=True)
        
        # Initialize test data loader
        self.test_data = MCPBackupTestDataLoader()
        
        # Create host-agnostic test configuration files
        self.test_configs = {}
        for hostname in ['claude-desktop', 'vscode', 'cursor', 'lmstudio']:
            config_data = self.test_data.load_host_agnostic_config("simple_server")
            config_file = self.config_dir / f"{hostname}_config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.test_configs[hostname] = config_file
        
        self.backup_manager = MCPHostConfigBackupManager(backup_root=self.backup_root)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @regression_test
    def test_backup_directory_creation(self):
        """Test automatic backup directory creation."""
        self.assertTrue(self.backup_root.exists())
        self.assertTrue(self.backup_root.is_dir())
    
    @regression_test
    def test_create_backup_success_all_hosts(self):
        """Test successful backup creation for all supported host types."""
        for hostname, config_file in self.test_configs.items():
            with self.subTest(hostname=hostname):
                result = self.backup_manager.create_backup(config_file, hostname)
                
                # Validate BackupResult Pydantic model
                self.assertIsInstance(result, BackupResult)
                self.assertTrue(result.success)
                self.assertIsNotNone(result.backup_path)
                self.assertTrue(result.backup_path.exists())
                self.assertGreater(result.backup_size, 0)
                self.assertEqual(result.original_size, result.backup_size)
                
                # Verify backup filename format (host-agnostic)
                expected_pattern = rf"mcp\.json\.{hostname}\.\d{{8}}_\d{{6}}_\d{{6}}"
                self.assertRegex(result.backup_path.name, expected_pattern)
    
    @regression_test
    def test_create_backup_nonexistent_file(self):
        """Test backup creation with nonexistent source file."""
        nonexistent = self.config_dir / "nonexistent.json"
        result = self.backup_manager.create_backup(nonexistent, "claude-desktop")
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn("not found", result.error_message.lower())
    
    @regression_test
    def test_backup_content_integrity_host_agnostic(self):
        """Test backup content matches original for any host configuration format."""
        hostname = 'claude-desktop'
        config_file = self.test_configs[hostname]
        original_content = config_file.read_text()
        
        result = self.backup_manager.create_backup(config_file, hostname)
        
        self.assertTrue(result.success)
        backup_content = result.backup_path.read_text()
        self.assertEqual(original_content, backup_content)
        
        # Verify JSON structure is preserved (host-agnostic validation)
        original_json = json.loads(original_content)
        backup_json = json.loads(backup_content)
        self.assertEqual(original_json, backup_json)
    
    @regression_test
    def test_multiple_backups_same_host(self):
        """Test creating multiple backups for same host."""
        hostname = 'vscode'
        config_file = self.test_configs[hostname]
        
        # Create first backup
        result1 = self.backup_manager.create_backup(config_file, hostname)
        self.assertTrue(result1.success)
        
        # Modify config and create second backup
        modified_config = self.test_data.load_host_agnostic_config("complex_server")
        with open(config_file, 'w') as f:
            json.dump(modified_config, f, indent=2)
        
        result2 = self.backup_manager.create_backup(config_file, hostname)
        self.assertTrue(result2.success)
        
        # Verify both backups exist and are different
        self.assertTrue(result1.backup_path.exists())
        self.assertTrue(result2.backup_path.exists())
        self.assertNotEqual(result1.backup_path, result2.backup_path)
    
    @regression_test
    def test_list_backups_empty(self):
        """Test listing backups when none exist."""
        backups = self.backup_manager.list_backups("claude-desktop")
        self.assertEqual(len(backups), 0)
    
    @regression_test
    def test_list_backups_pydantic_validation(self):
        """Test listing backups returns valid Pydantic models."""
        hostname = 'cursor'
        config_file = self.test_configs[hostname]
        
        # Create multiple backups
        self.backup_manager.create_backup(config_file, hostname)
        self.backup_manager.create_backup(config_file, hostname)
        
        backups = self.backup_manager.list_backups(hostname)
        self.assertEqual(len(backups), 2)
        
        # Verify BackupInfo Pydantic model validation
        for backup in backups:
            self.assertIsInstance(backup, BackupInfo)
            self.assertEqual(backup.hostname, hostname)
            self.assertIsInstance(backup.timestamp, datetime)
            self.assertTrue(backup.file_path.exists())
            self.assertGreater(backup.file_size, 0)
            
            # Test Pydantic serialization
            backup_dict = backup.dict()
            self.assertIn('hostname', backup_dict)
            self.assertIn('timestamp', backup_dict)
            
            # Test JSON serialization
            backup_json = backup.json()
            self.assertIsInstance(backup_json, str)
        
        # Verify sorting (newest first)
        self.assertGreaterEqual(backups[0].timestamp, backups[1].timestamp)
    
    @regression_test
    def test_backup_validation_unsupported_hostname(self):
        """Test Pydantic validation rejects unsupported hostnames."""
        config_file = self.test_configs['claude-desktop']
        
        # Test with unsupported hostname
        result = self.backup_manager.create_backup(config_file, 'unsupported-host')
        
        self.assertFalse(result.success)
        self.assertIn('unsupported', result.error_message.lower())
    
    @regression_test
    def test_multiple_hosts_isolation(self):
        """Test backup isolation between different host types."""
        # Create backups for multiple hosts
        results = {}
        for hostname, config_file in self.test_configs.items():
            results[hostname] = self.backup_manager.create_backup(config_file, hostname)
            self.assertTrue(results[hostname].success)
        
        # Verify separate backup directories
        for hostname in self.test_configs.keys():
            backups = self.backup_manager.list_backups(hostname)
            self.assertEqual(len(backups), 1)
            
            # Verify backup isolation (different directories)
            backup_dir = backups[0].file_path.parent
            self.assertEqual(backup_dir.name, hostname)
            
            # Verify no cross-contamination
            for other_hostname in self.test_configs.keys():
                if other_hostname != hostname:
                    other_backups = self.backup_manager.list_backups(other_hostname)
                    self.assertNotEqual(
                        backups[0].file_path.parent,
                        other_backups[0].file_path.parent
                    )
    
    @regression_test
    def test_clean_backups_older_than_days(self):
        """Test cleaning backups older than specified days."""
        hostname = 'lmstudio'
        config_file = self.test_configs[hostname]
        
        # Create backup
        result = self.backup_manager.create_backup(config_file, hostname)
        self.assertTrue(result.success)
        
        # Mock old backup by modifying timestamp
        old_backup_path = result.backup_path.parent / "mcp.json.lmstudio.20200101_120000_000000"
        shutil.copy2(result.backup_path, old_backup_path)
        
        # Clean backups older than 1 day (should remove the old one)
        cleaned_count = self.backup_manager.clean_backups(hostname, older_than_days=1)
        
        # Verify old backup was cleaned
        self.assertGreater(cleaned_count, 0)
        self.assertFalse(old_backup_path.exists())
        self.assertTrue(result.backup_path.exists())  # Recent backup should remain
    
    @regression_test
    def test_clean_backups_keep_count(self):
        """Test cleaning backups to keep only specified count."""
        hostname = 'claude-desktop'
        config_file = self.test_configs[hostname]
        
        # Create multiple backups
        for i in range(5):
            self.backup_manager.create_backup(config_file, hostname)
        
        # Verify 5 backups exist
        backups_before = self.backup_manager.list_backups(hostname)
        self.assertEqual(len(backups_before), 5)
        
        # Clean to keep only 2 backups
        cleaned_count = self.backup_manager.clean_backups(hostname, keep_count=2)
        
        # Verify only 2 backups remain
        backups_after = self.backup_manager.list_backups(hostname)
        self.assertEqual(len(backups_after), 2)
        self.assertEqual(cleaned_count, 3)
        
        # Verify newest backups were kept
        for backup in backups_after:
            self.assertIn(backup, backups_before[:2])  # Should be the first 2 (newest)


if __name__ == '__main__':
    unittest.main()
