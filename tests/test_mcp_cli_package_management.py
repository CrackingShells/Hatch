"""
Test suite for MCP CLI package management enhancements.

This module tests the enhanced package management commands with MCP host
configuration integration following CrackingShells testing standards.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add the parent directory to the path to import wobble
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wobble.decorators import integration_test, regression_test
except ImportError:
    # Fallback decorators if wobble is not available
    def regression_test(func):
        return func

    def integration_test(scope="component"):
        def decorator(func):
            return func

        return decorator


from hatch.cli_hatch import (
    get_package_mcp_server_config,
    parse_host_list,
    request_confirmation,
)
from hatch.mcp_host_config import MCPHostType, MCPServerConfig


class TestMCPCLIPackageManagement(unittest.TestCase):
    """Test suite for MCP CLI package management enhancements."""

    @regression_test
    def test_parse_host_list_comma_separated(self):
        """Test parsing comma-separated host list."""
        hosts = parse_host_list("claude-desktop,cursor,vscode")
        expected = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR, MCPHostType.VSCODE]
        self.assertEqual(hosts, expected)

    @regression_test
    def test_parse_host_list_single_host(self):
        """Test parsing single host."""
        hosts = parse_host_list("claude-desktop")
        expected = [MCPHostType.CLAUDE_DESKTOP]
        self.assertEqual(hosts, expected)

    @regression_test
    def test_parse_host_list_empty(self):
        """Test parsing empty host list."""
        hosts = parse_host_list("")
        self.assertEqual(hosts, [])

    @regression_test
    def test_parse_host_list_none(self):
        """Test parsing None host list."""
        hosts = parse_host_list(None)
        self.assertEqual(hosts, [])

    @regression_test
    def test_parse_host_list_all(self):
        """Test parsing 'all' host list."""
        with patch(
            "hatch.cli_hatch.MCPHostRegistry.detect_available_hosts"
        ) as mock_detect:
            mock_detect.return_value = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR]
            hosts = parse_host_list("all")
            expected = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR]
            self.assertEqual(hosts, expected)
            mock_detect.assert_called_once()

    @regression_test
    def test_parse_host_list_invalid_host(self):
        """Test parsing invalid host raises ValueError."""
        with self.assertRaises(ValueError) as context:
            parse_host_list("invalid-host")

        self.assertIn("Unknown host 'invalid-host'", str(context.exception))
        self.assertIn("Available:", str(context.exception))

    @regression_test
    def test_parse_host_list_mixed_valid_invalid(self):
        """Test parsing mixed valid and invalid hosts."""
        with self.assertRaises(ValueError) as context:
            parse_host_list("claude-desktop,invalid-host,cursor")

        self.assertIn("Unknown host 'invalid-host'", str(context.exception))

    @regression_test
    def test_parse_host_list_whitespace_handling(self):
        """Test parsing host list with whitespace."""
        hosts = parse_host_list(" claude-desktop , cursor , vscode ")
        expected = [MCPHostType.CLAUDE_DESKTOP, MCPHostType.CURSOR, MCPHostType.VSCODE]
        self.assertEqual(hosts, expected)

    @regression_test
    def test_request_confirmation_auto_approve(self):
        """Test confirmation with auto-approve flag."""
        result = request_confirmation("Test message?", auto_approve=True)
        self.assertTrue(result)

    @regression_test
    def test_request_confirmation_user_yes(self):
        """Test confirmation with user saying yes."""
        with patch("builtins.input", return_value="y"):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertTrue(result)

    @regression_test
    def test_request_confirmation_user_yes_full(self):
        """Test confirmation with user saying 'yes'."""
        with patch("builtins.input", return_value="yes"):
            result = request_confirmation("Test message?", auto_approve=False)
            self.assertTrue(result)

    @regression_test
    def test_request_confirmation_user_no(self):
        """Test confirmation with user saying no."""
        with patch.dict("os.environ", {"HATCH_AUTO_APPROVE": ""}, clear=False):
            with patch("builtins.input", return_value="n"):
                result = request_confirmation("Test message?", auto_approve=False)
                self.assertFalse(result)

    @regression_test
    def test_request_confirmation_user_no_full(self):
        """Test confirmation with user saying 'no'."""
        with patch.dict("os.environ", {"HATCH_AUTO_APPROVE": ""}, clear=False):
            with patch("builtins.input", return_value="no"):
                result = request_confirmation("Test message?", auto_approve=False)
                self.assertFalse(result)

    @regression_test
    def test_request_confirmation_user_empty(self):
        """Test confirmation with user pressing enter (default no)."""
        with patch.dict("os.environ", {"HATCH_AUTO_APPROVE": ""}, clear=False):
            with patch("builtins.input", return_value=""):
                result = request_confirmation("Test message?", auto_approve=False)
                self.assertFalse(result)

    @integration_test(scope="component")
    def test_package_add_argument_parsing(self):
        """Test package add command argument parsing with MCP flags."""
        import argparse

        from hatch.cli_hatch import main

        # Mock argparse to capture parsed arguments
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.command = "package"
            mock_args.pkg_command = "add"
            mock_args.package_path_or_name = "test-package"
            mock_args.host = "claude-desktop,cursor"
            mock_args.env = None
            mock_args.version = None
            mock_args.force_download = False
            mock_args.refresh_registry = False
            mock_args.auto_approve = False
            mock_parse.return_value = mock_args

            # Mock environment manager to avoid actual operations
            with patch("hatch.cli_hatch.HatchEnvironmentManager") as mock_env_manager:
                mock_env_manager.return_value.add_package_to_environment.return_value = True
                mock_env_manager.return_value.get_current_environment.return_value = (
                    "default"
                )

                # Mock MCP manager
                with patch("hatch.cli_hatch.MCPHostConfigurationManager"):
                    with patch("builtins.print") as mock_print:
                        result = main()

                        # Should succeed
                        self.assertEqual(result, 0)

                        # Should print success message
                        mock_print.assert_any_call(
                            "Successfully added package: test-package"
                        )

    @integration_test(scope="component")
    def test_package_sync_argument_parsing(self):
        """Test package sync command argument parsing."""
        import argparse

        from hatch.cli_hatch import main

        # Mock argparse to capture parsed arguments
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.command = "package"
            mock_args.pkg_command = "sync"
            mock_args.package_name = "test-package"
            mock_args.host = "claude-desktop,cursor"
            mock_args.env = None
            mock_args.dry_run = True  # Use dry run to avoid actual configuration
            mock_args.auto_approve = False
            mock_args.no_backup = False
            mock_parse.return_value = mock_args

            # Mock the get_package_mcp_server_config function
            with patch(
                "hatch.cli_hatch.get_package_mcp_server_config"
            ) as mock_get_config:
                mock_server_config = MagicMock()
                mock_server_config.name = "test-package"
                mock_server_config.args = ["/path/to/server.py"]
                mock_get_config.return_value = mock_server_config

                # Mock environment manager
                with patch(
                    "hatch.cli_hatch.HatchEnvironmentManager"
                ) as mock_env_manager:
                    mock_env_manager.return_value.get_current_environment.return_value = "default"

                    # Mock MCP manager
                    with patch("hatch.cli_hatch.MCPHostConfigurationManager"):
                        with patch("builtins.print") as mock_print:
                            result = main()

                            # Should succeed
                            self.assertEqual(result, 0)

                            # Should print dry run message (new format includes dependency info)
                            mock_print.assert_any_call(
                                "[DRY RUN] Would synchronize MCP servers for 1 package(s) to hosts: ['claude-desktop', 'cursor']"
                            )

    @integration_test(scope="component")
    def test_package_sync_package_not_found(self):
        """Test package sync when package doesn't exist."""
        import argparse

        from hatch.cli_hatch import main

        # Mock argparse to capture parsed arguments
        with patch("argparse.ArgumentParser.parse_args") as mock_parse:
            mock_args = MagicMock()
            mock_args.command = "package"
            mock_args.pkg_command = "sync"
            mock_args.package_name = "nonexistent-package"
            mock_args.host = "claude-desktop"
            mock_args.env = None
            mock_args.dry_run = False
            mock_args.auto_approve = False
            mock_args.no_backup = False
            mock_parse.return_value = mock_args

            # Mock the get_package_mcp_server_config function to raise ValueError
            with patch(
                "hatch.cli_hatch.get_package_mcp_server_config"
            ) as mock_get_config:
                mock_get_config.side_effect = ValueError(
                    "Package 'nonexistent-package' not found in environment 'default'"
                )

                # Mock environment manager
                with patch(
                    "hatch.cli_hatch.HatchEnvironmentManager"
                ) as mock_env_manager:
                    mock_env_manager.return_value.get_current_environment.return_value = "default"

                    with patch("builtins.print") as mock_print:
                        result = main()

                        # Should fail
                        self.assertEqual(result, 1)

                        # Should print error message (new format)
                        mock_print.assert_any_call(
                            "Error: No MCP server configurations found for package 'nonexistent-package' or its dependencies"
                        )

    @regression_test
    def test_get_package_mcp_server_config_success(self):
        """Test successful MCP server config retrieval."""
        # Mock environment manager
        mock_env_manager = MagicMock()
        mock_env_manager.list_packages.return_value = [
            {
                "name": "test-package",
                "version": "1.0.0",
                "source": {"path": "/path/to/package"},
            }
        ]
        # Mock the Python executable method to return a proper string
        mock_env_manager.get_current_python_executable.return_value = "/path/to/python"

        # Mock file system and metadata
        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "builtins.open",
                mock_open(
                    read_data='{"package_schema_version": "1.2.1", "name": "test-package"}'
                ),
            ):
                with patch(
                    "hatch_validator.package.package_service.PackageService"
                ) as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.get_mcp_entry_point.return_value = "mcp_server.py"
                    mock_service_class.return_value = mock_service

                    config = get_package_mcp_server_config(
                        mock_env_manager, "test-env", "test-package"
                    )

                    self.assertIsInstance(config, MCPServerConfig)
                    self.assertEqual(config.name, "test-package")
                    self.assertEqual(
                        config.command, "/path/to/python"
                    )  # Now uses environment-specific Python
                    self.assertTrue(config.args[0].endswith("mcp_server.py"))

    @regression_test
    def test_get_package_mcp_server_config_package_not_found(self):
        """Test MCP server config retrieval when package not found."""
        # Mock environment manager with empty package list
        mock_env_manager = MagicMock()
        mock_env_manager.list_packages.return_value = []

        with self.assertRaises(ValueError) as context:
            get_package_mcp_server_config(
                mock_env_manager, "test-env", "nonexistent-package"
            )

        self.assertIn("Package 'nonexistent-package' not found", str(context.exception))

    @regression_test
    def test_get_package_mcp_server_config_no_metadata(self):
        """Test MCP server config retrieval when package has no metadata."""
        # Mock environment manager
        mock_env_manager = MagicMock()
        mock_env_manager.list_packages.return_value = [
            {
                "name": "test-package",
                "version": "1.0.0",
                "source": {"path": "/path/to/package"},
            }
        ]

        # Mock file system - metadata file doesn't exist
        with patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(ValueError) as context:
                get_package_mcp_server_config(
                    mock_env_manager, "test-env", "test-package"
                )

            self.assertIn("not a Hatch package", str(context.exception))


if __name__ == "__main__":
    unittest.main()
