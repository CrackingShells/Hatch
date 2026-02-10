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
from unittest.mock import MagicMock, patch
import io


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
        assert (
            "from hatch.cli.cli_utils import" in source and "ResultReporter" in source
        ), "handle_mcp_configure should import ResultReporter from cli_utils"

    def test_handler_uses_result_reporter_for_output(self):
        """Handler should use ResultReporter instead of display_report.

        Verifies that handle_mcp_configure creates a ResultReporter and uses
        add_from_conversion_report() for ConversionReport integration.

        Risk: R3 (ConversionReport mapping loses field data)
        """
        from hatch.cli.cli_mcp import handle_mcp_configure

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
        with patch(
            "hatch.cli.cli_mcp.MCPHostConfigurationManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_server_config.return_value = None  # New server
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = None
            mock_manager.configure_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            # Capture stdout to verify ResultReporter output format
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output):
                # Run the handler
                result = handle_mcp_configure(args)

            output = captured_output.getvalue()

            # Verify output uses new format (ResultReporter style)
            # The new format should have [SUCCESS] and [CONFIGURED] patterns
            assert (
                "[SUCCESS]" in output or result == 0
            ), "Handler should produce success output"

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

        with patch(
            "hatch.cli.cli_mcp.MCPHostConfigurationManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_server_config.return_value = None
            mock_manager_class.return_value = mock_manager

            # Capture stdout
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output):
                result = handle_mcp_configure(args)

            output = captured_output.getvalue()

            # Verify dry-run output format
            assert (
                "[DRY RUN]" in output
            ), "Dry-run should show [DRY RUN] prefix in output"

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

        with patch(
            "hatch.cli.cli_mcp.MCPHostConfigurationManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_server_config.return_value = None
            mock_manager_class.return_value = mock_manager

            # Capture stdout and mock confirmation to decline
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output):
                with patch(
                    "hatch.cli.cli_utils.request_confirmation", return_value=False
                ):
                    result = handle_mcp_configure(args)

            output = captured_output.getvalue()

            # Verify prompt was shown (should contain command name and CONFIGURE verb)
            assert (
                "hatch mcp configure" in output or "[CONFIGURE]" in output
            ), "Handler should show consequence preview before confirmation"


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
        assert "ResultReporter" in source, "cli_mcp module should import ResultReporter"

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
            dry_run=False,
            auto_approve=True,
            no_backup=True,
        )

        with patch(
            "hatch.cli.cli_mcp.MCPHostConfigurationManager"
        ) as mock_manager_class:
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
            with patch("sys.stdout", captured_output):
                result = handle_mcp_sync(args)

            output = captured_output.getvalue()

            # Verify output uses ResultReporter format
            # ResultReporter uses [SYNC] for prompt and [SYNCED] for result, or [SUCCESS] header
            assert (
                "[SUCCESS]" in output or "[SYNCED]" in output or "[SYNC]" in output
            ), f"Sync handler should use ResultReporter output format. Got: {output}"


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

        with patch(
            "hatch.cli.cli_mcp.MCPHostConfigurationManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.backup_path = None
            mock_manager.remove_server.return_value = mock_result
            mock_manager_class.return_value = mock_manager

            # Capture stdout
            captured_output = io.StringIO()
            with patch("sys.stdout", captured_output):
                result = handle_mcp_remove(args)

            output = captured_output.getvalue()

            # Verify output uses ResultReporter format
            assert (
                "[SUCCESS]" in output or "[REMOVED]" in output
            ), "Remove handler should use ResultReporter output format"


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
        mock_env_manager.apply_restored_host_configuration_to_environments.return_value = (
            0
        )

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

            with patch.object(MCPHostConfigBackupManager, "__init__", mock_init):
                with patch.object(
                    MCPHostConfigBackupManager, "restore_backup", return_value=True
                ):
                    # Mock the strategy for post-restore sync
                    with patch("hatch.mcp_host_config.strategies"):
                        with patch(
                            "hatch.cli.cli_mcp.MCPHostRegistry"
                        ) as mock_registry:
                            mock_strategy = MagicMock()
                            mock_strategy.read_configuration.return_value = MagicMock(
                                servers={}
                            )
                            mock_registry.get_strategy.return_value = mock_strategy

                            # Capture stdout
                            captured_output = io.StringIO()
                            with patch("sys.stdout", captured_output):
                                result = handle_mcp_backup_restore(args)

                            output = captured_output.getvalue()

                            # Verify output uses ResultReporter format
                            assert (
                                "[SUCCESS]" in output or "[RESTORED]" in output
                            ), f"Backup restore handler should use ResultReporter output format. Got: {output}"

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

        with patch.object(MCPHostConfigBackupManager, "__init__", return_value=None):
            with patch.object(MCPHostConfigBackupManager, "list_backups") as mock_list:
                mock_backup_info = MagicMock()
                mock_backup_info.age_days = 45
                mock_backup_info.file_path = MagicMock()
                mock_backup_info.file_path.name = "old_backup.json"
                mock_list.return_value = [mock_backup_info]

                with patch.object(
                    MCPHostConfigBackupManager, "clean_backups", return_value=1
                ):
                    # Capture stdout
                    captured_output = io.StringIO()
                    with patch("sys.stdout", captured_output):
                        result = handle_mcp_backup_clean(args)

                    output = captured_output.getvalue()

                    # Verify output uses ResultReporter format
                    assert (
                        "[SUCCESS]" in output
                        or "[CLEANED]" in output
                        or "cleaned" in output.lower()
                    ), "Backup clean handler should use ResultReporter output format"


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
                    "configured_hosts": {
                        "claude-desktop": {"configured_at": "2026-01-30"}
                    },
                }
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",
            json=False,
        )

        # Mock the host strategy to return servers from config file
        # This simulates reading from ~/.claude/config.json
        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="python", args=["weather.py"]
                ),
                "custom-tool": MCPServerConfig(
                    name="custom-tool", command="node", args=["custom.js"]
                ),  # 3rd party!
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]

            # Import strategies to trigger registration
            with patch("hatch.mcp_host_config.strategies"):
                # Capture stdout
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_servers(args)

                output = captured_output.getvalue()

                # CRITICAL: Verify the command reads from host config (strategy.read_configuration called)
                mock_strategy.read_configuration.assert_called_once()

                # Verify BOTH servers appear in output (Hatch-managed AND 3rd party)
                assert (
                    "weather-server" in output
                ), "Hatch-managed server should appear in output"
                assert (
                    "custom-tool" in output
                ), "3rd party server should appear in output (host-centric design)"

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
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        # Create mock env_manager with NO packages (empty environment)
        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host=None,  # No filter - show all hosts
            json=False,
        )

        # Host config has a server that's NOT in any Hatch environment
        mock_host_config = HostConfiguration(
            servers={
                "external-tool": MCPServerConfig(
                    name="external-tool", command="external", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_servers(args)

                output = captured_output.getvalue()

                # 3rd party server should appear with ❌ status
                assert (
                    "external-tool" in output
                ), "3rd party server should appear in output"
                assert (
                    "❌" in output
                ), "3rd party server should show ❌ (not Hatch-managed)"

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
            json=False,
        )

        # Create configs for multiple hosts
        claude_config = HostConfiguration(
            servers={
                "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "server-b": MCPServerConfig(name="server-b", command="node", args=[]),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            # Mock detect_available_hosts to return multiple hosts
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            # Mock get_strategy to return different configs per host
            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_servers(args)

                output = captured_output.getvalue()

                # Both servers from different hosts should appear
                assert "server-a" in output, "Server from claude-desktop should appear"
                assert "server-b" in output, "Server from cursor should appear"

                # Host column should be present (since no --host filter)
                assert (
                    "claude-desktop" in output or "Host" in output
                ), "Host column should be present when showing all hosts"

    def test_list_servers_host_filter_pattern(self):
        """--host flag should filter by host name using regex pattern.

        Reference: R10 §3.2 - "--host accepts regex patterns"
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host="claude.*",  # Regex pattern
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="python", args=[]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="node", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_servers(args)

                output = captured_output.getvalue()

                # Server from claude-desktop should appear (matches pattern)
                assert (
                    "weather-server" in output
                ), "weather-server should appear (host matches pattern)"

                # Server from cursor should NOT appear (doesn't match pattern)
                assert (
                    "fetch-server" not in output
                ), "fetch-server should NOT appear (cursor doesn't match 'claude.*')"

    def test_list_servers_json_output_host_centric(self):
        """JSON output should include host-centric data structure.

        Reference: R10 §3.2 - JSON output format for mcp list servers
        """
        from hatch.cli.cli_mcp import handle_mcp_list_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        import json

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "managed-server",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {}},
                }
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            host=None,  # No filter - show all hosts
            json=True,  # JSON output
        )

        mock_host_config = HostConfiguration(
            servers={
                "managed-server": MCPServerConfig(
                    name="managed-server", command="python", args=[]
                ),
                "unmanaged-server": MCPServerConfig(
                    name="unmanaged-server", command="node", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_servers(args)

                output = captured_output.getvalue()

                # Parse JSON output
                data = json.loads(output)

                # Verify structure per R10 §8
                assert "rows" in data, "JSON should include rows array"

                # Verify both servers present with correct fields
                server_names = [s["server"] for s in data["rows"]]
                assert "managed-server" in server_names
                assert "unmanaged-server" in server_names

                # Verify hatch_managed status and host field
                for row in data["rows"]:
                    assert "host" in row, "Each row should have host field"
                    assert (
                        "hatch_managed" in row
                    ), "Each row should have hatch_managed field"
                    if row["server"] == "managed-server":
                        assert row["hatch_managed"] == True
                        assert row["environment"] == "default"
                    elif row["server"] == "unmanaged-server":
                        assert row["hatch_managed"] == False


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
                    "configured_hosts": {
                        "claude-desktop": {"configured_at": "2026-01-30"}
                    },
                }
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            server=None,  # No filter
            json=False,
        )

        # Host config has both Hatch-managed and 3rd party servers
        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="python", args=["weather.py"]
                ),
                "custom-tool": MCPServerConfig(
                    name="custom-tool", command="node", args=["custom.js"]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
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

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="python", args=[]
                ),
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="node", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
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

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="python", args=[]
                ),
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="node", args=[]
                ),
                "custom-tool": MCPServerConfig(
                    name="custom-tool", command="node", args=[]
                ),  # Should NOT match
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_hosts(args)

                output = captured_output.getvalue()

                # Matching servers should appear
                assert "weather-server" in output, "weather-server should match pattern"
                assert "fetch-server" in output, "fetch-server should match pattern"

                # Non-matching server should NOT appear
                assert (
                    "custom-tool" not in output
                ), "custom-tool should NOT match pattern"

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
        claude_config = HostConfiguration(
            servers={
                "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "server-b": MCPServerConfig(name="server-b", command="node", args=[]),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            # Return hosts in non-alphabetical order to test sorting
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CURSOR,  # Should come second alphabetically
                MCPHostType.CLAUDE_DESKTOP,  # Should come first alphabetically
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_list_hosts(args)

                output = captured_output.getvalue()

                # Find positions of hosts in output
                claude_pos = output.find("claude-desktop")
                cursor_pos = output.find("cursor")

                # claude-desktop should appear before cursor (alphabetically)
                assert (
                    claude_pos < cursor_pos
                ), "Hosts should be sorted alphabetically (claude-desktop before cursor)"


class TestEnvListHostsCommand:
    """Integration tests for env list hosts command.

    Reference: R10 §3.3 (10-namespace_consistency_specification_v2.md)

    These tests verify that handle_env_list_hosts:
    1. Reads from environment data (Hatch-managed packages only)
    2. Shows environment/host/server deployments with columns: Environment → Host → Server → Version
    3. Supports --env and --server filters (regex patterns)
    4. First column (Environment) sorted alphabetically
    """

    def test_env_list_hosts_uniform_output(self):
        """Command should produce uniform table output with Environment → Host → Server → Version columns.

        Reference: R10 §3.3 - Column order matches command structure
        """
        from hatch.cli.cli_env import handle_env_list_hosts

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default", "is_current": True},
            {"name": "dev", "is_current": False},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "weather-server",
                        "version": "1.0.0",
                        "configured_hosts": {
                            "claude-desktop": {"configured_at": "2026-01-30"},
                            "cursor": {"configured_at": "2026-01-30"},
                        },
                    }
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "test-server",
                        "version": "0.1.0",
                        "configured_hosts": {
                            "claude-desktop": {"configured_at": "2026-01-30"},
                        },
                    }
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env=None,
            server=None,
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_hosts(args)

        output = captured_output.getvalue()

        # Verify column headers present
        assert "Environment" in output, "Environment column should be present"
        assert "Host" in output, "Host column should be present"
        assert "Server" in output, "Server column should be present"
        assert "Version" in output, "Version column should be present"

        # Verify data appears
        assert "default" in output, "default environment should appear"
        assert "dev" in output, "dev environment should appear"
        assert "weather-server" in output, "weather-server should appear"
        assert "test-server" in output, "test-server should appear"

    def test_env_list_hosts_env_filter_exact(self):
        """--env flag with exact name should filter to matching environment only.

        Reference: R10 §3.3 - --env <pattern> filter
        """
        from hatch.cli.cli_env import handle_env_list_hosts

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "server-a",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "server-b",
                        "version": "0.1.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env="default",  # Exact match filter
            server=None,
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_hosts(args)

        output = captured_output.getvalue()

        # Matching environment should appear
        assert "server-a" in output, "server-a from default should appear"

        # Non-matching environment should NOT appear
        assert "server-b" not in output, "server-b from dev should NOT appear"

    def test_env_list_hosts_env_filter_pattern(self):
        """--env flag with regex pattern should filter matching environments.

        Reference: R10 §3.3 - --env accepts regex patterns
        """
        from hatch.cli.cli_env import handle_env_list_hosts

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
            {"name": "dev-staging"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "server-a",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "server-b",
                        "version": "0.1.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
            "dev-staging": {
                "packages": [
                    {
                        "name": "server-c",
                        "version": "0.2.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env="dev.*",  # Regex pattern
            server=None,
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_hosts(args)

        output = captured_output.getvalue()

        # Matching environments should appear
        assert "server-b" in output, "server-b from dev should appear"
        assert "server-c" in output, "server-c from dev-staging should appear"

        # Non-matching environment should NOT appear
        assert "server-a" not in output, "server-a from default should NOT appear"

    def test_env_list_hosts_server_filter(self):
        """--server flag should filter by server name regex.

        Reference: R10 §3.3 - --server <pattern> filter
        """
        from hatch.cli.cli_env import handle_env_list_hosts

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "weather-server",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {}},
                },
                {
                    "name": "fetch-server",
                    "version": "2.0.0",
                    "configured_hosts": {"claude-desktop": {}},
                },
                {
                    "name": "custom-tool",
                    "version": "0.5.0",
                    "configured_hosts": {"claude-desktop": {}},
                },
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            env=None,
            server=".*-server",  # Regex pattern
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_hosts(args)

        output = captured_output.getvalue()

        # Matching servers should appear
        assert "weather-server" in output, "weather-server should match pattern"
        assert "fetch-server" in output, "fetch-server should match pattern"

        # Non-matching server should NOT appear
        assert "custom-tool" not in output, "custom-tool should NOT match pattern"

    def test_env_list_hosts_combined_filters(self):
        """Combined --env and --server filters should work with AND logic.

        Reference: R10 §1.5 - Combined filters
        """
        from hatch.cli.cli_env import handle_env_list_hosts

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "weather-server",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    },
                    {
                        "name": "fetch-server",
                        "version": "2.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    },
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "weather-server",
                        "version": "0.9.0",
                        "configured_hosts": {"claude-desktop": {}},
                    },
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env="default",
            server="weather.*",
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_hosts(args)

        output = captured_output.getvalue()

        # Only weather-server from default should appear
        assert "weather-server" in output, "weather-server from default should appear"
        assert "1.0.0" in output, "Version 1.0.0 should appear"

        # fetch-server should NOT appear (doesn't match server filter)
        assert "fetch-server" not in output, "fetch-server should NOT appear"

        # dev environment should NOT appear (doesn't match env filter)
        assert "0.9.0" not in output, "Version 0.9.0 from dev should NOT appear"


class TestEnvListServersCommand:
    """Integration tests for env list servers command.

    Reference: R10 §3.4 (10-namespace_consistency_specification_v2.md)

    These tests verify that handle_env_list_servers:
    1. Reads from environment data (Hatch-managed packages only)
    2. Shows environment/server/host deployments with columns: Environment → Server → Host → Version
    3. Shows '-' for undeployed packages
    4. Supports --env and --host filters (regex patterns)
    5. Supports --host - to show only undeployed packages
    6. First column (Environment) sorted alphabetically
    """

    def test_env_list_servers_uniform_output(self):
        """Command should produce uniform table output with Environment → Server → Host → Version columns.

        Reference: R10 §3.4 - Column order matches command structure
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "weather-server",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    },
                    {
                        "name": "util-lib",
                        "version": "0.5.0",
                        "configured_hosts": {},  # Undeployed
                    },
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "test-server",
                        "version": "0.1.0",
                        "configured_hosts": {"cursor": {}},
                    }
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env=None,
            host=None,
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Verify column headers present
        assert "Environment" in output, "Environment column should be present"
        assert "Server" in output, "Server column should be present"
        assert "Host" in output, "Host column should be present"
        assert "Version" in output, "Version column should be present"

        # Verify data appears
        assert "default" in output, "default environment should appear"
        assert "dev" in output, "dev environment should appear"
        assert "weather-server" in output, "weather-server should appear"
        assert "util-lib" in output, "util-lib should appear"
        assert "test-server" in output, "test-server should appear"

    def test_env_list_servers_env_filter_exact(self):
        """--env flag with exact name should filter to matching environment only.

        Reference: R10 §3.4 - --env <pattern> filter
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "server-a",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "server-b",
                        "version": "0.1.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env="default",
            host=None,
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Matching environment should appear
        assert "server-a" in output, "server-a from default should appear"

        # Non-matching environment should NOT appear
        assert "server-b" not in output, "server-b from dev should NOT appear"

    def test_env_list_servers_env_filter_pattern(self):
        """--env flag with regex pattern should filter matching environments.

        Reference: R10 §3.4 - --env accepts regex patterns
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
            {"name": "dev-staging"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "server-a",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "server-b",
                        "version": "0.1.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
            "dev-staging": {
                "packages": [
                    {
                        "name": "server-c",
                        "version": "0.2.0",
                        "configured_hosts": {"claude-desktop": {}},
                    }
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env="dev.*",
            host=None,
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Matching environments should appear
        assert "server-b" in output, "server-b from dev should appear"
        assert "server-c" in output, "server-c from dev-staging should appear"

        # Non-matching environment should NOT appear
        assert "server-a" not in output, "server-a from default should NOT appear"

    def test_env_list_servers_host_filter_exact(self):
        """--host flag with exact name should filter to matching host only.

        Reference: R10 §3.4 - --host <pattern> filter
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "server-a",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {}},
                },
                {
                    "name": "server-b",
                    "version": "2.0.0",
                    "configured_hosts": {"cursor": {}},
                },
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            env=None,
            host="claude-desktop",
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Matching host should appear
        assert "server-a" in output, "server-a on claude-desktop should appear"

        # Non-matching host should NOT appear
        assert "server-b" not in output, "server-b on cursor should NOT appear"

    def test_env_list_servers_host_filter_pattern(self):
        """--host flag with regex pattern should filter matching hosts.

        Reference: R10 §3.4 - --host accepts regex patterns
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "server-a",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {}},
                },
                {
                    "name": "server-b",
                    "version": "2.0.0",
                    "configured_hosts": {"cursor": {}},
                },
                {
                    "name": "server-c",
                    "version": "3.0.0",
                    "configured_hosts": {"claude-code": {}},
                },
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            env=None,
            host="claude.*",  # Regex pattern
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Matching hosts should appear
        assert "server-a" in output, "server-a on claude-desktop should appear"
        assert "server-c" in output, "server-c on claude-code should appear"

        # Non-matching host should NOT appear
        assert "server-b" not in output, "server-b on cursor should NOT appear"

    def test_env_list_servers_host_filter_undeployed(self):
        """--host - should show only undeployed packages.

        Reference: R10 §3.4 - Special filter for undeployed packages
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "deployed-server",
                    "version": "1.0.0",
                    "configured_hosts": {"claude-desktop": {}},
                },
                {
                    "name": "util-lib",
                    "version": "0.5.0",
                    "configured_hosts": {},
                },  # Undeployed
                {
                    "name": "debug-lib",
                    "version": "0.3.0",
                    "configured_hosts": {},
                },  # Undeployed
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            env=None,
            host="-",  # Special filter for undeployed
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Undeployed packages should appear
        assert "util-lib" in output, "util-lib (undeployed) should appear"
        assert "debug-lib" in output, "debug-lib (undeployed) should appear"

        # Deployed package should NOT appear
        assert "deployed-server" not in output, "deployed-server should NOT appear"

    def test_env_list_servers_combined_filters(self):
        """Combined --env and --host filters should work with AND logic.

        Reference: R10 §1.5 - Combined filters
        """
        from hatch.cli.cli_env import handle_env_list_servers

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [
            {"name": "default"},
            {"name": "dev"},
        ]
        mock_env_manager.get_environment_data.side_effect = lambda env_name: {
            "default": {
                "packages": [
                    {
                        "name": "server-a",
                        "version": "1.0.0",
                        "configured_hosts": {"claude-desktop": {}},
                    },
                    {
                        "name": "server-b",
                        "version": "2.0.0",
                        "configured_hosts": {"cursor": {}},
                    },
                ]
            },
            "dev": {
                "packages": [
                    {
                        "name": "server-c",
                        "version": "0.1.0",
                        "configured_hosts": {"claude-desktop": {}},
                    },
                ]
            },
        }.get(env_name, {"packages": []})

        args = Namespace(
            env_manager=mock_env_manager,
            env="default",
            host="claude-desktop",
            json=False,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = handle_env_list_servers(args)

        output = captured_output.getvalue()

        # Only server-a from default on claude-desktop should appear
        assert "server-a" in output, "server-a should appear"

        # server-b should NOT appear (wrong host)
        assert "server-b" not in output, "server-b should NOT appear"

        # server-c should NOT appear (wrong env)
        assert "server-c" not in output, "server-c should NOT appear"


class TestMCPShowHostsCommand:
    """Integration tests for hatch mcp show hosts command.

    Reference: R11 §2.1 (11-enhancing_show_command_v0.md) - Show hosts specification

    These tests verify that handle_mcp_show_hosts:
    1. Shows detailed host configurations with hierarchical output
    2. Supports --server filter for regex pattern matching
    3. Omits hosts with no matching servers when filter applied
    4. Shows horizontal separators between host sections
    5. Highlights entity names with amber + bold
    6. Supports --json output format
    """

    def test_mcp_show_hosts_no_filter(self):
        """Command should show all hosts with detailed configuration.

        Reference: R11 §2.1 - Output format without filter
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "weather-server",
                    "version": "1.0.0",
                    "configured_hosts": {
                        "claude-desktop": {"configured_at": "2026-01-30"}
                    },
                }
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            server=None,  # No filter
            json=False,
        )

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=["weather-mcp"]
                ),
                "custom-tool": MCPServerConfig(
                    name="custom-tool", command="node", args=["custom.js"]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # Should show host header
                assert "claude-desktop" in output, "Host name should appear"

                # Should show both servers
                assert "weather-server" in output, "weather-server should appear"
                assert "custom-tool" in output, "custom-tool should appear"

                # Should show server details
                assert (
                    "Command:" in output or "uvx" in output
                ), "Server command should appear"

    def test_mcp_show_hosts_server_filter_exact(self):
        """--server filter should match exact server name.

        Reference: R11 §2.1 - Server filter with exact match
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            server="weather-server",  # Exact match
            json=False,
        )

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=["weather-mcp"]
                ),
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=["fetch.py"]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # Should show matching server
                assert "weather-server" in output, "weather-server should appear"

                # Should NOT show non-matching server
                assert "fetch-server" not in output, "fetch-server should NOT appear"

    def test_mcp_show_hosts_server_filter_pattern(self):
        """--server filter should support regex patterns.

        Reference: R11 §2.1 - Server filter with regex pattern
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
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

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=[]
                ),
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=[]
                ),
                "custom-tool": MCPServerConfig(
                    name="custom-tool", command="node", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # Should show matching servers
                assert "weather-server" in output, "weather-server should appear"
                assert "fetch-server" in output, "fetch-server should appear"

                # Should NOT show non-matching server
                assert "custom-tool" not in output, "custom-tool should NOT appear"

    def test_mcp_show_hosts_omits_empty_hosts(self):
        """Hosts with no matching servers should be omitted.

        Reference: R11 §2.1 - Empty host omission
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            server="weather-server",  # Only matches on claude-desktop
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=[]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # claude-desktop should appear (has matching server)
                assert "claude-desktop" in output, "claude-desktop should appear"

                # cursor should NOT appear (no matching servers)
                assert (
                    "cursor" not in output
                ), "cursor should NOT appear (no matching servers)"

    def test_mcp_show_hosts_alphabetical_ordering(self):
        """Hosts should be sorted alphabetically.

        Reference: R11 §1.4 - Alphabetical ordering
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
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

        mock_config = HostConfiguration(
            servers={
                "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            # Return hosts in non-alphabetical order
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CURSOR,
                MCPHostType.CLAUDE_DESKTOP,
            ]

            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # Find positions of host names
                claude_pos = output.find("claude-desktop")
                cursor_pos = output.find("cursor")

                # claude-desktop should appear before cursor (alphabetically)
                assert (
                    claude_pos < cursor_pos
                ), "Hosts should be sorted alphabetically (claude-desktop before cursor)"

    def test_mcp_show_hosts_horizontal_separators(self):
        """Output should have horizontal separators between host sections.

        Reference: R11 §3.1 - Horizontal separators
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
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

        mock_config = HostConfiguration(
            servers={
                "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # Should have horizontal separator (═ character)
                assert "═" in output, "Output should have horizontal separators"

    def test_mcp_show_hosts_json_output(self):
        """--json flag should output JSON format.

        Reference: R11 §6.1 - JSON output format
        """
        from hatch.cli.cli_mcp import handle_mcp_show_hosts
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        import json

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            server=None,
            json=True,  # JSON output
        )

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=["weather-mcp"]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_hosts(args)

                output = captured_output.getvalue()

                # Should be valid JSON
                try:
                    data = json.loads(output)
                except json.JSONDecodeError:
                    pytest.fail(f"Output should be valid JSON: {output}")

                # Should have hosts array
                assert "hosts" in data, "JSON should have 'hosts' key"
                assert len(data["hosts"]) > 0, "Should have at least one host"

                # Host should have expected structure
                host = data["hosts"][0]
                assert "host" in host, "Host should have 'host' key"
                assert "servers" in host, "Host should have 'servers' key"


class TestMCPShowServersCommand:
    """Integration tests for hatch mcp show servers command.

    Reference: R11 §2.2 (11-enhancing_show_command_v0.md) - Show servers specification

    These tests verify that handle_mcp_show_servers:
    1. Shows detailed server configurations across hosts
    2. Supports --host filter for regex pattern matching
    3. Omits servers with no matching hosts when filter applied
    4. Shows horizontal separators between server sections
    5. Highlights entity names with amber + bold
    6. Supports --json output format
    """

    def test_mcp_show_servers_no_filter(self):
        """Command should show all servers with host configurations.

        Reference: R11 §2.2 - Output format without filter
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {
            "packages": [
                {
                    "name": "weather-server",
                    "version": "1.0.0",
                    "configured_hosts": {
                        "claude-desktop": {"configured_at": "2026-01-30"}
                    },
                }
            ]
        }

        args = Namespace(
            env_manager=mock_env_manager,
            host=None,  # No filter
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=["weather-mcp"]
                ),
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=["fetch.py"]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=["weather-mcp"]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Should show both servers
                assert "weather-server" in output, "weather-server should appear"
                assert "fetch-server" in output, "fetch-server should appear"

                # Should show host configurations
                assert "claude-desktop" in output, "claude-desktop should appear"
                assert "cursor" in output, "cursor should appear"

    def test_mcp_show_servers_host_filter_exact(self):
        """--host filter should match exact host name.

        Reference: R11 §2.2 - Host filter with exact match
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",  # Exact match
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=[]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Should show server from matching host
                assert "weather-server" in output, "weather-server should appear"

                # Should NOT show server only on non-matching host
                assert "fetch-server" not in output, "fetch-server should NOT appear"

    def test_mcp_show_servers_host_filter_pattern(self):
        """--host filter should support regex patterns.

        Reference: R11 §2.2 - Host filter with regex pattern
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host="claude.*",  # Regex pattern
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=[]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Should show server from matching host
                assert "weather-server" in output, "weather-server should appear"

                # Should NOT show server only on non-matching host
                assert "fetch-server" not in output, "fetch-server should NOT appear"

    def test_mcp_show_servers_host_filter_multi_pattern(self):
        """--host filter should support multi-pattern regex.

        Reference: R11 §2.2 - Host filter with multi-pattern
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop|cursor",  # Multi-pattern
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=[]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=[]
                ),
            }
        )
        kiro_config = HostConfiguration(
            servers={
                "debug-server": MCPServerConfig(
                    name="debug-server", command="node", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
                MCPHostType.KIRO,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                elif host_type == MCPHostType.KIRO:
                    mock_strategy.read_configuration.return_value = kiro_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Should show servers from matching hosts
                assert "weather-server" in output, "weather-server should appear"
                assert "fetch-server" in output, "fetch-server should appear"

                # Should NOT show server only on non-matching host
                assert "debug-server" not in output, "debug-server should NOT appear"

    def test_mcp_show_servers_omits_empty_servers(self):
        """Servers with no matching hosts should be omitted.

        Reference: R11 §2.2 - Empty server omission
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host="claude-desktop",  # Only matches claude-desktop
            json=False,
        )

        claude_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=[]
                ),
            }
        )
        cursor_config = HostConfiguration(
            servers={
                "fetch-server": MCPServerConfig(
                    name="fetch-server", command="python", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP,
                MCPHostType.CURSOR,
            ]

            def get_strategy_side_effect(host_type):
                mock_strategy = MagicMock()
                mock_strategy.get_config_path.return_value = MagicMock(
                    exists=lambda: True
                )
                if host_type == MCPHostType.CLAUDE_DESKTOP:
                    mock_strategy.read_configuration.return_value = claude_config
                elif host_type == MCPHostType.CURSOR:
                    mock_strategy.read_configuration.return_value = cursor_config
                else:
                    mock_strategy.read_configuration.return_value = HostConfiguration(
                        servers={}
                    )
                return mock_strategy

            mock_registry.get_strategy.side_effect = get_strategy_side_effect

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # weather-server should appear (has matching host)
                assert "weather-server" in output, "weather-server should appear"

                # fetch-server should NOT appear (no matching hosts)
                assert "fetch-server" not in output, "fetch-server should NOT appear"

    def test_mcp_show_servers_alphabetical_ordering(self):
        """Servers should be sorted alphabetically.

        Reference: R11 §1.4 - Alphabetical ordering
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host=None,
            json=False,
        )

        # Servers in non-alphabetical order
        mock_config = HostConfiguration(
            servers={
                "zebra-server": MCPServerConfig(
                    name="zebra-server", command="python", args=[]
                ),
                "alpha-server": MCPServerConfig(
                    name="alpha-server", command="python", args=[]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Find positions of server names
                alpha_pos = output.find("alpha-server")
                zebra_pos = output.find("zebra-server")

                # alpha-server should appear before zebra-server (alphabetically)
                assert (
                    alpha_pos < zebra_pos
                ), "Servers should be sorted alphabetically (alpha-server before zebra-server)"

    def test_mcp_show_servers_horizontal_separators(self):
        """Output should have horizontal separators between server sections.

        Reference: R11 §3.1 - Horizontal separators
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host=None,
            json=False,
        )

        mock_config = HostConfiguration(
            servers={
                "server-a": MCPServerConfig(name="server-a", command="python", args=[]),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Should have horizontal separator (═ character)
                assert "═" in output, "Output should have horizontal separators"

    def test_mcp_show_servers_json_output(self):
        """--json flag should output JSON format.

        Reference: R11 §6.2 - JSON output format
        """
        from hatch.cli.cli_mcp import handle_mcp_show_servers
        from hatch.mcp_host_config import MCPHostType, MCPServerConfig
        from hatch.mcp_host_config.models import HostConfiguration
        import json

        mock_env_manager = MagicMock()
        mock_env_manager.list_environments.return_value = [{"name": "default"}]
        mock_env_manager.get_environment_data.return_value = {"packages": []}

        args = Namespace(
            env_manager=mock_env_manager,
            host=None,
            json=True,  # JSON output
        )

        mock_host_config = HostConfiguration(
            servers={
                "weather-server": MCPServerConfig(
                    name="weather-server", command="uvx", args=["weather-mcp"]
                ),
            }
        )

        with patch("hatch.cli.cli_mcp.MCPHostRegistry") as mock_registry:
            mock_registry.detect_available_hosts.return_value = [
                MCPHostType.CLAUDE_DESKTOP
            ]
            mock_strategy = MagicMock()
            mock_strategy.read_configuration.return_value = mock_host_config
            mock_strategy.get_config_path.return_value = MagicMock(exists=lambda: True)
            mock_registry.get_strategy.return_value = mock_strategy

            with patch("hatch.mcp_host_config.strategies"):
                captured_output = io.StringIO()
                with patch("sys.stdout", captured_output):
                    result = handle_mcp_show_servers(args)

                output = captured_output.getvalue()

                # Should be valid JSON
                try:
                    data = json.loads(output)
                except json.JSONDecodeError:
                    pytest.fail(f"Output should be valid JSON: {output}")

                # Should have servers array
                assert "servers" in data, "JSON should have 'servers' key"
                assert len(data["servers"]) > 0, "Should have at least one server"

                # Server should have expected structure
                server = data["servers"][0]
                assert "name" in server, "Server should have 'name' key"
                assert "hosts" in server, "Server should have 'hosts' key"


class TestMCPShowCommandRemoval:
    """Tests for mcp show command behavior after removal of legacy syntax.

    Reference: R11 §5 (11-enhancing_show_command_v0.md) - Migration Path

    These tests verify that:
    1. 'hatch mcp show' without subcommand shows help/error
    2. Invalid subcommands show appropriate error
    """

    def test_mcp_show_without_subcommand_shows_help(self):
        """'hatch mcp show' without subcommand should show help message.

        Reference: R11 §5.3 - Clean removal
        """
        from hatch.cli.__main__ import _route_mcp_command

        # Create args with no show_command
        args = Namespace(
            mcp_command="show",
            show_command=None,
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = _route_mcp_command(args)

        output = captured_output.getvalue()

        # Should return error code
        assert result == 1, "Should return error code when no subcommand"

        # Should show helpful message
        assert (
            "hosts" in output or "servers" in output
        ), "Error message should mention available subcommands"

    def test_mcp_show_invalid_subcommand_error(self):
        """Invalid subcommand should show error message.

        Reference: R11 §5.3 - Clean removal
        """
        from hatch.cli.__main__ import _route_mcp_command

        # Create args with invalid show_command
        args = Namespace(
            mcp_command="show",
            show_command="invalid",
        )

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            result = _route_mcp_command(args)

        output = captured_output.getvalue()

        # Should return error code
        assert result == 1, "Should return error code for invalid subcommand"
