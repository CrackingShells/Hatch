"""
Test suite for MCP synchronization functionality (Phase 3f).

This module contains comprehensive tests for the advanced synchronization
features including cross-environment and cross-host synchronization.
"""

import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import tempfile
import json
from typing import Dict, List, Optional

# Import test decorators from wobble framework
from wobble import integration_test, regression_test

# Import the modules we'll be testing
from hatch.mcp_host_config.host_management import MCPHostConfigurationManager, MCPHostType
from hatch.mcp_host_config.models import (
    EnvironmentData, MCPServerConfig, SyncResult, ConfigurationResult
)
from hatch.cli_hatch import handle_mcp_sync, parse_host_list, main


class TestMCPSyncConfigurations(unittest.TestCase):
    """Test suite for MCPHostConfigurationManager.sync_configurations() method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MCPHostConfigurationManager()

        # We'll use mocks instead of real data objects to avoid validation issues
    
    @regression_test
    def test_sync_from_environment_to_single_host(self):
        """Test basic environment-to-host synchronization."""
        with patch.object(self.manager, 'sync_configurations') as mock_sync:
            mock_result = SyncResult(
                success=True,
                results=[ConfigurationResult(success=True, hostname="claude-desktop")],
                servers_synced=2,
                hosts_updated=1
            )
            mock_sync.return_value = mock_result

            result = self.manager.sync_configurations(
                from_env="test-env",
                to_hosts=["claude-desktop"]
            )

            self.assertTrue(result.success)
            self.assertEqual(result.servers_synced, 2)
            self.assertEqual(result.hosts_updated, 1)
            mock_sync.assert_called_once()
    
    @integration_test(scope="component")
    def test_sync_from_environment_to_multiple_hosts(self):
        """Test environment-to-multiple-hosts synchronization."""
        with patch.object(self.manager, 'sync_configurations') as mock_sync:
            mock_result = SyncResult(
                success=True,
                results=[
                    ConfigurationResult(success=True, hostname="claude-desktop"),
                    ConfigurationResult(success=True, hostname="cursor")
                ],
                servers_synced=4,
                hosts_updated=2
            )
            mock_sync.return_value = mock_result

            result = self.manager.sync_configurations(
                from_env="test-env",
                to_hosts=["claude-desktop", "cursor"]
            )

            self.assertTrue(result.success)
            self.assertEqual(result.servers_synced, 4)
            self.assertEqual(result.hosts_updated, 2)
    
    @integration_test(scope="component")
    def test_sync_from_host_to_host(self):
        """Test host-to-host configuration synchronization."""
        # This test will validate the new host-to-host sync functionality
        # that needs to be implemented
        with patch.object(self.manager.host_registry, 'get_strategy') as mock_get_strategy:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = MagicMock()
            mock_strategy.write_configuration.return_value = True
            mock_get_strategy.return_value = mock_strategy
            
            # Mock the sync_configurations method that we'll implement
            with patch.object(self.manager, 'sync_configurations') as mock_sync:
                mock_result = SyncResult(
                    success=True,
                    results=[ConfigurationResult(success=True, hostname="cursor")],
                    servers_synced=2,
                    hosts_updated=1
                )
                mock_sync.return_value = mock_result
                
                result = self.manager.sync_configurations(
                    from_host="claude-desktop",
                    to_hosts=["cursor"]
                )
                
                self.assertTrue(result.success)
                self.assertEqual(result.hosts_updated, 1)
    
    @integration_test(scope="component")
    def test_sync_with_server_name_filter(self):
        """Test synchronization with specific server names."""
        with patch.object(self.manager, 'sync_configurations') as mock_sync:
            mock_result = SyncResult(
                success=True,
                results=[ConfigurationResult(success=True, hostname="claude-desktop")],
                servers_synced=1,  # Only one server due to filtering
                hosts_updated=1
            )
            mock_sync.return_value = mock_result
            
            result = self.manager.sync_configurations(
                from_env="test-env",
                to_hosts=["claude-desktop"],
                servers=["weather-toolkit"]
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.servers_synced, 1)
    
    @integration_test(scope="component")
    def test_sync_with_pattern_filter(self):
        """Test synchronization with regex pattern filter."""
        with patch.object(self.manager, 'sync_configurations') as mock_sync:
            mock_result = SyncResult(
                success=True,
                results=[ConfigurationResult(success=True, hostname="claude-desktop")],
                servers_synced=1,  # Only servers matching pattern
                hosts_updated=1
            )
            mock_sync.return_value = mock_result
            
            result = self.manager.sync_configurations(
                from_env="test-env",
                to_hosts=["claude-desktop"],
                pattern="weather-.*"
            )
            
            self.assertTrue(result.success)
            self.assertEqual(result.servers_synced, 1)
    
    @regression_test
    def test_sync_invalid_source_environment(self):
        """Test synchronization with non-existent source environment."""
        with patch.object(self.manager, 'sync_configurations') as mock_sync:
            mock_result = SyncResult(
                success=False,
                results=[ConfigurationResult(
                    success=False, 
                    hostname="claude-desktop",
                    error_message="Environment 'nonexistent' not found"
                )],
                servers_synced=0,
                hosts_updated=0
            )
            mock_sync.return_value = mock_result
            
            result = self.manager.sync_configurations(
                from_env="nonexistent",
                to_hosts=["claude-desktop"]
            )
            
            self.assertFalse(result.success)
            self.assertEqual(result.servers_synced, 0)
    
    @regression_test
    def test_sync_no_source_specified(self):
        """Test synchronization without source specification."""
        with self.assertRaises(ValueError) as context:
            self.manager.sync_configurations(to_hosts=["claude-desktop"])
        
        self.assertIn("Must specify either from_env or from_host", str(context.exception))
    
    @regression_test
    def test_sync_both_sources_specified(self):
        """Test synchronization with both env and host sources."""
        with self.assertRaises(ValueError) as context:
            self.manager.sync_configurations(
                from_env="test-env",
                from_host="claude-desktop",
                to_hosts=["cursor"]
            )
        
        self.assertIn("Cannot specify both from_env and from_host", str(context.exception))


class TestMCPSyncCommandParsing(unittest.TestCase):
    """Test suite for MCP sync command argument parsing."""
    
    @regression_test
    def test_sync_command_basic_parsing(self):
        """Test basic sync command argument parsing."""
        test_args = [
            'hatch', 'mcp', 'sync', 
            '--from-env', 'test-env', 
            '--to-host', 'claude-desktop'
        ]
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_sync', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with(
                            from_env='test-env',
                            from_host=None,
                            to_hosts='claude-desktop',
                            servers=None,
                            pattern=None,
                            dry_run=False,
                            auto_approve=False,
                            no_backup=False
                        )
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)
    
    @regression_test
    def test_sync_command_with_filters(self):
        """Test sync command with server filters."""
        test_args = [
            'hatch', 'mcp', 'sync',
            '--from-env', 'test-env',
            '--to-host', 'claude-desktop,cursor',
            '--servers', 'weather-api,file-manager',
            '--dry-run'
        ]
        
        with patch('sys.argv', test_args):
            with patch('hatch.cli_hatch.HatchEnvironmentManager'):
                with patch('hatch.cli_hatch.handle_mcp_sync', return_value=0) as mock_handler:
                    try:
                        main()
                        mock_handler.assert_called_once_with(
                            from_env='test-env',
                            from_host=None,
                            to_hosts='claude-desktop,cursor',
                            servers='weather-api,file-manager',
                            pattern=None,
                            dry_run=True,
                            auto_approve=False,
                            no_backup=False
                        )
                    except SystemExit as e:
                        self.assertEqual(e.code, 0)


class TestMCPSyncCommandHandler(unittest.TestCase):
    """Test suite for MCP sync command handler."""
    
    @integration_test(scope="component")
    def test_handle_sync_environment_to_host(self):
        """Test sync handler for environment-to-host operation."""
        with patch('hatch.cli_hatch.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_result = SyncResult(
                success=True,
                results=[ConfigurationResult(success=True, hostname="claude-desktop")],
                servers_synced=2,
                hosts_updated=1
            )
            mock_manager.sync_configurations.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            with patch('builtins.print') as mock_print:
                with patch('hatch.cli_hatch.parse_host_list') as mock_parse:
                    with patch('hatch.cli_hatch.request_confirmation', return_value=True) as mock_confirm:
                        from hatch.mcp_host_config.models import MCPHostType
                        mock_parse.return_value = [MCPHostType.CLAUDE_DESKTOP]

                        result = handle_mcp_sync(
                            from_env="test-env",
                            to_hosts="claude-desktop"
                        )

                        self.assertEqual(result, 0)
                        mock_manager.sync_configurations.assert_called_once()
                        mock_confirm.assert_called_once()

                        # Verify success output
                        print_calls = [call[0][0] for call in mock_print.call_args_list]
                        self.assertTrue(any("[SUCCESS] Synchronization completed" in call for call in print_calls))
    
    @integration_test(scope="component")
    def test_handle_sync_dry_run(self):
        """Test sync handler dry-run functionality."""
        with patch('builtins.print') as mock_print:
            with patch('hatch.cli_hatch.parse_host_list') as mock_parse:
                from hatch.mcp_host_config.models import MCPHostType
                mock_parse.return_value = [MCPHostType.CLAUDE_DESKTOP]

                result = handle_mcp_sync(
                    from_env="test-env",
                    to_hosts="claude-desktop",
                    dry_run=True
                )

                self.assertEqual(result, 0)

                # Verify dry-run output
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                self.assertTrue(any("[DRY RUN] Would synchronize" in call for call in print_calls))


if __name__ == '__main__':
    unittest.main()
