"""Test utilities for CLI handler testing.

This module provides helper functions to simplify test setup for CLI handlers,
particularly for creating Namespace objects and mock managers.

These utilities reduce boilerplate in test files and ensure consistent
test patterns across the CLI test suite.
"""

import sys
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# Add the parent directory to the path to import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def create_mcp_configure_args(
    host: str = "claude-desktop",
    server_name: str = "test-server",
    command: Optional[str] = "python",
    args: Optional[List[str]] = None,
    env: Optional[List[str]] = None,
    url: Optional[str] = None,
    header: Optional[List[str]] = None,
    http_url: Optional[str] = None,
    disabled: bool = False,
    timeout: Optional[int] = None,
    include_tools: Optional[List[str]] = None,
    exclude_tools: Optional[List[str]] = None,
    inputs: Optional[List[str]] = None,
    auto_approve_tools: Optional[List[str]] = None,
    disable_tools: Optional[List[str]] = None,
    enabled: Optional[bool] = None,
    roots: Optional[List[str]] = None,
    transport: Optional[str] = None,
    transport_options: Optional[List[str]] = None,
    env_file: Optional[str] = None,
    working_dir: Optional[str] = None,
    shell: Optional[bool] = None,
    type_field: Optional[str] = None,
    scope: Optional[str] = None,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
) -> Namespace:
    """Create a Namespace object for handle_mcp_configure testing.

    This helper creates a properly structured Namespace object that matches
    the expected arguments for handle_mcp_configure, making tests more
    readable and maintainable.

    Args:
        host: Target MCP host (e.g., 'claude-desktop', 'cursor', 'vscode')
        server_name: Name of the MCP server to configure
        command: Command to run for local servers
        args: Arguments for the command
        env: Environment variables in KEY=VALUE format
        url: URL for SSE remote servers
        header: HTTP headers in KEY=VALUE format
        http_url: URL for HTTP remote servers (Gemini only)
        disabled: Whether the server should be disabled
        timeout: Server timeout in seconds
        include_tools: Tools to include (Gemini)
        exclude_tools: Tools to exclude (Gemini)
        inputs: VSCode input configurations
        auto_approve_tools: Tools to auto-approve (Kiro)
        disable_tools: Tools to disable (Kiro)
        enabled: Whether server is enabled (Codex)
        roots: Root directories (Codex)
        transport: Transport type (Codex)
        transport_options: Transport options (Codex)
        env_file: Environment file path (Codex)
        working_dir: Working directory (Codex)
        shell: Use shell execution (Codex)
        type_field: Server type field
        scope: Configuration scope
        no_backup: Disable backup creation
        dry_run: Preview changes without applying
        auto_approve: Skip confirmation prompts

    Returns:
        Namespace object with all arguments set
    """
    if args is None:
        args = ["server.py"]

    return Namespace(
        host=host,
        server_name=server_name,
        command=command,
        args=args,
        env=env,
        url=url,
        header=header,
        http_url=http_url,
        disabled=disabled,
        timeout=timeout,
        include_tools=include_tools,
        exclude_tools=exclude_tools,
        inputs=inputs,
        auto_approve_tools=auto_approve_tools,
        disable_tools=disable_tools,
        enabled=enabled,
        roots=roots,
        transport=transport,
        transport_options=transport_options,
        env_file=env_file,
        working_dir=working_dir,
        shell=shell,
        type_field=type_field,
        scope=scope,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def create_mock_env_manager(
    current_env: str = "default",
    environments: Optional[List[str]] = None,
    packages: Optional[Dict[str, Any]] = None,
) -> MagicMock:
    """Create a mock HatchEnvironmentManager for testing.

    Args:
        current_env: Name of the current environment
        environments: List of available environment names
        packages: Dictionary of packages in the environment

    Returns:
        MagicMock configured as a HatchEnvironmentManager
    """
    if environments is None:
        environments = ["default"]
    if packages is None:
        packages = {}

    mock_manager = MagicMock()
    mock_manager.get_current_environment.return_value = current_env
    mock_manager.list_environments.return_value = environments
    mock_manager.get_environment_packages.return_value = packages
    mock_manager.environment_exists.side_effect = lambda name: name in environments

    return mock_manager


def create_mock_mcp_manager(
    hosts: Optional[List[str]] = None,
    servers: Optional[Dict[str, Dict[str, Any]]] = None,
) -> MagicMock:
    """Create a mock MCPHostConfigurationManager for testing.

    Args:
        hosts: List of available host names
        servers: Dictionary mapping host names to their server configurations

    Returns:
        MagicMock configured as an MCPHostConfigurationManager
    """
    if hosts is None:
        hosts = ["claude-desktop", "cursor", "vscode"]
    if servers is None:
        servers = {}

    mock_manager = MagicMock()
    mock_manager.list_hosts.return_value = hosts
    mock_manager.get_servers.side_effect = lambda host: servers.get(host, {})

    # Configure successful operations by default
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.backup_path = None
    mock_manager.configure_server.return_value = mock_result
    mock_manager.remove_server.return_value = mock_result

    return mock_manager
