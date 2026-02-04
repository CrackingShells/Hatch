"""Test utilities for CLI handler testing.

This module provides helper functions to simplify test setup for CLI handlers,
particularly for creating Namespace objects and mock managers.

These utilities reduce boilerplate in test files and ensure consistent
test patterns across the CLI test suite.

IMPORTANT: The attribute names in create_mcp_configure_args MUST match
the exact names expected by handle_mcp_configure in hatch/cli/cli_mcp.py.
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
    server_command: Optional[str] = "python",
    args: Optional[List[str]] = None,
    env_var: Optional[List[str]] = None,
    url: Optional[str] = None,
    header: Optional[List[str]] = None,
    timeout: Optional[int] = None,
    trust: bool = False,
    cwd: Optional[str] = None,
    env_file: Optional[str] = None,
    http_url: Optional[str] = None,
    include_tools: Optional[List[str]] = None,
    exclude_tools: Optional[List[str]] = None,
    input: Optional[List[str]] = None,
    disabled: Optional[bool] = None,
    auto_approve_tools: Optional[List[str]] = None,
    disable_tools: Optional[List[str]] = None,
    env_vars: Optional[List[str]] = None,
    startup_timeout: Optional[int] = None,
    tool_timeout: Optional[int] = None,
    enabled: Optional[bool] = None,
    bearer_token_env_var: Optional[str] = None,
    env_header: Optional[List[str]] = None,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
    _use_default_args: bool = True,
) -> Namespace:
    """Create a Namespace object for handle_mcp_configure testing.

    This helper creates a properly structured Namespace object that matches
    the expected arguments for handle_mcp_configure, making tests more
    readable and maintainable.

    IMPORTANT: Attribute names MUST match those in handle_mcp_configure:
    - server_command (not command)
    - env_var (not env)
    - input (not inputs)

    Args:
        host: Target MCP host (e.g., 'claude-desktop', 'cursor', 'vscode')
        server_name: Name of the MCP server to configure
        server_command: Command to run for local servers
        args: Arguments for the command (defaults to ['server.py'] for local servers)
        env_var: Environment variables in KEY=VALUE format
        url: URL for SSE remote servers
        header: HTTP headers in KEY=VALUE format
        timeout: Server timeout in seconds
        trust: Trust the server (Cursor)
        cwd: Working directory
        env_file: Environment file path
        http_url: URL for HTTP remote servers (Gemini only)
        include_tools: Tools to include (Gemini)
        exclude_tools: Tools to exclude (Gemini)
        input: VSCode input configurations
        disabled: Whether the server should be disabled
        auto_approve_tools: Tools to auto-approve (Kiro)
        disable_tools: Tools to disable (Kiro)
        env_vars: Additional environment variables
        startup_timeout: Startup timeout
        tool_timeout: Tool execution timeout
        enabled: Whether server is enabled
        bearer_token_env_var: Bearer token environment variable
        env_header: Environment headers
        no_backup: Disable backup creation
        dry_run: Preview changes without applying
        auto_approve: Skip confirmation prompts
        _use_default_args: If True and args is None and server_command is set, use default args

    Returns:
        Namespace object with all arguments set
    """
    # Only use default args for local servers (when command is set)
    if args is None and server_command is not None and _use_default_args:
        args = ["server.py"]

    return Namespace(
        host=host,
        server_name=server_name,
        server_command=server_command,
        args=args,
        env_var=env_var,
        url=url,
        header=header,
        timeout=timeout,
        trust=trust,
        cwd=cwd,
        env_file=env_file,
        http_url=http_url,
        include_tools=include_tools,
        exclude_tools=exclude_tools,
        input=input,
        disabled=disabled,
        auto_approve_tools=auto_approve_tools,
        disable_tools=disable_tools,
        env_vars=env_vars,
        startup_timeout=startup_timeout,
        tool_timeout=tool_timeout,
        enabled=enabled,
        bearer_token_env_var=bearer_token_env_var,
        env_header=env_header,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def create_mcp_remove_args(
    host: str = "claude-desktop",
    server_name: str = "test-server",
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
) -> Namespace:
    """Create a Namespace object for handle_mcp_remove testing.

    Args:
        host: Target MCP host
        server_name: Name of the MCP server to remove
        no_backup: Disable backup creation
        dry_run: Preview changes without applying
        auto_approve: Skip confirmation prompts

    Returns:
        Namespace object with all arguments set
    """
    return Namespace(
        host=host,
        server_name=server_name,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def create_mcp_remove_server_args(
    env_manager: Any = None,
    server_name: str = "test-server",
    host: Optional[str] = None,
    env: Optional[str] = None,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
) -> Namespace:
    """Create a Namespace object for handle_mcp_remove_server testing.

    Args:
        env_manager: Environment manager instance
        server_name: Name of the MCP server to remove
        host: Comma-separated list of target hosts
        env: Environment name
        no_backup: Disable backup creation
        dry_run: Preview changes without applying
        auto_approve: Skip confirmation prompts

    Returns:
        Namespace object with all arguments set
    """
    return Namespace(
        env_manager=env_manager,
        server_name=server_name,
        host=host,
        env=env,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def create_mcp_remove_host_args(
    env_manager: Any = None,
    host_name: str = "claude-desktop",
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
) -> Namespace:
    """Create a Namespace object for handle_mcp_remove_host testing.

    Args:
        env_manager: Environment manager instance
        host_name: Name of the host to remove configuration from
        no_backup: Disable backup creation
        dry_run: Preview changes without applying
        auto_approve: Skip confirmation prompts

    Returns:
        Namespace object with all arguments set
    """
    return Namespace(
        env_manager=env_manager,
        host_name=host_name,
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
