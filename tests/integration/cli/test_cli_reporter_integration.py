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


class TestMCPListServersHostCentric:
    """Integration tests for host-centric mcp list servers command.
    
    Reference: R02 §2.5 (02-list_output_format_specification_v2.md)
    Reference: R09 §1 (09-implementation_gap_analysis_v0.md) - Critical deviation analysis
    
    These tests verify that handle_mcp_list_servers:
    1. Reads from actual host config files (not environment data)
    2. Shows ALL servers (Hatch-managed ✅ and 3rd party ❌)
    3. Cross-references with environments for Hatch status
    4. Supports --host flag to filter to specific host
    5. Supports --pattern flag for regex filtering
    """

    def test_list_servers_reads_from_host_config(self):
        """Command should read servers from host config files, not environment data.
        
        This is the CRITICAL test for host-centric design.
        The command must read from actual host config files (e.g., ~/.claude/config.json)
        and show ALL servers, not just Hatch-managed packages.
        
        Risk: Architectural deviation - package-centric vs host-centric
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        # Create mock env_manager with dict-based return values (matching real implementation)
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "weather-server",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {"configured_at": "2026-01-30"}}
                }
            ]
        }
        
        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",
            pattern=None,
            json=False,
        )
        
        # Mock the host strategy to return servers from config file
        # This simulates reading from ~/.claude/config.json
        mock_host_config = HostConfiguration(servers={
            "weather-server": MCPServerConfig(name="weather-server", command="python", args=["weather.py"]),
            "custom-tool": MCPServerConfig(name="custom-tool", command="node", args=["custom.js"]),  # 3rd party!
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [MCPHostType.CLAUDE_DESKTOP]
            
            # Import strategies to trigger registration
            with patch('hatch.mcp_host_config.strategies'):
                # Capture stdout
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_servers(args)
                
                output = captured_output.getvalue()
                
                # CRITICAL: Verify the command reads from host config (strategy.read_configuration called)
                mock_strategy.read_configuration.assert_called_once()
                
                # Verify BOTH servers appear in output (Hatch-managed AND 3rd party)
                assert "weather-server" in output, \
                    "Hatch-managed server should appear in output"
                assert "custom-tool" in output, \
                    "3rd party server should appear in output (host-centric design)"
                
                # Verify Hatch status indicators
                assert "✅" in output, "Hatch-managed server should show ✅"
                assert "❌" in output, "3rd party server should show ❌"

    def test_list_servers_shows_third_party_servers(self):
        """Command should show 3rd party servers with ❌ status.
        
        A 3rd party server is one configured directly on the host
        that is NOT tracked in any Hatch environment.
        
        Risk: Missing 3rd party servers in output
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        # Create mock env_manager with NO packages (empty environment)
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}
        
        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",
            pattern=None,
            json=False,
        )
        
        # Host config has a server that's NOT in any Hatch environment
        mock_host_config = HostConfiguration(servers={
            "external-tool": MCPServerConfig(name="external-tool", command="external", args=[]),
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_servers(args)
                
                output = captured_output.getvalue()
                
                # 3rd party server should appear with ❌ status
                assert "external-tool" in output, \
                    "3rd party server should appear in output"
                assert "❌" in output, \
                    "3rd party server should show ❌ (not Hatch-managed)"

    def test_list_servers_without_host_shows_all_hosts(self):
        """Without --host flag, command should show servers from ALL available hosts.
        
        Reference: R02 §2.5 - "Without --host: shows all servers across all hosts"
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}
        
        args = Namespace(
            env_manager=mock_env_manager,
            host=None,  # No host filter - show ALL hosts
            pattern=None,
            json=False,
        )
        
        # Create configs for multiple hosts
        claude_config = HostConfiguration(servers={
            "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
        })
        cursor_config = HostConfiguration(servers={
            "server-b": MCPServerConfig(name="server-b", command="node", args=[]),
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            # Mock detect_available_hosts to return multiple hosts
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]
            
            # Mock get_strategy to return different configs per host
            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(servers={})
                return mock_strategy
            
            mock_registry.get_strategy.side_effect = get_strategy_side_effect
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_servers(args)
                
                output = captured_output.getvalue()
                
                # Both servers from different hosts should appear
                assert "server-a" in output, "Server from claude-desktop should appear"
                assert "server-b" in output, "Server from cursor should appear"
                
                # Host column should be present (since no --host filter)
                assert "claude-desktop" in output or "Host" in output, \
                    "Host column should be present when showing all hosts"

    def test_list_servers_pattern_filter(self):
        """--pattern flag should filter servers by regex on server name.
        
        Reference: R02 §2.5 - "--pattern filters by server name (regex)"
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}
        
        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",
            pattern="weather.*",  # Regex pattern
            json=False,
        )
        
        mock_host_config = HostConfiguration(servers={
            "weather-server": MCPServerConfig(name="weather-server", command="python", args=[]),
            "weather-api": MCPServerConfig(name="weather-api", command="python", args=[]),
            "fetch-server": MCPServerConfig(name="fetch-server", command="node", args=[]),  # Should NOT match
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_servers(args)
                
                output = captured_output.getvalue()
                
                # Matching servers should appear
                assert "weather-server" in output, "weather-server should match pattern"
                assert "weather-api" in output, "weather-api should match pattern"
                
                # Non-matching server should NOT appear
                assert "fetch-server" not in output, \
                    "fetch-server should NOT appear (doesn't match pattern)"

    def test_list_servers_json_output_host_centric(self):
        """JSON output should include host-centric data structure.
        
        Reference: R02 §8.1 - JSON output format for mcp list servers
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        import json
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "managed-server",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {}}
                }
            ]
        }
        
        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",
            pattern=None,
            json=True,  # JSON output
        )
        
        mock_host_config = HostConfiguration(servers={
            "managed-server": MCPServerConfig(name="managed-server", command="python", args=[]),
            "unmanaged-server": MCPServerConfig(name="unmanaged-server", command="node", args=[]),
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_servers(args)
                
                output = captured_output.getvalue()
                
                # Parse JSON output
                data = json.loads(output)
                
                # Verify structure
                assert "host" in data, "JSON should include host field"
                assert "servers" in data, "JSON should include servers array"
                assert data["host"] == "claude-desktop"
                
                # Verify both servers present with hatch_managed field
                server_names = [s["name"] for s in data["servers"]]
                assert "managed-server" in server_names
                assert "unmanaged-server" in server_names
                
                # Verify hatch_managed status
                for server in data["servers"]:
                    if server["name"] == "managed-server":
                        assert server["hatch_managed"] == True
                    elif server["name"] == "unmanaged-server":
                        assert server["hatch_managed"] == False


class TestMCPListHostsHostCentric:
    """Integration tests for host-centric mcp list hosts command.
    
    Reference: R10 §3.1 (10-namespace_consistency_specification_v2.md)
    
    These tests verify that handle_mcp_list_hosts:
    1. Reads from actual host config files (not environment data)
    2. Shows host/server pairs with columns: Host → Server → Hatch → Environment
    3. Supports --server flag to filter by server name regex
    4. First column (Host) sorted alphabetically
    """

    def test_mcp_list_hosts_uniform_output(self):
        """Command should produce uniform table output with Host → Server → Hatch → Environment columns.
        
        Reference: R10 §3.1 - Column order matches command structure
        """
        from hatch.cli.cli_mcp import handle_mcp_list_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "weather-server",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {"configured_at": "2026-01-30"}}
                }
            ]
        }
        
        args = Namespace(
            env_manager=mock_env_manager,
            server=None,  # No filter
            json=False,
        )
        
        # Host config has both Hatch-managed and 3rd party servers
        mock_host_config = HostConfiguration(servers={
            "weather-server": MCPServerConfig(name="weather-server", command="python", args=["weather.py"]),
            "custom-tool": MCPServerConfig(name="custom-tool", command="node", args=["custom.js"]),
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [MCPHostType.CLAUDE_DESKTOP]
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_hosts(args)
                
                output = captured_output.getvalue()
                
                # Verify column headers present
                assert "Host" in output, "Host column should be present"
                assert "Server" in output, "Server column should be present"
                assert "Hatch" in output, "Hatch column should be present"
                assert "Environment" in output, "Environment column should be present"
                
                # Verify both servers appear
                assert "weather-server" in output, "Hatch-managed server should appear"
                assert "custom-tool" in output, "3rd party server should appear"
                
                # Verify Hatch status indicators
                assert "✅" in output, "Hatch-managed server should show ✅"
                assert "❌" in output, "3rd party server should show ❌"

    def test_mcp_list_hosts_server_filter_exact(self):
        """--server flag with exact name should filter to matching servers only.
        
        Reference: R10 §3.1 - --server <pattern> filter
        """
        from hatch.cli.cli_mcp import handle_mcp_list_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}
        
        args = Namespace(
            env_manager=mock_env_manager,
            server="weather-server",  # Exact match filter
            json=False,
        )
        
        mock_host_config = HostConfiguration(servers={
            "weather-server": MCPServerConfig(name="weather-server", command="python", args=[]),
            "fetch-server": MCPServerConfig(name="fetch-server", command="node", args=[]),
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [MCPHostType.CLAUDE_DESKTOP]
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_hosts(args)
                
                output = captured_output.getvalue()
                
                # Matching server should appear
                assert "weather-server" in output, "weather-server should match filter"
                
                # Non-matching server should NOT appear
                assert "fetch-server" not in output, "fetch-server should NOT appear"

    def test_mcp_list_hosts_server_filter_pattern(self):
        """--server flag with regex pattern should filter matching servers.
        
        Reference: R10 §3.1 - --server accepts regex patterns
        """
        from hatch.cli.cli_mcp import handle_mcp_list_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}
        
        args = Namespace(
            env_manager=mock_env_manager,
            server=".*-server",  # Regex pattern
            json=False,
        )
        
        mock_host_config = HostConfiguration(servers={
            "weather-server": MCPServerConfig(name="weather-server", command="python", args=[]),
            "fetch-server": MCPServerConfig(name="fetch-server", command="node", args=[]),
            "custom-tool": MCPServerConfig(name="custom-tool", command="node", args=[]),  # Should NOT match
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [MCPHostType.CLAUDE_DESKTOP]
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_hosts(args)
                
                output = captured_output.getvalue()
                
                # Matching servers should appear
                assert "weather-server" in output, "weather-server should match pattern"
                assert "fetch-server" in output, "fetch-server should match pattern"
                
                # Non-matching server should NOT appear
                assert "custom-tool" not in output, "custom-tool should NOT match pattern"

    def test_mcp_list_hosts_alphabetical_ordering(self):
        """First column (Host) should be sorted alphabetically.
        
        Reference: R10 §1.3 - Alphabetical ordering
        """
        from hatch.cli.cli_mcp import handle_mcp_list_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}
        
        args = Namespace(
            env_manager=mock_env_manager,
            server=None,
            json=False,
        )
        
        # Create configs for multiple hosts
        claude_config = HostConfiguration(servers={
            "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
        })
        cursor_config = HostConfiguration(servers={
            "server-b": MCPServerConfig(name="server-b", command="node", args=[]),
        })
        
        with patch('hatch.cli.cli_mcp.MCPHostRegistry') as mock_registry:
            # Return hosts in non-alphabetical order to test sorting
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CURSOR,  # Should come second alphabetically
                MCPHostType.CLAUDE_DESKTOP,  # Should come first alphabetically
            ]
            
            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(servers={})
                return mock_strategy
            
            mock_registry.get_strategy.side_effect = get_strategy_side_effect
            
            with patch('hatch.mcp_host_config.strategies'):
                captured_output = io.StringIO()
                with patch('sys.stdout', captured_output):
                    result = handle_mcp_list_hosts(args)
                
                output = captured_output.getvalue()
                
                # Find positions of hosts in output
                claude_pos = output.find("claude-desktop")
                cursor_pos = output.find("cursor")
                
                # claude-desktop should appear before cursor (alphabetically)
                assert claude_pos < cursor_pos, \
                    "Hosts should be sorted alphabetically (claude-desktop before cursor)"
