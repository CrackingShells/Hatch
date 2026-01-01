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
        target_dir = Path(args.dir).resolve()
        package_dir = create_package_template(
            target_dir=target_dir, package_name=args.name, description=args.description
        )
        print(f"Package template created at: {package_dir}")

    elif args.command == "validate":
        package_path = Path(args.package_dir).resolve()

        # Create validator with registry data from environment manager
        validator = HatchPackageValidator(
            version="latest",
            allow_local_dependencies=True,
            registry_data=env_manager.registry_data,
        )

        # Validate the package
        is_valid, validation_results = validator.validate_package(package_path)

        if is_valid:
            print(f"Package validation SUCCESSFUL: {package_path}")
            return 0
        else:
            print(f"Package validation FAILED: {package_path}")

            # Print detailed validation results if available
            if validation_results and isinstance(validation_results, dict):
                for category, result in validation_results.items():
                    if (
                        category != "valid"
                        and category != "metadata"
                        and isinstance(result, dict)
                    ):
                        if not result.get("valid", True) and result.get("errors"):
                            print(f"\n{category.replace('_', ' ').title()} errors:")
                            for error in result["errors"]:
                                print(f"  - {error}")

            return 1

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
        if args.pkg_command == "add":
            # Add package to environment
            if env_manager.add_package_to_environment(
                args.package_path_or_name,
                args.env,
                args.version,
                args.force_download,
                args.refresh_registry,
                args.auto_approve,
            ):
                print(f"Successfully added package: {args.package_path_or_name}")

                # Handle MCP host configuration if requested
                if hasattr(args, "host") and args.host:
                    try:
                        hosts = parse_host_list(args.host)
                        env_name = args.env or env_manager.get_current_environment()

                        package_name = args.package_path_or_name
                        package_service = None

                        # Check if it's a local package path
                        pkg_path = Path(args.package_path_or_name)
                        if pkg_path.exists() and pkg_path.is_dir():
                            # Local package - load metadata from directory
                            with open(pkg_path / "hatch_metadata.json", "r") as f:
                                metadata = json.load(f)
                                package_service = PackageService(metadata)
                            package_name = package_service.get_field("name")
                        else:
                            # Registry package - get metadata from environment manager
                            try:
                                env_data = env_manager.get_environment_data(env_name)
                                if env_data:
                                    # Find the package in the environment
                                    for pkg in env_data.packages:
                                        if pkg.name == package_name:
                                            # Create a minimal metadata structure for PackageService
                                            metadata = {
                                                "name": pkg.name,
                                                "version": pkg.version,
                                                "dependencies": {},  # Will be populated if needed
                                            }
                                            package_service = PackageService(metadata)
                                            break

                                if package_service is None:
                                    print(
                                        f"Warning: Could not find package '{package_name}' in environment '{env_name}'. Skipping dependency analysis."
                                    )
                                    package_service = None
                            except Exception as e:
                                print(
                                    f"Warning: Could not load package metadata for '{package_name}': {e}. Skipping dependency analysis."
                                )
                                package_service = None

                        # Get dependency names if we have package service
                        package_names = []
                        if package_service:
                            # Get Hatch dependencies
                            dependencies = package_service.get_dependencies()
                            hatch_deps = dependencies.get("hatch", [])
                            package_names = [
                                dep.get("name") for dep in hatch_deps if dep.get("name")
                            ]

                            # Resolve local dependency paths to actual names
                            for i in range(len(package_names)):
                                dep_path = Path(package_names[i])
                                if dep_path.exists() and dep_path.is_dir():
                                    try:
                                        with open(
                                            dep_path / "hatch_metadata.json", "r"
                                        ) as f:
                                            dep_metadata = json.load(f)
                                            dep_service = PackageService(dep_metadata)
                                        package_names[i] = dep_service.get_field("name")
                                    except Exception as e:
                                        print(
                                            f"Warning: Could not resolve dependency path '{package_names[i]}': {e}"
                                        )

                        # Add the main package to the list
                        package_names.append(package_name)

                        # Get MCP server configuration for all packages
                        server_configs = [
                            get_package_mcp_server_config(
                                env_manager, env_name, pkg_name
                            )
                            for pkg_name in package_names
                        ]

                        print(
                            f"Configuring MCP server for package '{package_name}' on {len(hosts)} host(s)..."
                        )

                        # Configure on each host
                        success_count = 0
                        for host in hosts:  # 'host', here, is a string
                            try:
                                # Convert string to MCPHostType enum
                                host_type = MCPHostType(host)
                                host_model_class = HOST_MODEL_REGISTRY.get(host_type)
                                if not host_model_class:
                                    print(
                                        f"✗ Error: No model registered for host '{host}'"
                                    )
                                    continue

                                host_success_count = 0
                                for i, server_config in enumerate(server_configs):
                                    pkg_name = package_names[i]
                                    try:
                                        # Convert MCPServerConfig to Omni model
                                        # Only include fields that have actual values
                                        omni_config_data = {"name": server_config.name}
                                        if server_config.command is not None:
                                            omni_config_data["command"] = (
                                                server_config.command
                                            )
                                        if server_config.args is not None:
                                            omni_config_data["args"] = (
                                                server_config.args
                                            )
                                        if server_config.env:
                                            omni_config_data["env"] = server_config.env
                                        if server_config.url is not None:
                                            omni_config_data["url"] = server_config.url
                                        headers = getattr(
                                            server_config, "headers", None
                                        )
                                        if headers is not None:
                                            omni_config_data["headers"] = headers

                                        omni_config = MCPServerConfigOmni(
                                            **omni_config_data
                                        )

                                        # Convert to host-specific model
                                        host_config = host_model_class.from_omni(
                                            omni_config
                                        )

                                        # Generate and display conversion report
                                        report = generate_conversion_report(
                                            operation="create",
                                            server_name=server_config.name,
                                            target_host=host_type,
                                            omni=omni_config,
                                            dry_run=False,
                                        )
                                        display_report(report)

                                        result = mcp_manager.configure_server(
                                            hostname=host,
                                            server_config=host_config,
                                            no_backup=False,  # Always backup when adding packages
                                        )

                                        if result.success:
                                            print(
                                                f"✓ Configured {server_config.name} ({pkg_name}) on {host}"
                                            )
                                            host_success_count += 1

                                            # Update package metadata with host configuration tracking
                                            try:
                                                server_config_dict = {
                                                    "name": server_config.name,
                                                    "command": server_config.command,
                                                    "args": server_config.args,
                                                }

                                                env_manager.update_package_host_configuration(
                                                    env_name=env_name,
                                                    package_name=pkg_name,
                                                    hostname=host,
                                                    server_config=server_config_dict,
                                                )
                                            except Exception as e:
                                                # Log but don't fail the configuration operation
                                                print(
                                                    f"[WARNING] Failed to update package metadata for {pkg_name}: {e}"
                                                )
                                        else:
                                            print(
                                                f"✗ Failed to configure {server_config.name} ({pkg_name}) on {host}: {result.error_message}"
                                            )

                                    except Exception as e:
                                        print(
                                            f"✗ Error configuring {server_config.name} ({pkg_name}) on {host}: {e}"
                                        )

                                if host_success_count == len(server_configs):
                                    success_count += 1

                            except ValueError as e:
                                print(f"✗ Invalid host '{host}': {e}")
                                continue

                        if success_count > 0:
                            print(
                                f"MCP configuration completed: {success_count}/{len(hosts)} hosts configured"
                            )
                        else:
                            print("Warning: MCP configuration failed on all hosts")

                    except ValueError as e:
                        print(f"Warning: MCP host configuration failed: {e}")
                        # Don't fail the entire operation for MCP configuration issues

                return 0
            else:
                print(f"Failed to add package: {args.package_path_or_name}")
                return 1

        elif args.pkg_command == "remove":
            if env_manager.remove_package(args.package_name, args.env):
                print(f"Successfully removed package: {args.package_name}")
                return 0
            else:
                print(f"Failed to remove package: {args.package_name}")
                return 1

        elif args.pkg_command == "list":
            packages = env_manager.list_packages(args.env)

            if not packages:
                print(f"No packages found in environment: {args.env}")
                return 0

            print(f"Packages in environment '{args.env}':")
            for pkg in packages:
                print(
                    f"{pkg['name']} ({pkg['version']})\tHatch compliant: {pkg['hatch_compliant']}\tsource: {pkg['source']['uri']}\tlocation: {pkg['source']['path']}"
                )
            return 0

        elif args.pkg_command == "sync":
            try:
                # Parse host list
                hosts = parse_host_list(args.host)
                env_name = args.env or env_manager.get_current_environment()

                # Get all packages to sync (main package + dependencies)
                package_names = [args.package_name]

                # Try to get dependencies for the main package
                try:
                    env_data = env_manager.get_environment_data(env_name)
                    if env_data:
                        # Find the main package in the environment
                        main_package = None
                        for pkg in env_data.packages:
                            if pkg.name == args.package_name:
                                main_package = pkg
                                break

                        if main_package:
                            # Create a minimal metadata structure for PackageService
                            metadata = {
                                "name": main_package.name,
                                "version": main_package.version,
                                "dependencies": {},  # Will be populated if needed
                            }
                            package_service = PackageService(metadata)

                            # Get Hatch dependencies
                            dependencies = package_service.get_dependencies()
                            hatch_deps = dependencies.get("hatch", [])
                            dep_names = [
                                dep.get("name") for dep in hatch_deps if dep.get("name")
                            ]

                            # Add dependencies to the sync list (before main package)
                            package_names = dep_names + [args.package_name]
                        else:
                            print(
                                f"Warning: Package '{args.package_name}' not found in environment '{env_name}'. Syncing only the specified package."
                            )
                    else:
                        print(
                            f"Warning: Could not access environment '{env_name}'. Syncing only the specified package."
                        )
                except Exception as e:
                    print(
                        f"Warning: Could not analyze dependencies for '{args.package_name}': {e}. Syncing only the specified package."
                    )

                # Get MCP server configurations for all packages
                server_configs = []
                for pkg_name in package_names:
                    try:
                        config = get_package_mcp_server_config(
                            env_manager, env_name, pkg_name
                        )
                        server_configs.append((pkg_name, config))
                    except Exception as e:
                        print(
                            f"Warning: Could not get MCP configuration for package '{pkg_name}': {e}"
                        )

                if not server_configs:
                    print(
                        f"Error: No MCP server configurations found for package '{args.package_name}' or its dependencies"
                    )
                    return 1

                if args.dry_run:
                    print(
                        f"[DRY RUN] Would synchronize MCP servers for {len(server_configs)} package(s) to hosts: {[h for h in hosts]}"
                    )
                    for pkg_name, config in server_configs:
                        print(
                            f"[DRY RUN] - {pkg_name}: {config.name} -> {' '.join(config.args)}"
                        )

                        # Generate and display conversion reports for dry-run mode
                        for host in hosts:
                            try:
                                host_type = MCPHostType(host)
                                host_model_class = HOST_MODEL_REGISTRY.get(host_type)
                                if not host_model_class:
                                    print(
                                        f"[DRY RUN] ✗ Error: No model registered for host '{host}'"
                                    )
                                    continue

                                # Convert to Omni model
                                # Only include fields that have actual values
                                omni_config_data = {"name": config.name}
                                if config.command is not None:
                                    omni_config_data["command"] = config.command
                                if config.args is not None:
                                    omni_config_data["args"] = config.args
                                if config.env:
                                    omni_config_data["env"] = config.env
                                if config.url is not None:
                                    omni_config_data["url"] = config.url
                                headers = getattr(config, "headers", None)
                                if headers is not None:
                                    omni_config_data["headers"] = headers

                                omni_config = MCPServerConfigOmni(**omni_config_data)

                                # Generate report
                                report = generate_conversion_report(
                                    operation="create",
                                    server_name=config.name,
                                    target_host=host_type,
                                    omni=omni_config,
                                    dry_run=True,
                                )
                                print(f"[DRY RUN] Preview for {pkg_name} on {host}:")
                                display_report(report)
                            except ValueError as e:
                                print(f"[DRY RUN] ✗ Invalid host '{host}': {e}")
                    return 0

                # Confirm operation unless auto-approved
                package_desc = (
                    f"package '{args.package_name}'"
                    if len(server_configs) == 1
                    else f"{len(server_configs)} packages ('{args.package_name}' + dependencies)"
                )
                if not request_confirmation(
                    f"Synchronize MCP servers for {package_desc} to {len(hosts)} host(s)?",
                    args.auto_approve,
                ):
                    print("Operation cancelled.")
                    return 0

                # Perform synchronization to each host for all packages
                total_operations = len(server_configs) * len(hosts)
                success_count = 0

                for host in hosts:
                    try:
                        # Convert string to MCPHostType enum
                        host_type = MCPHostType(host)
                        host_model_class = HOST_MODEL_REGISTRY.get(host_type)
                        if not host_model_class:
                            print(f"✗ Error: No model registered for host '{host}'")
                            continue

                        for pkg_name, server_config in server_configs:
                            try:
                                # Convert MCPServerConfig to Omni model
                                # Only include fields that have actual values
                                omni_config_data = {"name": server_config.name}
                                if server_config.command is not None:
                                    omni_config_data["command"] = server_config.command
                                if server_config.args is not None:
                                    omni_config_data["args"] = server_config.args
                                if server_config.env:
                                    omni_config_data["env"] = server_config.env
                                if server_config.url is not None:
                                    omni_config_data["url"] = server_config.url
                                headers = getattr(server_config, "headers", None)
                                if headers is not None:
                                    omni_config_data["headers"] = headers

                                omni_config = MCPServerConfigOmni(**omni_config_data)

                                # Convert to host-specific model
                                host_config = host_model_class.from_omni(omni_config)

                                # Generate and display conversion report
                                report = generate_conversion_report(
                                    operation="create",
                                    server_name=server_config.name,
                                    target_host=host_type,
                                    omni=omni_config,
                                    dry_run=False,
                                )
                                display_report(report)

                                result = mcp_manager.configure_server(
                                    hostname=host,
                                    server_config=host_config,
                                    no_backup=args.no_backup,
                                )

                                if result.success:
                                    print(
                                        f"[SUCCESS] Successfully configured {server_config.name} ({pkg_name}) on {host}"
                                    )
                                    success_count += 1

                                    # Update package metadata with host configuration tracking
                                    try:
                                        server_config_dict = {
                                            "name": server_config.name,
                                            "command": server_config.command,
                                            "args": server_config.args,
                                        }

                                        env_manager.update_package_host_configuration(
                                            env_name=env_name,
                                            package_name=pkg_name,
                                            hostname=host,
                                            server_config=server_config_dict,
                                        )
                                    except Exception as e:
                                        # Log but don't fail the sync operation
                                        print(
                                            f"[WARNING] Failed to update package metadata for {pkg_name}: {e}"
                                        )
                                else:
                                    print(
                                        f"[ERROR] Failed to configure {server_config.name} ({pkg_name}) on {host}: {result.error_message}"
                                    )

                            except Exception as e:
                                print(
                                    f"[ERROR] Error configuring {server_config.name} ({pkg_name}) on {host}: {e}"
                                )

                    except ValueError as e:
                        print(f"✗ Invalid host '{host}': {e}")
                        continue

                # Report results
                if success_count == total_operations:
                    package_desc = (
                        f"package '{args.package_name}'"
                        if len(server_configs) == 1
                        else f"{len(server_configs)} packages"
                    )
                    print(
                        f"Successfully synchronized {package_desc} to all {len(hosts)} host(s)"
                    )
                    return 0
                elif success_count > 0:
                    print(
                        f"Partially synchronized: {success_count}/{total_operations} operations succeeded"
                    )
                    return 1
                else:
                    package_desc = (
                        f"package '{args.package_name}'"
                        if len(server_configs) == 1
                        else f"{len(server_configs)} packages"
                    )
                    print(f"Failed to synchronize {package_desc} to any hosts")
                    return 1

            except ValueError as e:
                print(f"Error: {e}")
                return 1

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
