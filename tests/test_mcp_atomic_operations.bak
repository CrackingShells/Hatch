"""Tests for MCP atomic file operations.

This module contains tests for atomic file operations and backup-aware
operations with host-agnostic design.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from wobble.decorators import regression_test
from test_data_utils import MCPBackupTestDataLoader

from hatch.mcp_host_config.backup import (
    AtomicFileOperations, 
    MCPHostConfigBackupManager,
    BackupAwareOperation,
    BackupError
)


class TestAtomicFileOperations(unittest.TestCase):
    """Test atomic file operations with host-agnostic design."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_atomic_"))
        self.test_file = self.temp_dir / "test_config.json"
        self.backup_manager = MCPHostConfigBackupManager(backup_root=self.temp_dir / "backups")
        self.atomic_ops = AtomicFileOperations()
        self.test_data = MCPBackupTestDataLoader()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @regression_test
    def test_atomic_write_success_host_agnostic(self):
        """Test successful atomic write with any JSON configuration format."""
        test_data = self.test_data.load_host_agnostic_config("complex_server")
        
        result = self.atomic_ops.atomic_write_with_backup(
            self.test_file, test_data, self.backup_manager, "claude-desktop"
        )
        
        self.assertTrue(result)
        self.assertTrue(self.test_file.exists())
        
        # Verify content (host-agnostic)
        with open(self.test_file) as f:
            written_data = json.load(f)
        self.assertEqual(written_data, test_data)
    
    @regression_test
    def test_atomic_write_with_existing_file(self):
        """Test atomic write with existing file creates backup."""
        # Create initial file
        initial_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Update with atomic write
        new_data = self.test_data.load_host_agnostic_config("complex_server")
        result = self.atomic_ops.atomic_write_with_backup(
            self.test_file, new_data, self.backup_manager, "vscode"
        )
        
        self.assertTrue(result)
        
        # Verify backup was created
        backups = self.backup_manager.list_backups("vscode")
        self.assertEqual(len(backups), 1)
        
        # Verify backup contains original data
        with open(backups[0].file_path) as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data, initial_data)
        
        # Verify file contains new data
        with open(self.test_file) as f:
            current_data = json.load(f)
        self.assertEqual(current_data, new_data)
    
    @regression_test
    def test_atomic_write_skip_backup(self):
        """Test atomic write with backup skipped."""
        # Create initial file
        initial_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Update with atomic write, skipping backup
        new_data = self.test_data.load_host_agnostic_config("complex_server")
        result = self.atomic_ops.atomic_write_with_backup(
            self.test_file, new_data, self.backup_manager, "cursor", skip_backup=True
        )
        
        self.assertTrue(result)
        
        # Verify no backup was created
        backups = self.backup_manager.list_backups("cursor")
        self.assertEqual(len(backups), 0)
        
        # Verify file contains new data
        with open(self.test_file) as f:
            current_data = json.load(f)
        self.assertEqual(current_data, new_data)
    
    @regression_test
    def test_atomic_write_failure_rollback(self):
        """Test atomic write failure triggers rollback."""
        # Create initial file
        initial_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Mock file write failure after backup creation
        with patch('builtins.open', side_effect=[
            # First call succeeds (backup creation)
            open(self.test_file, 'r'),
            # Second call fails (atomic write)
            PermissionError("Access denied")
        ]):
            with self.assertRaises(BackupError):
                self.atomic_ops.atomic_write_with_backup(
                    self.test_file, {"new": "data"}, self.backup_manager, "lmstudio"
                )
        
        # Verify original file is unchanged
        with open(self.test_file) as f:
            current_data = json.load(f)
        self.assertEqual(current_data, initial_data)
    
    @regression_test
    def test_atomic_copy_success(self):
        """Test successful atomic copy operation."""
        source_file = self.temp_dir / "source.json"
        target_file = self.temp_dir / "target.json"
        
        test_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(source_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.atomic_ops.atomic_copy(source_file, target_file)
        
        self.assertTrue(result)
        self.assertTrue(target_file.exists())
        
        # Verify content integrity
        with open(target_file) as f:
            copied_data = json.load(f)
        self.assertEqual(copied_data, test_data)
    
    @regression_test
    def test_atomic_copy_failure_cleanup(self):
        """Test atomic copy failure cleans up temporary files."""
        source_file = self.temp_dir / "source.json"
        target_file = self.temp_dir / "target.json"
        
        test_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(source_file, 'w') as f:
            json.dump(test_data, f)
        
        # Mock copy failure
        with patch('shutil.copy2', side_effect=PermissionError("Access denied")):
            result = self.atomic_ops.atomic_copy(source_file, target_file)
        
        self.assertFalse(result)
        self.assertFalse(target_file.exists())
        
        # Verify no temporary files left behind
        temp_files = list(self.temp_dir.glob("*.tmp"))
        self.assertEqual(len(temp_files), 0)


class TestBackupAwareOperation(unittest.TestCase):
    """Test backup-aware operation API."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_backup_aware_"))
        self.test_file = self.temp_dir / "test_config.json"
        self.backup_manager = MCPHostConfigBackupManager(backup_root=self.temp_dir / "backups")
        self.test_data = MCPBackupTestDataLoader()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @regression_test
    def test_prepare_backup_success(self):
        """Test explicit backup preparation."""
        # Create initial configuration
        initial_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Test backup-aware operation
        operation = BackupAwareOperation(self.backup_manager)
        
        # Test explicit backup preparation
        backup_result = operation.prepare_backup(self.test_file, "gemini", no_backup=False)
        self.assertIsNotNone(backup_result)
        self.assertTrue(backup_result.success)
        
        # Verify backup was created
        backups = self.backup_manager.list_backups("gemini")
        self.assertEqual(len(backups), 1)
    
    @regression_test
    def test_prepare_backup_no_backup_mode(self):
        """Test no-backup mode."""
        # Create initial configuration
        initial_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        operation = BackupAwareOperation(self.backup_manager)
        
        # Test no-backup mode
        no_backup_result = operation.prepare_backup(self.test_file, "claude-code", no_backup=True)
        self.assertIsNone(no_backup_result)
        
        # Verify no backup was created
        backups = self.backup_manager.list_backups("claude-code")
        self.assertEqual(len(backups), 0)
    
    @regression_test
    def test_prepare_backup_failure_raises_exception(self):
        """Test backup preparation failure raises BackupError."""
        # Test with nonexistent file
        nonexistent_file = self.temp_dir / "nonexistent.json"
        
        operation = BackupAwareOperation(self.backup_manager)
        
        with self.assertRaises(BackupError):
            operation.prepare_backup(nonexistent_file, "vscode", no_backup=False)
    
    @regression_test
    def test_rollback_on_failure_success(self):
        """Test successful rollback functionality."""
        # Create initial configuration
        initial_data = self.test_data.load_host_agnostic_config("simple_server")
        with open(self.test_file, 'w') as f:
            json.dump(initial_data, f)
        
        operation = BackupAwareOperation(self.backup_manager)
        
        # Create backup
        backup_result = operation.prepare_backup(self.test_file, "cursor", no_backup=False)
        self.assertTrue(backup_result.success)
        
        # Modify file (simulate failed operation)
        modified_data = self.test_data.load_host_agnostic_config("complex_server")
        with open(self.test_file, 'w') as f:
            json.dump(modified_data, f)
        
        # Test rollback functionality
        rollback_success = operation.rollback_on_failure(backup_result, self.test_file, "cursor")
        self.assertTrue(rollback_success)
    
    @regression_test
    def test_rollback_on_failure_no_backup(self):
        """Test rollback with no backup result."""
        operation = BackupAwareOperation(self.backup_manager)
        
        # Test rollback with None backup result
        rollback_success = operation.rollback_on_failure(None, self.test_file, "lmstudio")
        self.assertFalse(rollback_success)


if __name__ == '__main__':
    unittest.main()
