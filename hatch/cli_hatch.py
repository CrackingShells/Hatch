"""Command-line interface for the Hatch package manager.

This module provides the CLI functionality for Hatch, allowing users to:
- Create new package templates
- Validate packages
- Manage environments
- Manage packages within environments
"""

import argparse
import json
import logging
import shlex
import sys
from pathlib import Path
from typing import List, Optional

from hatch_validator import HatchPackageValidator
from hatch_validator.package.package_service import PackageService

from hatch.environment_manager import HatchEnvironmentManager
from hatch.mcp_host_config import (
    MCPHostConfigurationManager,
    MCPHostRegistry,
    MCPHostType,
    MCPServerConfig,
)
from hatch.mcp_host_config.models import HOST_MODEL_REGISTRY, MCPServerConfigOmni
from hatch.mcp_host_config.reporting import display_report, generate_conversion_report
from hatch.template_generator import create_package_template


# Import get_hatch_version from cli_utils (extracted in M1.2.1)
from hatch.cli.cli_utils import get_hatch_version

# Import user interaction and parsing utilities from cli_utils (extracted in M1.2.3)
from hatch.cli.cli_utils import (
    request_confirmation,
    parse_env_vars,
    parse_header,
    parse_input,
    parse_host_list,
    get_package_mcp_server_config,
)

# Import MCP handlers from cli_mcp (extracted in M1.3.1)
from hatch.cli.cli_mcp import (
    handle_mcp_discover_hosts as _handle_mcp_discover_hosts,
    handle_mcp_discover_servers as _handle_mcp_discover_servers,
    handle_mcp_list_hosts as _handle_mcp_list_hosts,
    handle_mcp_list_servers as _handle_mcp_list_servers,
    handle_mcp_backup_restore as _handle_mcp_backup_restore,
    handle_mcp_backup_list as _handle_mcp_backup_list,
    handle_mcp_backup_clean as _handle_mcp_backup_clean,
    handle_mcp_configure as _handle_mcp_configure,
)



def handle_mcp_discover_hosts():
    """Handle 'hatch mcp discover hosts' command.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_discover_hosts.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace()
    return _handle_mcp_discover_hosts(args)


def handle_mcp_discover_servers(
    env_manager: HatchEnvironmentManager, env_name: Optional[str] = None
):
    """Handle 'hatch mcp discover servers' command.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_discover_servers.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace(env_manager=env_manager, env=env_name)
    return _handle_mcp_discover_servers(args)


def handle_mcp_list_hosts(
    env_manager: HatchEnvironmentManager,
    env_name: Optional[str] = None,
    detailed: bool = False,
):
    """Handle 'hatch mcp list hosts' command - shows configured hosts in environment.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_list_hosts.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace(env_manager=env_manager, env=env_name, detailed=detailed)
    return _handle_mcp_list_hosts(args)


def handle_mcp_list_servers(
    env_manager: HatchEnvironmentManager, env_name: Optional[str] = None
):
    """Handle 'hatch mcp list servers' command.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_list_servers.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace(env_manager=env_manager, env=env_name)
    return _handle_mcp_list_servers(args)


def handle_mcp_backup_restore(
    env_manager: HatchEnvironmentManager,
    host: str,
    backup_file: Optional[str] = None,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    """Handle 'hatch mcp backup restore' command.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_backup_restore.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace(
        env_manager=env_manager,
        host=host,
        backup_file=backup_file,
        dry_run=dry_run,
        auto_approve=auto_approve
    )
    return _handle_mcp_backup_restore(args)


def handle_mcp_backup_list(host: str, detailed: bool = False):
    """Handle 'hatch mcp backup list' command.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_backup_list.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace(host=host, detailed=detailed)
    return _handle_mcp_backup_list(args)


def handle_mcp_backup_clean(
    host: str,
    older_than_days: Optional[int] = None,
    keep_count: Optional[int] = None,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    """Handle 'hatch mcp backup clean' command.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_backup_clean.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    args = Namespace(
        host=host,
        older_than_days=older_than_days,
        keep_count=keep_count,
        dry_run=dry_run,
        auto_approve=auto_approve
    )
    return _handle_mcp_backup_clean(args)


def handle_mcp_configure(
    host: str,
    server_name: str,
    command: str,
    args: list,
    env: Optional[list] = None,
    url: Optional[str] = None,
    header: Optional[list] = None,
    timeout: Optional[int] = None,
    trust: bool = False,
    cwd: Optional[str] = None,
    env_file: Optional[str] = None,
    http_url: Optional[str] = None,
    include_tools: Optional[list] = None,
    exclude_tools: Optional[list] = None,
    input: Optional[list] = None,
    disabled: Optional[bool] = None,
    auto_approve_tools: Optional[list] = None,
    disable_tools: Optional[list] = None,
    env_vars: Optional[list] = None,
    startup_timeout: Optional[int] = None,
    tool_timeout: Optional[int] = None,
    enabled: Optional[bool] = None,
    bearer_token_env_var: Optional[str] = None,
    env_header: Optional[list] = None,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    """Handle 'hatch mcp configure' command with ALL host-specific arguments.
    
    Delegates to hatch.cli.cli_mcp.handle_mcp_configure.
    This wrapper maintains backward compatibility during refactoring.
    """
    from argparse import Namespace
    ns_args = Namespace(
        host=host,
        server_name=server_name,
        server_command=command,
        args=args,
        env_var=env,
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
        auto_approve=auto_approve
    )
    return _handle_mcp_configure(ns_args)


def handle_mcp_remove(
    host: str,
    server_name: str,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    """Handle 'hatch mcp remove' command.
    
    Backward compatibility wrapper - delegates to cli_mcp module.
    """
    from hatch.cli.cli_mcp import handle_mcp_remove as _handle_mcp_remove
    return _handle_mcp_remove(
        host=host,
        server_name=server_name,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def handle_mcp_remove_server(
    env_manager: HatchEnvironmentManager,
    server_name: str,
    hosts: Optional[str] = None,
    env: Optional[str] = None,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    """Handle 'hatch mcp remove server' command.
    
    Backward compatibility wrapper - delegates to cli_mcp module.
    """
    from hatch.cli.cli_mcp import handle_mcp_remove_server as _handle_mcp_remove_server
    return _handle_mcp_remove_server(
        env_manager=env_manager,
        server_name=server_name,
        hosts=hosts,
        env=env,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def handle_mcp_remove_host(
    env_manager: HatchEnvironmentManager,
    host_name: str,
    no_backup: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    """Handle 'hatch mcp remove host' command.
    
    Backward compatibility wrapper - delegates to cli_mcp module.
    """
    from hatch.cli.cli_mcp import handle_mcp_remove_host as _handle_mcp_remove_host
    return _handle_mcp_remove_host(
        env_manager=env_manager,
        host_name=host_name,
        no_backup=no_backup,
        dry_run=dry_run,
        auto_approve=auto_approve,
    )


def handle_mcp_sync(
    from_env: Optional[str] = None,
    from_host: Optional[str] = None,
    to_hosts: Optional[str] = None,
    servers: Optional[str] = None,
    pattern: Optional[str] = None,
    dry_run: bool = False,
    auto_approve: bool = False,
    no_backup: bool = False,
) -> int:
    """Handle 'hatch mcp sync' command.
    
    Backward compatibility wrapper - delegates to cli_mcp module.
    """
    from hatch.cli.cli_mcp import handle_mcp_sync as _handle_mcp_sync
    return _handle_mcp_sync(
        from_env=from_env,
        from_host=from_host,
        to_hosts=to_hosts,
        servers=servers,
        pattern=pattern,
        dry_run=dry_run,
        auto_approve=auto_approve,
        no_backup=no_backup,
    )


def main():
    """Main entry point for Hatch CLI.

    Parses command-line arguments and executes the requested commands for:
    - Package template creation
    - Package validation
    - Environment management (create, remove, list, use, current)
    - Package management (add, remove, list)

    Returns:
        int: Exit code (0 for success, 1 for errors)
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create argument parser
    parser = argparse.ArgumentParser(description="Hatch package manager CLI")

    # Add version argument
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_hatch_version()}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create template command
    create_parser = subparsers.add_parser(
        "create", help="Create a new package template"
    )
    create_parser.add_argument("name", help="Package name")
    create_parser.add_argument(
        "--dir", "-d", default=".", help="Target directory (default: current directory)"
    )
    create_parser.add_argument(
        "--description", "-D", default="", help="Package description"
    )

    # Validate package command
    validate_parser = subparsers.add_parser("validate", help="Validate a package")
    validate_parser.add_argument("package_dir", help="Path to package directory")

    # Environment management commands
    env_subparsers = subparsers.add_parser(
        "env", help="Environment management commands"
    ).add_subparsers(dest="env_command", help="Environment command to execute")

    # Create environment command
    env_create_parser = env_subparsers.add_parser(
        "create", help="Create a new environment"
    )
    env_create_parser.add_argument("name", help="Environment name")
    env_create_parser.add_argument(
        "--description", "-D", default="", help="Environment description"
    )
    env_create_parser.add_argument(
        "--python-version", help="Python version for the environment (e.g., 3.11, 3.12)"
    )
    env_create_parser.add_argument(
        "--no-python",
        action="store_true",
        help="Don't create a Python environment using conda/mamba",
    )
    env_create_parser.add_argument(
        "--no-hatch-mcp-server",
        action="store_true",
        help="Don't install hatch_mcp_server wrapper in the new environment",
    )
    env_create_parser.add_argument(
        "--hatch_mcp_server_tag",
        help="Git tag/branch reference for hatch_mcp_server wrapper installation (e.g., 'dev', 'v0.1.0')",
    )

    # Remove environment command
    env_remove_parser = env_subparsers.add_parser(
        "remove", help="Remove an environment"
    )
    env_remove_parser.add_argument("name", help="Environment name")

    # List environments command
    env_subparsers.add_parser("list", help="List all available environments")

    # Set current environment command
    env_use_parser = env_subparsers.add_parser(
        "use", help="Set the current environment"
    )
    env_use_parser.add_argument("name", help="Environment name")

    # Show current environment command
    env_subparsers.add_parser("current", help="Show the current environment")

    # Python environment management commands - advanced subcommands
    env_python_subparsers = env_subparsers.add_parser(
        "python", help="Manage Python environments"
    ).add_subparsers(
        dest="python_command", help="Python environment command to execute"
    )

    # Initialize Python environment
    python_init_parser = env_python_subparsers.add_parser(
        "init", help="Initialize Python environment"
    )
    python_init_parser.add_argument(
        "--hatch_env",
        default=None,
        help="Hatch environment name in which the Python environment is located (default: current environment)",
    )
    python_init_parser.add_argument(
        "--python-version", help="Python version (e.g., 3.11, 3.12)"
    )
    python_init_parser.add_argument(
        "--force", action="store_true", help="Force recreation if exists"
    )
    python_init_parser.add_argument(
        "--no-hatch-mcp-server",
        action="store_true",
        help="Don't install hatch_mcp_server wrapper in the Python environment",
    )
    python_init_parser.add_argument(
        "--hatch_mcp_server_tag",
        help="Git tag/branch reference for hatch_mcp_server wrapper installation (e.g., 'dev', 'v0.1.0')",
    )

    # Show Python environment info
    python_info_parser = env_python_subparsers.add_parser(
        "info", help="Show Python environment information"
    )
    python_info_parser.add_argument(
        "--hatch_env",
        default=None,
        help="Hatch environment name in which the Python environment is located (default: current environment)",
    )
    python_info_parser.add_argument(
        "--detailed", action="store_true", help="Show detailed diagnostics"
    )

    # Hatch MCP server wrapper management commands
    hatch_mcp_parser = env_python_subparsers.add_parser(
        "add-hatch-mcp", help="Add hatch_mcp_server wrapper to the environment"
    )
    ## Install MCP server command
    hatch_mcp_parser.add_argument(
        "--hatch_env",
        default=None,
        help="Hatch environment name. It must possess a valid Python environment. (default: current environment)",
    )
    hatch_mcp_parser.add_argument(
        "--tag",
        default=None,
        help="Git tag/branch reference for wrapper installation (e.g., 'dev', 'v0.1.0')",
    )

    # Remove Python environment
    python_remove_parser = env_python_subparsers.add_parser(
        "remove", help="Remove Python environment"
    )
    python_remove_parser.add_argument(
        "--hatch_env",
        default=None,
        help="Hatch environment name in which the Python environment is located (default: current environment)",
    )
    python_remove_parser.add_argument(
        "--force", action="store_true", help="Force removal without confirmation"
    )

    # Launch Python shell
    python_shell_parser = env_python_subparsers.add_parser(
        "shell", help="Launch Python shell in environment"
    )
    python_shell_parser.add_argument(
        "--hatch_env",
        default=None,
        help="Hatch environment name in which the Python environment is located (default: current environment)",
    )
    python_shell_parser.add_argument(
        "--cmd", help="Command to run in the shell (optional)"
    )

    # MCP host configuration commands
    mcp_subparsers = subparsers.add_parser(
        "mcp", help="MCP host configuration commands"
    ).add_subparsers(dest="mcp_command", help="MCP command to execute")

    # MCP discovery commands
    mcp_discover_subparsers = mcp_subparsers.add_parser(
        "discover", help="Discover MCP hosts and servers"
    ).add_subparsers(dest="discover_command", help="Discovery command to execute")

    # Discover hosts command
    mcp_discover_hosts_parser = mcp_discover_subparsers.add_parser(
        "hosts", help="Discover available MCP host platforms"
    )

    # Discover servers command
    mcp_discover_servers_parser = mcp_discover_subparsers.add_parser(
        "servers", help="Discover configured MCP servers"
    )
    mcp_discover_servers_parser.add_argument(
        "--env",
        "-e",
        default=None,
        help="Environment name (default: current environment)",
    )

    # MCP list commands
    mcp_list_subparsers = mcp_subparsers.add_parser(
        "list", help="List MCP hosts and servers"
    ).add_subparsers(dest="list_command", help="List command to execute")

    # List hosts command
    mcp_list_hosts_parser = mcp_list_subparsers.add_parser(
        "hosts", help="List configured MCP hosts from environment"
    )
    mcp_list_hosts_parser.add_argument(
        "--env",
        "-e",
        default=None,
        help="Environment name (default: current environment)",
    )
    mcp_list_hosts_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed host configuration information",
    )

    # List servers command
    mcp_list_servers_parser = mcp_list_subparsers.add_parser(
        "servers", help="List configured MCP servers from environment"
    )
    mcp_list_servers_parser.add_argument(
        "--env",
        "-e",
        default=None,
        help="Environment name (default: current environment)",
    )

    # MCP backup commands
    mcp_backup_subparsers = mcp_subparsers.add_parser(
        "backup", help="Backup management commands"
    ).add_subparsers(dest="backup_command", help="Backup command to execute")

    # Restore backup command
    mcp_backup_restore_parser = mcp_backup_subparsers.add_parser(
        "restore", help="Restore MCP host configuration from backup"
    )
    mcp_backup_restore_parser.add_argument(
        "host", help="Host platform to restore (e.g., claude-desktop, cursor)"
    )
    mcp_backup_restore_parser.add_argument(
        "--backup-file",
        "-f",
        default=None,
        help="Specific backup file to restore (default: latest)",
    )
    mcp_backup_restore_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview restore operation without execution",
    )
    mcp_backup_restore_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )

    # List backups command
    mcp_backup_list_parser = mcp_backup_subparsers.add_parser(
        "list", help="List available backups for MCP host"
    )
    mcp_backup_list_parser.add_argument(
        "host", help="Host platform to list backups for (e.g., claude-desktop, cursor)"
    )
    mcp_backup_list_parser.add_argument(
        "--detailed", "-d", action="store_true", help="Show detailed backup information"
    )

    # Clean backups command
    mcp_backup_clean_parser = mcp_backup_subparsers.add_parser(
        "clean", help="Clean old backups based on criteria"
    )
    mcp_backup_clean_parser.add_argument(
        "host", help="Host platform to clean backups for (e.g., claude-desktop, cursor)"
    )
    mcp_backup_clean_parser.add_argument(
        "--older-than-days", type=int, help="Remove backups older than specified days"
    )
    mcp_backup_clean_parser.add_argument(
        "--keep-count",
        type=int,
        help="Keep only the specified number of newest backups",
    )
    mcp_backup_clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview cleanup operation without execution",
    )
    mcp_backup_clean_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )

    # MCP direct management commands
    mcp_configure_parser = mcp_subparsers.add_parser(
        "configure", help="Configure MCP server directly on host"
    )
    mcp_configure_parser.add_argument(
        "server_name", help="Name for the MCP server [hosts: all]"
    )
    mcp_configure_parser.add_argument(
        "--host",
        required=True,
        help="Host platform to configure (e.g., claude-desktop, cursor) [hosts: all]",
    )

    # Create mutually exclusive group for server type
    server_type_group = mcp_configure_parser.add_mutually_exclusive_group()
    server_type_group.add_argument(
        "--command",
        dest="server_command",
        help="Command to execute the MCP server (for local servers) [hosts: all]",
    )
    server_type_group.add_argument(
        "--url", help="Server URL for remote MCP servers (SSE transport) [hosts: all except claude-desktop, claude-code]"
    )
    server_type_group.add_argument(
        "--http-url", help="HTTP streaming endpoint URL [hosts: gemini]"
    )

    mcp_configure_parser.add_argument(
        "--args",
        nargs="*",
        help="Arguments for the MCP server command (only with --command) [hosts: all]",
    )
    mcp_configure_parser.add_argument(
        "--env-var",
        action="append",
        help="Environment variables (format: KEY=VALUE) [hosts: all]",
    )
    mcp_configure_parser.add_argument(
        "--header",
        action="append",
        help="HTTP headers for remote servers (format: KEY=VALUE, only with --url) [hosts: all except claude-desktop, claude-code]",
    )

    # Host-specific arguments (Gemini)
    mcp_configure_parser.add_argument(
        "--timeout", type=int, help="Request timeout in milliseconds [hosts: gemini]"
    )
    mcp_configure_parser.add_argument(
        "--trust", action="store_true", help="Bypass tool call confirmations [hosts: gemini]"
    )
    mcp_configure_parser.add_argument(
        "--cwd", help="Working directory for stdio transport [hosts: gemini, codex]"
    )
    mcp_configure_parser.add_argument(
        "--include-tools",
        nargs="*",
        help="Tool allowlist / enabled tools [hosts: gemini, codex]",
    )
    mcp_configure_parser.add_argument(
        "--exclude-tools",
        nargs="*",
        help="Tool blocklist / disabled tools [hosts: gemini, codex]",
    )

    # Host-specific arguments (Cursor/VS Code/LM Studio)
    mcp_configure_parser.add_argument(
        "--env-file", help="Path to environment file [hosts: cursor, vscode, lmstudio]"
    )

    # Host-specific arguments (VS Code)
    mcp_configure_parser.add_argument(
        "--input",
        action="append",
        help="Input variable definitions in format: type,id,description[,password=true] [hosts: vscode]",
    )

    # Host-specific arguments (Kiro)
    mcp_configure_parser.add_argument(
        "--disabled",
        action="store_true",
        default=None,
        help="Disable the MCP server [hosts: kiro]"
    )
    mcp_configure_parser.add_argument(
        "--auto-approve-tools",
        action="append",
        help="Tool names to auto-approve without prompting [hosts: kiro]"
    )
    mcp_configure_parser.add_argument(
        "--disable-tools",
        action="append",
        help="Tool names to disable [hosts: kiro]"
    )

    # Codex-specific arguments
    mcp_configure_parser.add_argument(
        "--env-vars",
        action="append",
        help="Environment variable names to whitelist/forward [hosts: codex]"
    )
    mcp_configure_parser.add_argument(
        "--startup-timeout",
        type=int,
        help="Server startup timeout in seconds (default: 10) [hosts: codex]"
    )
    mcp_configure_parser.add_argument(
        "--tool-timeout",
        type=int,
        help="Tool execution timeout in seconds (default: 60) [hosts: codex]"
    )
    mcp_configure_parser.add_argument(
        "--enabled",
        action="store_true",
        default=None,
        help="Enable the MCP server [hosts: codex]"
    )
    mcp_configure_parser.add_argument(
        "--bearer-token-env-var",
        type=str,
        help="Name of environment variable containing bearer token for Authorization header [hosts: codex]"
    )
    mcp_configure_parser.add_argument(
        "--env-header",
        action="append",
        help="HTTP header from environment variable in KEY=ENV_VAR_NAME format [hosts: codex]"
    )

    mcp_configure_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation before configuration [hosts: all]",
    )
    mcp_configure_parser.add_argument(
        "--dry-run", action="store_true", help="Preview configuration without execution [hosts: all]"
    )
    mcp_configure_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts [hosts: all]"
    )

    # Remove MCP commands (object-action pattern)
    mcp_remove_subparsers = mcp_subparsers.add_parser(
        "remove", help="Remove MCP servers or host configurations"
    ).add_subparsers(dest="remove_command", help="Remove command to execute")

    # Remove server command
    mcp_remove_server_parser = mcp_remove_subparsers.add_parser(
        "server", help="Remove MCP server from hosts"
    )
    mcp_remove_server_parser.add_argument(
        "server_name", help="Name of the MCP server to remove"
    )
    mcp_remove_server_parser.add_argument(
        "--host", help="Target hosts (comma-separated or 'all')"
    )
    mcp_remove_server_parser.add_argument(
        "--env", "-e", help="Environment name (for environment-based removal)"
    )
    mcp_remove_server_parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup creation before removal"
    )
    mcp_remove_server_parser.add_argument(
        "--dry-run", action="store_true", help="Preview removal without execution"
    )
    mcp_remove_server_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )

    # Remove host command
    mcp_remove_host_parser = mcp_remove_subparsers.add_parser(
        "host", help="Remove entire host configuration"
    )
    mcp_remove_host_parser.add_argument(
        "host_name", help="Host platform to remove (e.g., claude-desktop, cursor)"
    )
    mcp_remove_host_parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup creation before removal"
    )
    mcp_remove_host_parser.add_argument(
        "--dry-run", action="store_true", help="Preview removal without execution"
    )
    mcp_remove_host_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )

    # MCP synchronization command
    mcp_sync_parser = mcp_subparsers.add_parser(
        "sync", help="Synchronize MCP configurations between environments and hosts"
    )

    # Source options (mutually exclusive)
    sync_source_group = mcp_sync_parser.add_mutually_exclusive_group(required=True)
    sync_source_group.add_argument("--from-env", help="Source environment name")
    sync_source_group.add_argument("--from-host", help="Source host platform")

    # Target options
    mcp_sync_parser.add_argument(
        "--to-host", required=True, help="Target hosts (comma-separated or 'all')"
    )

    # Filter options (mutually exclusive)
    sync_filter_group = mcp_sync_parser.add_mutually_exclusive_group()
    sync_filter_group.add_argument(
        "--servers", help="Specific server names to sync (comma-separated)"
    )
    sync_filter_group.add_argument(
        "--pattern", help="Regex pattern for server selection"
    )

    # Standard options
    mcp_sync_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview synchronization without execution",
    )
    mcp_sync_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )
    mcp_sync_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation before synchronization",
    )

    # Package management commands
    pkg_subparsers = subparsers.add_parser(
        "package", help="Package management commands"
    ).add_subparsers(dest="pkg_command", help="Package command to execute")

    # Add package command
    pkg_add_parser = pkg_subparsers.add_parser(
        "add", help="Add a package to the current environment"
    )
    pkg_add_parser.add_argument(
        "package_path_or_name", help="Path to package directory or name of the package"
    )
    pkg_add_parser.add_argument(
        "--env",
        "-e",
        default=None,
        help="Environment name (default: current environment)",
    )
    pkg_add_parser.add_argument(
        "--version", "-v", default=None, help="Version of the package (optional)"
    )
    pkg_add_parser.add_argument(
        "--force-download",
        "-f",
        action="store_true",
        help="Force download even if package is in cache",
    )
    pkg_add_parser.add_argument(
        "--refresh-registry",
        "-r",
        action="store_true",
        help="Force refresh of registry data",
    )
    pkg_add_parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve changes installation of deps for automation scenario",
    )
    # MCP host configuration integration
    pkg_add_parser.add_argument(
        "--host",
        help="Comma-separated list of MCP host platforms to configure (e.g., claude-desktop,cursor)",
    )

    # Remove package command
    pkg_remove_parser = pkg_subparsers.add_parser(
        "remove", help="Remove a package from the current environment"
    )
    pkg_remove_parser.add_argument("package_name", help="Name of the package to remove")
    pkg_remove_parser.add_argument(
        "--env",
        "-e",
        default=None,
        help="Environment name (default: current environment)",
    )

    # List packages command
    pkg_list_parser = pkg_subparsers.add_parser(
        "list", help="List packages in an environment"
    )
    pkg_list_parser.add_argument(
        "--env", "-e", help="Environment name (default: current environment)"
    )

    # Sync package MCP servers command
    pkg_sync_parser = pkg_subparsers.add_parser(
        "sync", help="Synchronize package MCP servers to host platforms"
    )
    pkg_sync_parser.add_argument(
        "package_name", help="Name of the package whose MCP servers to sync"
    )
    pkg_sync_parser.add_argument(
        "--host",
        required=True,
        help="Comma-separated list of host platforms to sync to (or 'all')",
    )
    pkg_sync_parser.add_argument(
        "--env",
        "-e",
        default=None,
        help="Environment name (default: current environment)",
    )
    pkg_sync_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )
    pkg_sync_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )
    pkg_sync_parser.add_argument(
        "--no-backup", action="store_true", help="Disable default backup behavior"
    )

    # General arguments for the environment manager
    parser.add_argument(
        "--envs-dir",
        default=Path.home() / ".hatch" / "envs",
        help="Directory to store environments",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=86400,
        help="Cache TTL in seconds (default: 86400 seconds --> 1 day)",
    )
    parser.add_argument(
        "--cache-dir",
        default=Path.home() / ".hatch" / "cache",
        help="Directory to store cached packages",
    )

    args = parser.parse_args()

    # Initialize environment manager
    env_manager = HatchEnvironmentManager(
        environments_dir=args.envs_dir,
        cache_ttl=args.cache_ttl,
        cache_dir=args.cache_dir,
    )

    # Initialize MCP configuration manager
    mcp_manager = MCPHostConfigurationManager()

    # Execute commands
    if args.command == "create":
        from hatch.cli.cli_system import handle_create
        return handle_create(args)

    elif args.command == "validate":
        from hatch.cli.cli_system import handle_validate
        args.env_manager = env_manager
        return handle_validate(args)

    elif args.command == "env":
        # Import environment handlers
        from hatch.cli.cli_env import (
            handle_env_create,
            handle_env_remove,
            handle_env_list,
            handle_env_use,
            handle_env_current,
            handle_env_python_init,
            handle_env_python_info,
            handle_env_python_remove,
            handle_env_python_shell,
            handle_env_python_add_hatch_mcp,
        )
        
        # Attach env_manager to args for handler access
        args.env_manager = env_manager
        
        if args.env_command == "create":
            return handle_env_create(args)

        elif args.env_command == "remove":
            return handle_env_remove(args)

        elif args.env_command == "list":
            return handle_env_list(args)

        elif args.env_command == "use":
            return handle_env_use(args)

        elif args.env_command == "current":
            return handle_env_current(args)

        elif args.env_command == "python":
            # Advanced Python environment management
            if args.python_command == "init":
                return handle_env_python_init(args)

            elif args.python_command == "info":
                return handle_env_python_info(args)

            elif args.python_command == "remove":
                return handle_env_python_remove(args)

            elif args.python_command == "shell":
                return handle_env_python_shell(args)

            elif args.python_command == "add-hatch-mcp":
                return handle_env_python_add_hatch_mcp(args)

            else:
                print("Unknown Python environment command")
                return 1

    elif args.command == "package":
        # Import package handlers
        from hatch.cli.cli_package import (
            handle_package_add,
            handle_package_remove,
            handle_package_list,
            handle_package_sync,
        )
        
        # Attach managers to args for handler access
        args.env_manager = env_manager
        args.mcp_manager = mcp_manager
        
        if args.pkg_command == "add":
            return handle_package_add(args)

        elif args.pkg_command == "remove":
            return handle_package_remove(args)

        elif args.pkg_command == "list":
            return handle_package_list(args)

        elif args.pkg_command == "sync":
            return handle_package_sync(args)

        else:
            parser.print_help()
            return 1

    elif args.command == "mcp":
        if args.mcp_command == "discover":
            if args.discover_command == "hosts":
                return handle_mcp_discover_hosts()
            elif args.discover_command == "servers":
                return handle_mcp_discover_servers(env_manager, args.env)
            else:
                print("Unknown discover command")
                return 1

        elif args.mcp_command == "list":
            if args.list_command == "hosts":
                return handle_mcp_list_hosts(env_manager, args.env, args.detailed)
            elif args.list_command == "servers":
                return handle_mcp_list_servers(env_manager, args.env)
            else:
                print("Unknown list command")
                return 1

        elif args.mcp_command == "backup":
            if args.backup_command == "restore":
                return handle_mcp_backup_restore(
                    env_manager,
                    args.host,
                    args.backup_file,
                    args.dry_run,
                    args.auto_approve,
                )
            elif args.backup_command == "list":
                return handle_mcp_backup_list(args.host, args.detailed)
            elif args.backup_command == "clean":
                return handle_mcp_backup_clean(
                    args.host,
                    args.older_than_days,
                    args.keep_count,
                    args.dry_run,
                    args.auto_approve,
                )
            else:
                print("Unknown backup command")
                return 1

        elif args.mcp_command == "configure":
            return handle_mcp_configure(
                args.host,
                args.server_name,
                args.server_command,
                args.args,
                getattr(args, "env_var", None),
                args.url,
                args.header,
                getattr(args, "timeout", None),
                getattr(args, "trust", False),
                getattr(args, "cwd", None),
                getattr(args, "env_file", None),
                getattr(args, "http_url", None),
                getattr(args, "include_tools", None),
                getattr(args, "exclude_tools", None),
                getattr(args, "input", None),
                getattr(args, "disabled", None),
                getattr(args, "auto_approve_tools", None),
                getattr(args, "disable_tools", None),
                getattr(args, "env_vars", None),
                getattr(args, "startup_timeout", None),
                getattr(args, "tool_timeout", None),
                getattr(args, "enabled", None),
                getattr(args, "bearer_token_env_var", None),
                getattr(args, "env_header", None),
                args.no_backup,
                args.dry_run,
                args.auto_approve,
            )

        elif args.mcp_command == "remove":
            if args.remove_command == "server":
                return handle_mcp_remove_server(
                    env_manager,
                    args.server_name,
                    args.host,
                    args.env,
                    args.no_backup,
                    args.dry_run,
                    args.auto_approve,
                )
            elif args.remove_command == "host":
                return handle_mcp_remove_host(
                    env_manager,
                    args.host_name,
                    args.no_backup,
                    args.dry_run,
                    args.auto_approve,
                )
            else:
                print("Unknown remove command")
                return 1

        elif args.mcp_command == "sync":
            return handle_mcp_sync(
                from_env=getattr(args, "from_env", None),
                from_host=getattr(args, "from_host", None),
                to_hosts=args.to_host,
                servers=getattr(args, "servers", None),
                pattern=getattr(args, "pattern", None),
                dry_run=args.dry_run,
                auto_approve=args.auto_approve,
                no_backup=args.no_backup,
            )

        else:
            print("Unknown MCP command")
            return 1

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
