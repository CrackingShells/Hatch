"""
Test suite for MCP CLI backup management commands (Phase 3d).

This module tests the new MCP backup management functionality:
- hatch mcp backup restore
- hatch mcp backup list
- hatch mcp backup clean

Tests cover argument parsing, backup operations, output formatting,
and error handling scenarios.
"""

import unittest
from unittest.mock import patch, MagicMock, ANY
import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.cli_hatch import (
    main, handle_mcp_backup_restore, handle_mcp_backup_list, handle_mcp_backup_clean
)
from hatch.mcp_host_config.models import MCPHostType
from wobble import regression_test, integration_test


class TestMCPBackupRestoreCommand(unittest.TestCase):
    """Test suite for MCP backup restore command."""
    
    @regression_test
    def test_backup_restore_argument_parsing(self):
        """Test argument parsing for 'hatch mcp backup restore' command."""
        test_args = ['hatch', 'mcp', 'backup', 'restore', 'claude-desktop', '--backup-file', 'test.backup']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_backup_restore', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with(
                            ANY, 'claude-desktop', 'test.backup', False, False
                        )
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_backup_restore_dry_run_argument(self):
        """Test dry run argument for backup restore command."""
        test_args = ['hatch', 'mcp', 'backup', 'restore', 'cursor', '--dry-run', '--auto-approve']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_backup_restore', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with(
                            ANY, 'cursor', None, True, True
                        )
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @integration_test(scope="component")
    def test_backup_restore_invalid_host(self):
        """Test backup restore with invalid host type."""
        with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
            with patch('builtins.print') as mock_print:
                result = handle_mcp_backup_restore(mock_env_manager.return_value, 'invalid-host')

                self.assertEqual(result, 1)
            
            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Invalid host 'invalid-host'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_restore_no_backups(self):
        """Test backup restore when no backups exist."""
        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_manager._get_latest_backup.return_value = None
            mock_backup_class.return_value = mock_backup_manager

            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_backup_restore(mock_env_manager.return_value, 'claude-desktop')

                    self.assertEqual(result, 1)

                # Verify error message
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("Error: No backups found for host 'claude-desktop'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_restore_dry_run(self):
        """Test backup restore dry run functionality."""
        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_path = Path("/test/backup.json")
            mock_backup_manager._get_latest_backup.return_value = mock_backup_path
            mock_backup_class.return_value = mock_backup_manager

            with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_backup_restore(mock_env_manager.return_value, 'claude-desktop', dry_run=True)

                    self.assertEqual(result, 0)

                # Verify dry run output
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("[DRY RUN] Would restore backup for host 'claude-desktop'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_restore_successful(self):
        """Test successful backup restore operation."""
        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_path = Path("/test/backup.json")
            mock_backup_manager._get_latest_backup.return_value = mock_backup_path
            mock_backup_manager.restore_backup.return_value = True
            mock_backup_class.return_value = mock_backup_manager

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('hatch.cli_hatch.HatchEnvironmentManager') as mock_env_manager:
                    with patch('builtins.print') as mock_print:
                        result = handle_mcp_backup_restore(mock_env_manager.return_value, 'claude-desktop', auto_approve=True)

                        self.assertEqual(result, 0)
                    mock_backup_manager.restore_backup.assert_called_once()

                    # Verify success message
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("[SUCCESS] Successfully restored backup" in call for call in print_calls))


class TestMCPBackupListCommand(unittest.TestCase):
    """Test suite for MCP backup list command."""
    
    @regression_test
    def test_backup_list_argument_parsing(self):
        """Test argument parsing for 'hatch mcp backup list' command."""
        test_args = ['hatch', 'mcp', 'backup', 'list', 'vscode', '--detailed']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_backup_list', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with('vscode', True)
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @integration_test(scope="component")
    def test_backup_list_invalid_host(self):
        """Test backup list with invalid host type."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_backup_list('invalid-host')
            
            self.assertEqual(result, 1)
            
            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Invalid host 'invalid-host'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_list_no_backups(self):
        """Test backup list when no backups exist."""
        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_manager.list_backups.return_value = []
            mock_backup_class.return_value = mock_backup_manager

            with patch('builtins.print') as mock_print:
                result = handle_mcp_backup_list('claude-desktop')

                self.assertEqual(result, 0)

                # Verify no backups message
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("No backups found for host 'claude-desktop'" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_list_detailed_output(self):
        """Test backup list with detailed output format."""
        from hatch.mcp_host_config.backup import BackupInfo

        # Create mock backup info with proper attributes
        mock_backup = MagicMock(spec=BackupInfo)
        mock_backup.file_path = MagicMock()
        mock_backup.file_path.name = "mcp.json.claude-desktop.20250922_143000_123456"
        mock_backup.timestamp = datetime(2025, 9, 22, 14, 30, 0)
        mock_backup.file_size = 1024
        mock_backup.age_days = 5

        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_manager.list_backups.return_value = [mock_backup]
            mock_backup_class.return_value = mock_backup_manager

            with patch('builtins.print') as mock_print:
                result = handle_mcp_backup_list('claude-desktop', detailed=True)

                self.assertEqual(result, 0)

                # Verify detailed table output
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("Backup File" in call for call in print_calls))
                self.assertTrue(any("Created" in call for call in print_calls))
                self.assertTrue(any("Size" in call for call in print_calls))


class TestMCPBackupCleanCommand(unittest.TestCase):
    """Test suite for MCP backup clean command."""
    
    @regression_test
    def test_backup_clean_argument_parsing(self):
        """Test argument parsing for 'hatch mcp backup clean' command."""
        test_args = ['hatch', 'mcp', 'backup', 'clean', 'cursor', '--older-than-days', '30', '--dry-run']
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_backup_clean', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with('cursor', 30, None, True, False)
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @integration_test(scope="component")
    def test_backup_clean_no_criteria(self):
        """Test backup clean with no cleanup criteria specified."""
        with patch('builtins.print') as mock_print:
            result = handle_mcp_backup_clean('claude-desktop')
            
            self.assertEqual(result, 1)
            
            # Verify error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            self.assertTrue(any("Error: Must specify either --older-than-days or --keep-count" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_clean_dry_run(self):
        """Test backup clean dry run functionality."""
        from hatch.mcp_host_config.backup import BackupInfo

        # Create mock backup info with proper attributes
        mock_backup = MagicMock(spec=BackupInfo)
        mock_backup.file_path = Path("/test/old_backup.json")
        mock_backup.age_days = 35

        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_manager.list_backups.return_value = [mock_backup]
            mock_backup_class.return_value = mock_backup_manager

            with patch('builtins.print') as mock_print:
                result = handle_mcp_backup_clean('claude-desktop', older_than_days=30, dry_run=True)

                self.assertEqual(result, 0)

                # Verify dry run output
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("[DRY RUN] Would clean" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_backup_clean_successful(self):
        """Test successful backup clean operation."""
        from hatch.mcp_host_config.backup import BackupInfo

        # Create mock backup with proper attributes
        mock_backup = MagicMock(spec=BackupInfo)
        mock_backup.file_path = Path("/test/backup.json")
        mock_backup.age_days = 35

        with patch('hatch.mcp_host_config.backup.MCPHostConfigBackupManager') as mock_backup_class:
            mock_backup_manager = MagicMock()
            mock_backup_manager.list_backups.return_value = [mock_backup]  # Some backups exist
            mock_backup_manager.clean_backups.return_value = 3  # 3 backups cleaned
            mock_backup_class.return_value = mock_backup_manager

            with patch('hatch.cli_hatch.request_confirmation', return_value=True):
                with patch('builtins.print') as mock_print:
                    result = handle_mcp_backup_clean('claude-desktop', older_than_days=30, auto_approve=True)

                    self.assertEqual(result, 0)
                    mock_backup_manager.clean_backups.assert_called_once()

                    # Verify success message
                    print_calls = [call[0][0] for call in mock_print.call_args_list]
                    self.assertTrue(any("✓ Successfully cleaned 3 backup(s)" in call for call in print_calls))


if __name__ == '__main__':
    unittest.main()
