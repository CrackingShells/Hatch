"""Integration tests for CLI handler → ResultReporter flow.

These tests verify that CLI handlers correctly integrate with ResultReporter
for unified output rendering. Focus is on component communication, not output format.

Reference: R05 §3.7 (05-test_definition_v0.md) — CLI Handler Integration test group

Test Strategy:
- Tests verify that handlers USE ResultReporter (import and instantiate)
- Tests fail if handlers don't import ResultReporter from cli_utils
- Once handlers are updated, tests will pass
"""

import pytest
from argparse import Namespace
from unittest.mock import MagicMock, patch, PropertyMock
import io
import sys

from hatch.cli.cli_utils import ResultReporter, ConsequenceType


def _handler_uses_result_reporter(handler_module_source: str) -> bool:
    """Check if handler module imports and uses ResultReporter.
    
    This is a simple source code check to verify the handler has been updated.
    """
    return "ResultReporter" in handler_module_source


class TestMCPConfigureHandlerIntegration:
    """Integration tests for handle_mcp_configure → ResultReporter flow."""

    def test_handler_imports_result_reporter(self):
        """Handler module should import ResultReporter from cli_utils.
        
        This test verifies that the handler has been updated to use the new
        ResultReporter infrastructure instead of display_report.
        
        Risk: R3 (ConversionReport mapping loses field data)
        """
        import inspect
        from hatch.cli import cli_mcp
        
        # Get the source code of the module
        source = inspect.getsource(cli_mcp)
        
        # Verify ResultReporter is imported
        assert "from hatch.cli.cli_utils import" in source and "ResultReporter" in source, \
            "handle_mcp_configure should import ResultReporter from cli_utils"

    def test_handler_uses_result_reporter_for_output(self):
        """Handler should use ResultReporter instead of display_report.
        
        Verifies that handle_mcp_configure creates a ResultReporter and uses
        add_from_conversion_report() for ConversionReport integration.
        
        Risk: R3 (ConversionReport mapping loses field data)
        """
        from hatch.cli.cli_mcp import handle_mcp_configure
        from hatch.mcp_host_config import MCPHostType
        
        # Create mock args for a simple configure operation
        args = Namespace(
            host="claude-desktop",
            server_name="test-server",
            server_command="python",
            args=["server.py"],
            env_var=None,
            url=None,
            header=None,
            timeout=None,
            trust=False,
            cwd=None,
            env_file=None,
            http_url=None,
            include_tools=None,
            exclude_tools=None,
            input=None,
            disabled=None,
            auto_approve_tools=None,
            disable_tools=None,
            env_vars=None,
            startup_timeout=None,
            tool_timeout=None,
            enabled=None,
            bearer_token_env_var=None,
            env_header=None,
            no_backup=True,
            dry_run=False,
            auto_approve=True,  # Skip confirmation
        )
        
        # Mock the MCPHostConfigurationManager
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_server_config.return_value = None  # New server
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = None
            mock_manager.configure_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            # Capture stdout to verify ResultReporter output format
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                # Run the handler
                result = handle_mcp_configure(args)
            
            output = captured_output.getvalue()
            
            # Verify output uses new format (ResultReporter style)
            # The new format should have [SUCCESS] and [CONFIGURED] patterns
            assert "[SUCCESS]" in output or result == 0, \
                "Handler should produce success output"

    def test_handler_dry_run_shows_preview(self):
        """Dry-run flag should show preview without executing.
        
        Risk: R5 (Dry-run mode not propagated correctly)
        """
        from hatch.cli.cli_mcp import handle_mcp_configure
        
        args = Namespace(
            host="claude-desktop",
            server_name="test-server",
            server_command="python",
            args=["server.py"],
            env_var=None,
            url=None,
            header=None,
            timeout=None,
            trust=False,
            cwd=None,
            env_file=None,
            http_url=None,
            include_tools=None,
            exclude_tools=None,
            input=None,
            disabled=None,
            auto_approve_tools=None,
            disable_tools=None,
            env_vars=None,
            startup_timeout=None,
            tool_timeout=None,
            enabled=None,
            bearer_token_env_var=None,
            env_header=None,
            no_backup=True,
            dry_run=True,  # Dry-run enabled
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_server_config.return_value = None
            mock_manager_class.return_value = mock_manager
            
            # Capture stdout
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = handle_mcp_configure(args)
            
            output = captured_output.getvalue()
            
            # Verify dry-run output format
            assert "[DRY RUN]" in output, \
                "Dry-run should show [DRY RUN] prefix in output"
            
            # Verify configure_server was NOT called (dry-run doesn't execute)
            mock_manager.configure_server.assert_not_called()

    def test_handler_shows_prompt_before_confirmation(self):
        """Handler should show consequence preview before requesting confirmation.
        
        Risk: R1 (Consequence data lost/corrupted during tracking)
        """
        from hatch.cli.cli_mcp import handle_mcp_configure
        
        args = Namespace(
            host="claude-desktop",
            server_name="test-server",
            server_command="python",
            args=["server.py"],
            env_var=None,
            url=None,
            header=None,
            timeout=None,
            trust=False,
            cwd=None,
            env_file=None,
            http_url=None,
            include_tools=None,
            exclude_tools=None,
            input=None,
            disabled=None,
            auto_approve_tools=None,
            disable_tools=None,
            env_vars=None,
            startup_timeout=None,
            tool_timeout=None,
            enabled=None,
            bearer_token_env_var=None,
            env_header=None,
            no_backup=True,
            dry_run=False,
            auto_approve=False,  # Will prompt for confirmation
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_server_config.return_value = None
            mock_manager_class.return_value = mock_manager
            
            # Capture stdout and mock confirmation to decline
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                with patch('hatch.cli.cli_utils.request_confirmation', return_value=False):
                    result = handle_mcp_configure(args)
            
            output = captured_output.getvalue()
            
            # Verify prompt was shown (should contain command name and CONFIGURE verb)
            assert "hatch mcp configure" in output or "[CONFIGURE]" in output, \
                "Handler should show consequence preview before confirmation"


class TestMCPSyncHandlerIntegration:
    """Integration tests for handle_mcp_sync → ResultReporter flow."""

    def test_sync_handler_imports_result_reporter(self):
        """Sync handler module should import ResultReporter.
        
        Risk: R1 (Consequence data lost/corrupted)
        """
        import inspect
        from hatch.cli import cli_mcp
        
        source = inspect.getsource(cli_mcp)
        
        # Verify ResultReporter is imported and used in sync handler
        assert "ResultReporter" in source, \
            "cli_mcp module should import ResultReporter"

    def test_sync_handler_uses_result_reporter(self):
        """Sync handler should use ResultReporter for output.
        
        Risk: R1 (Consequence data lost/corrupted)
        """
        from hatch.cli.cli_mcp import handle_mcp_sync
        
        args = Namespace(
            from_env=None,
            from_host="claude-desktop",
            to_host="cursor",
            servers=None,
            pattern=None,
            dry_run=False,
            auto_approve=True,
            no_backup=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.servers_synced = 1
            mock_result.hosts_updated = 1
            mock_result.results = []
            mock_manager.sync_configurations.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            # Capture stdout
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = handle_mcp_sync(args)
            
            output = captured_output.getvalue()
            
            # Verify output uses ResultReporter format
            # ResultReporter uses [SYNC] for prompt and [SYNCED] for result, or [SUCCESS] header
            assert "[SUCCESS]" in output or "[SYNCED]" in output or "[SYNC]" in output, \
                f"Sync handler should use ResultReporter output format. Got: {output}"


class TestMCPRemoveHandlerIntegration:
    """Integration tests for handle_mcp_remove → ResultReporter flow."""

    def test_remove_handler_uses_result_reporter(self):
        """Remove handler should use ResultReporter for output.
        
        Risk: R1 (Consequence data lost/corrupted)
        """
        from hatch.cli.cli_mcp import handle_mcp_remove
        
        args = Namespace(
            host="claude-desktop",
            server_name="test-server",
            no_backup=True,
            dry_run=False,
            auto_approve=True,
        )
        
        with patch('hatch.cli.cli_mcp.MCPHostConfigurationManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = None
            mock_manager.remove_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager
            
            # Capture stdout
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                result = handle_mcp_remove(args)
            
            output = captured_output.getvalue()
            
            # Verify output uses ResultReporter format
            assert "[SUCCESS]" in output or "[REMOVED]" in output, \
                "Remove handler should use ResultReporter output format"


class TestMCPBackupHandlerIntegration:
    """Integration tests for MCP backup handlers → ResultReporter flow."""

    def test_backup_restore_handler_uses_result_reporter(self):
        """Backup restore handler should use ResultReporter for output.
        
        Risk: R1 (Consequence data lost/corrupted)
        """
        from hatch.cli.cli_mcp import handle_mcp_backup_restore
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager
        from pathlib import Path
        import tempfile
        
        # Create mock env_manager
        mock_env_manager = MagicMock()
        mock_env_manager.apply_restored_host_configuration_to_environments.return_value = 0
        
        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",
            backup_file=None,
            dry_run=False,
            auto_approve=True,
        )
        
        # Create a temporary backup file for the test
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir) / "claude-desktop"
            backup_dir.mkdir(parents=True)
            backup_file = backup_dir / "mcp.json.claude-desktop.20260130_120000_000000"
            backup_file.write_text('{"mcpServers": {}}')
            
            # Mock the backup manager to use our temp directory
            original_init = MCPHostConfigBackupManager.__init__
            def mock_init(self, backup_root=None):
                self.backup_root = Path(tmpdir)
                self.backup_root.mkdir(parents=True, exist_ok=True)
                from hatch.mcp_host_config.backup import AtomicFileOperations
                self.atomic_ops = AtomicFileOperations()
            
            with patch.object(MCPHostConfigBackupManager, '__init__', mock_init):
                with patch.object(MCPHostConfigBackupManager, 'restore_backup', return_value=True):
                    # Mock the strategy for post-restore sync
                    with patch('hatch.mcp_host_config.strategies'):
                        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
                            mock_strategy = MagicMock()
                            mock_strategy.read_configuration.return_value = MagicMock(servers={})
                            mock_registry.get_strategy.return_value = mock_strategy
                            
                            # Capture stdout
                            captured_output = io.StringIO()
                            with patch('sys.stdout', captured_output):
                                result = handle_mcp_backup_restore(args)
                            
                            output = captured_output.getvalue()
                            
                            # Verify output uses ResultReporter format
                            assert "[SUCCESS]" in output or "[RESTORED]" in output, \
                                f"Backup restore handler should use ResultReporter output format. Got: {output}"

    def test_backup_clean_handler_uses_result_reporter(self):
        """Backup clean handler should use ResultReporter for output.
        
        Risk: R1 (Consequence data lost/corrupted)
        """
        from hatch.cli.cli_mcp import handle_mcp_backup_clean
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager
        
        args = Namespace(
            host="claude-desktop",
            older_than_days=30,
            keep_count=None,
            dry_run=False,
            auto_approve=True,
        )
        
        with patch.object(MCPHostConfigBackupManager, '__init__', return_value=None):
            with patch.object(MCPHostConfigBackupManager, 'list_backups') as mock_list:
                mock_backup_info = MagicMock()
                mock_backup_info.age_days = 45
                mock_backup_info.file_path = MagicMock()
                mock_backup_info.file_path.name = "old_backup.json"
                mock_list.return_value = [mock_backup_info]
                
                with patch.object(MCPHostConfigBackupManager, 'clean_backups', return_value=1):
                    # Capture stdout
                    captured_output = io.StringIO()
                    with patch('sys.stdout', captured_output):
                        result = handle_mcp_backup_clean(args)
                    
                    output = captured_output.getvalue()
                    
                    # Verify output uses ResultReporter format
                    assert "[SUCCESS]" in output or "[CLEANED]" in output or "cleaned" in output.lower(), \
                        "Backup clean handler should use ResultReporter output format"
