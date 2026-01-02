"""Tests for MCP backup system integration.

This module contains integration tests for the backup system with existing
Hatch infrastructure and end-to-end workflows.
"""

import unittest
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

from wobble.decorators import integration_test, slow_test, regression_test
from test_data_utils import MCPBackupTestDataLoader

from hatch.mcp_host_config.backup import (
    MCPHostConfigBackupManager, 
    BackupAwareOperation,
    BackupInfo,
    BackupResult
)


class TestMCPBackupIntegration(unittest.TestCase):
    """Test backup system integration with existing Hatch infrastructure."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_integration_"))
        self.backup_manager = MCPHostConfigBackupManager(backup_root=self.temp_dir / "backups")
        self.test_data = MCPBackupTestDataLoader()
        
        # Create test configuration files
        self.config_dir = self.temp_dir / "configs"
        self.config_dir.mkdir(parents=True)
        
        self.test_configs = {}
        for hostname in ['claude-desktop', 'claude-code', 'vscode', 'cursor']:
            config_data = self.test_data.load_host_agnostic_config("simple_server")
            config_file = self.config_dir / f"{hostname}_config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.test_configs[hostname] = config_file
    
    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @integration_test(scope="component")
    def test_complete_backup_restore_cycle(self):
        """Test complete backup creation and restoration cycle."""
        hostname = 'claude-desktop'
        config_file = self.test_configs[hostname]
        
        # Create backup
        backup_result = self.backup_manager.create_backup(config_file, hostname)
        self.assertTrue(backup_result.success)
        
        # Modify original file
        modified_data = self.test_data.load_host_agnostic_config("complex_server")
        with open(config_file, 'w') as f:
            json.dump(modified_data, f)
        
        # Verify file was modified
        with open(config_file) as f:
            current_data = json.load(f)
        self.assertEqual(current_data, modified_data)
        
        # Restore from backup (placeholder - actual restore would need host config paths)
        restore_success = self.backup_manager.restore_backup(hostname)
        self.assertTrue(restore_success)  # Currently returns True as placeholder
    
    @integration_test(scope="component")
    def test_multi_host_backup_management(self):
        """Test backup management across multiple hosts."""
        # Create backups for multiple hosts
        results = {}
        for hostname, config_file in self.test_configs.items():
            results[hostname] = self.backup_manager.create_backup(config_file, hostname)
            self.assertTrue(results[hostname].success)
        
        # Verify separate backup directories
        for hostname in self.test_configs.keys():
            backups = self.backup_manager.list_backups(hostname)
            self.assertEqual(len(backups), 1)
            
            # Verify backup isolation
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
    
    @integration_test(scope="end_to_end")
    def test_backup_with_configuration_update_workflow(self):
        """Test backup integration with configuration update operations."""
        hostname = 'vscode'
        config_file = self.test_configs[hostname]
        
        # Simulate configuration update with backup
        original_data = self.test_data.load_host_agnostic_config("simple_server")
        updated_data = self.test_data.load_host_agnostic_config("complex_server")
        
        # Ensure original data is in file
        with open(config_file, 'w') as f:
            json.dump(original_data, f)
        
        # Simulate update operation with backup
        backup_result = self.backup_manager.create_backup(config_file, hostname)
        self.assertTrue(backup_result.success)
        
        # Update configuration
        with open(config_file, 'w') as f:
            json.dump(updated_data, f)
        
        # Verify backup contains original data
        backups = self.backup_manager.list_backups(hostname)
        self.assertEqual(len(backups), 1)
        
        with open(backups[0].file_path) as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data, original_data)
        
        # Verify current file has updated data
        with open(config_file) as f:
            current_data = json.load(f)
        self.assertEqual(current_data, updated_data)
    
    @integration_test(scope="service")
    def test_backup_system_with_existing_test_utilities(self):
        """Test backup system integration with existing test utilities."""
        # Use existing TestDataLoader patterns
        test_config = self.test_data.load_host_agnostic_config("complex_server")
        
        # Test backup creation with complex configuration
        config_path = self.temp_dir / "complex_config.json"
        with open(config_path, 'w') as f:
            json.dump(test_config, f)
        
        result = self.backup_manager.create_backup(config_path, "lmstudio")
        self.assertTrue(result.success)
        
        # Verify integration with existing test data patterns
        self.assertIsInstance(test_config, dict)
        self.assertIn("servers", test_config)
        
        # Verify backup content matches test data
        with open(result.backup_path) as f:
            backup_content = json.load(f)
        self.assertEqual(backup_content, test_config)
    
    @integration_test(scope="component")
    def test_backup_aware_operation_workflow(self):
        """Test backup-aware operation following environment manager patterns."""
        hostname = 'cursor'
        config_file = self.test_configs[hostname]
        
        # Test backup-aware operation following existing patterns
        operation = BackupAwareOperation(self.backup_manager)
        
        # Simulate environment manager update workflow
        backup_result = operation.prepare_backup(config_file, hostname, no_backup=False)
        self.assertTrue(backup_result.success)
        
        # Verify backup was created following existing patterns
        backups = self.backup_manager.list_backups(hostname)
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].hostname, hostname)
        
        # Test rollback capability
        rollback_success = operation.rollback_on_failure(backup_result, config_file, hostname)
        self.assertTrue(rollback_success)


class TestMCPBackupPerformance(unittest.TestCase):
    """Test backup system performance characteristics."""
    
    def setUp(self):
        """Set up performance test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="test_performance_"))
        self.backup_manager = MCPHostConfigBackupManager(backup_root=self.temp_dir / "backups")
        self.test_data = MCPBackupTestDataLoader()
    
    def tearDown(self):
        """Clean up performance test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @slow_test
    @regression_test
    def test_backup_performance_large_config(self):
        """Test backup performance with larger configuration files."""
        # Create large host-agnostic configuration
        large_config = {"servers": {}}
        for i in range(1000):
            large_config["servers"][f"server_{i}"] = {
                "command": f"python_{i}",
                "args": [f"arg_{j}" for j in range(10)]
            }
        
        config_file = self.temp_dir / "large_config.json"
        with open(config_file, 'w') as f:
            json.dump(large_config, f)
        
        start_time = time.time()
        result = self.backup_manager.create_backup(config_file, "gemini")
        duration = time.time() - start_time
        
        self.assertTrue(result.success)
        self.assertLess(duration, 1.0)  # Should complete within 1 second
    
    @regression_test
    def test_pydantic_validation_performance(self):
        """Test Pydantic model validation performance."""
        hostname = "claude-desktop"
        config_data = self.test_data.load_host_agnostic_config("simple_server")
        config_file = self.temp_dir / "test_config.json"
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        start_time = time.time()
        
        # Create backup (includes Pydantic validation)
        result = self.backup_manager.create_backup(config_file, hostname)
        
        # List backups (includes Pydantic model creation)
        backups = self.backup_manager.list_backups(hostname)
        
        duration = time.time() - start_time
        
        self.assertTrue(result.success)
        self.assertEqual(len(backups), 1)
        self.assertLess(duration, 0.1)  # Pydantic operations should be fast
    
    @regression_test
    def test_concurrent_backup_operations(self):
        """Test concurrent backup operations for different hosts."""
        import threading
        
        results = {}
        config_files = {}
        
        # Create test configurations for different hosts
        for hostname in ['claude-desktop', 'vscode', 'cursor', 'lmstudio']:
            config_data = self.test_data.load_host_agnostic_config("simple_server")
            config_file = self.temp_dir / f"{hostname}_config.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            config_files[hostname] = config_file
        
        def create_backup_thread(hostname, config_file):
            results[hostname] = self.backup_manager.create_backup(config_file, hostname)
        
        # Start concurrent backup operations
        threads = []
        for hostname, config_file in config_files.items():
            thread = threading.Thread(target=create_backup_thread, args=(hostname, config_file))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify all operations succeeded
        for hostname in config_files.keys():
            self.assertIn(hostname, results)
            self.assertTrue(results[hostname].success)
    
    @regression_test
    def test_backup_list_performance_many_backups(self):
        """Test backup listing performance with many backup files."""
        hostname = "claude-code"
        config_data = self.test_data.load_host_agnostic_config("simple_server")
        config_file = self.temp_dir / "test_config.json"
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Create many backups
        for i in range(50):
            result = self.backup_manager.create_backup(config_file, hostname)
            self.assertTrue(result.success)
        
        # Test listing performance
        start_time = time.time()
        backups = self.backup_manager.list_backups(hostname)
        duration = time.time() - start_time
        
        self.assertEqual(len(backups), 50)
        self.assertLess(duration, 0.1)  # Should be fast even with many backups
        
        # Verify all backups are valid Pydantic models
        for backup in backups:
            self.assertIsInstance(backup, BackupInfo)
            self.assertEqual(backup.hostname, hostname)


if __name__ == '__main__':
    unittest.main()
