"""Entry point for Hatch CLI.

This module provides the main entry point for the Hatch package manager CLI.
It handles argument parsing and routes commands to appropriate handler modules.

Architecture:
    This module implements the routing layer of the CLI architecture:
    1. Parses command-line arguments using argparse
    2. Initializes shared managers (HatchEnvironmentManager, MCPHostConfigurationManager)
    3. Attaches managers to the args namespace for handler access
    4. Routes commands to appropriate handler modules

Command Structure:
    hatch create <name>           - Create package template (cli_system)
    hatch validate <path>         - Validate package (cli_system)
    hatch env <subcommand>        - Environment management (cli_env)
    hatch package <subcommand>    - Package management (cli_package)
    hatch mcp <subcommand>        - MCP host configuration (cli_mcp)

Entry Points:
    - python -m hatch.cli: Module execution via __main__.py
    - hatch: Console script defined in pyproject.toml

Handler Signature:
    All handlers follow: (args: Namespace) -> int
    - args.env_manager: HatchEnvironmentManager instance
    - args.mcp_manager: MCPHostConfigurationManager instance
    - Returns: Exit code (0 for success, non-zero for errors)

Example:
    $ hatch --version
    $ hatch env list
    $ hatch mcp configure claude-desktop my-server --command python
"""

import argparse
import logging
import sys
from pathlib import Path

from hatch.cli.cli_utils import get_hatch_version, Color, _colors_enabled


class HatchArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser with formatted error messages.
    
    Overrides the error() method to format argparse errors with
    [ERROR] prefix and bright red color (when colors enabled).
    
    Reference: R13 §4.2.1 (13-error_message_formatting_v0.md)
    
    Output format:
        [ERROR] <message>
    
    Example:
        >>> parser = HatchArgumentParser(description="Test CLI")
        >>> parser.parse_args(['--invalid'])
        [ERROR] unrecognized arguments: --invalid
    """
    
    def error(self, message: str) -> None:
        """Override to format errors with [ERROR] prefix and color.
        
        Args:
            message: Error message from argparse
        
        Note:
            Preserves exit code 2 (argparse convention).
        """
        if _colors_enabled():
            self.exit(2, f"{Color.RED.value}[ERROR]{Color.RESET.value} {message}\n")
        else:
            self.exit(2, f"[ERROR] {message}\n")


def _setup_create_command(subparsers):
    """Set up 'hatch create' command parser."""
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
    create_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )


def _setup_validate_command(subparsers):
    """Set up 'hatch validate' command parser."""
    validate_parser = subparsers.add_parser("validate", help="Validate a package")
    validate_parser.add_argument("package_dir", help="Path to package directory")


def _setup_env_commands(subparsers):
    """Set up 'hatch env' command parsers."""
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
    env_create_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )

    # Remove environment command
    env_remove_parser = env_subparsers.add_parser(
        "remove", help="Remove an environment"
    )
    env_remove_parser.add_argument("name", help="Environment name")
    env_remove_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )
    env_remove_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompt"
    )

    # List environments command - now with subcommands per R10
    env_list_parser = env_subparsers.add_parser("list", help="List environments, hosts, or servers")
    env_list_subparsers = env_list_parser.add_subparsers(dest="list_command", help="List command to execute")
    
    # Default list behavior (no subcommand) - handled by checking list_command is None
    env_list_parser.add_argument(
        "--pattern",
        help="Filter environments by name using regex pattern",
    )
    env_list_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    
    # env list hosts subcommand per R10 §3.3
    env_list_hosts_parser = env_list_subparsers.add_parser(
        "hosts", help="List environment/host/server deployments"
    )
    env_list_hosts_parser.add_argument(
        "--env", "-e",
        help="Filter by environment name using regex pattern",
    )
    env_list_hosts_parser.add_argument(
        "--server",
        help="Filter by server name using regex pattern",
    )
    env_list_hosts_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )
    
    # env list servers subcommand per R10 §3.4
    env_list_servers_parser = env_list_subparsers.add_parser(
        "servers", help="List environment/server/host deployments"
    )
    env_list_servers_parser.add_argument(
        "--env", "-e",
        help="Filter by environment name using regex pattern",
    )
    env_list_servers_parser.add_argument(
        "--host",
        help="Filter by host name using regex pattern (use '-' for undeployed)",
    )
    env_list_servers_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # Set current environment command
    env_use_parser = env_subparsers.add_parser(
        "use", help="Set the current environment"
    )
    env_use_parser.add_argument("name", help="Environment name")
    env_use_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )

    # Show current environment command
    env_subparsers.add_parser("current", help="Show the current environment")

    # Show environment details command
    env_show_parser = env_subparsers.add_parser(
        "show", help="Show detailed environment configuration"
    )
    env_show_parser.add_argument("name", help="Environment name to show")

    # Python environment management commands
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
    python_init_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
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

    # Hatch MCP server wrapper management
    hatch_mcp_parser = env_python_subparsers.add_parser(
        "add-hatch-mcp", help="Add hatch_mcp_server wrapper to the environment"
    )
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
    hatch_mcp_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
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
    python_remove_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
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


def _setup_package_commands(subparsers):
    """Set up 'hatch package' command parsers."""
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
    pkg_add_parser.add_argument(
        "--host",
        help="Comma-separated list of MCP host platforms to configure (e.g., claude-desktop,cursor)",
    )
    pkg_add_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
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
    pkg_remove_parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without execution"
    )
    pkg_remove_parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompt"
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


def _setup_mcp_commands(subparsers):
    """Set up 'hatch mcp' command parsers."""
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
    mcp_discover_hosts_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
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

    # List hosts command - host-centric design per R10 §3.1
    mcp_list_hosts_parser = mcp_list_subparsers.add_parser(
        "hosts", help="List host/server pairs from host configuration files"
    )
    mcp_list_hosts_parser.add_argument(
        "--server",
        help="Filter by server name using regex pattern",
    )
    mcp_list_hosts_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # List servers command - per R10 §3.2 (--pattern removed, use mcp list hosts --server instead)
    mcp_list_servers_parser = mcp_list_subparsers.add_parser(
        "servers", help="List server/host pairs from host configuration files"
    )
    mcp_list_servers_parser.add_argument(
        "--host",
        help="Filter by host name using regex pattern",
    )
    mcp_list_servers_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # MCP show commands (detailed views) - per R11 specification
    mcp_show_subparsers = mcp_subparsers.add_parser(
        "show", help="Show detailed MCP host or server configuration"
    ).add_subparsers(dest="show_command", help="Show command to execute")

    # Show hosts command - host-centric detailed view per R11 §2.1
    mcp_show_hosts_parser = mcp_show_subparsers.add_parser(
        "hosts", help="Show detailed host configurations"
    )
    mcp_show_hosts_parser.add_argument(
        "--server",
        help="Filter by server name using regex pattern",
    )
    mcp_show_hosts_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
    )

    # Show servers command - server-centric detailed view per R11 §2.2
    mcp_show_servers_parser = mcp_show_subparsers.add_parser(
        "servers", help="Show detailed server configurations across hosts"
    )
    mcp_show_servers_parser.add_argument(
        "--host",
        help="Filter by host name using regex pattern",
    )
    mcp_show_servers_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
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
    mcp_backup_list_parser.add_argument(
        "--json", action="store_true", help="Output in JSON format"
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

    # MCP configure command
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

    # MCP remove commands
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

    # MCP sync command
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


def _route_env_command(args):
    """Route environment commands to handlers."""
    from hatch.cli.cli_env import (
        handle_env_create,
        handle_env_remove,
        handle_env_list,
        handle_env_list_hosts,
        handle_env_list_servers,
        handle_env_use,
        handle_env_current,
        handle_env_show,
        handle_env_python_init,
        handle_env_python_info,
        handle_env_python_remove,
        handle_env_python_shell,
        handle_env_python_add_hatch_mcp,
    )

    if args.env_command == "create":
        return handle_env_create(args)
    elif args.env_command == "remove":
        return handle_env_remove(args)
    elif args.env_command == "list":
        # Check for subcommand (hosts, servers) or default list behavior
        list_command = getattr(args, 'list_command', None)
        if list_command == "hosts":
            return handle_env_list_hosts(args)
        elif list_command == "servers":
            return handle_env_list_servers(args)
        else:
            # Default: list environments
            return handle_env_list(args)
    elif args.env_command == "use":
        return handle_env_use(args)
    elif args.env_command == "current":
        return handle_env_current(args)
    elif args.env_command == "show":
        return handle_env_show(args)
    elif args.env_command == "python":
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
    else:
        print("Unknown environment command")
        return 1


def _route_package_command(args):
    """Route package commands to handlers."""
    from hatch.cli.cli_package import (
        handle_package_add,
        handle_package_remove,
        handle_package_list,
        handle_package_sync,
    )

    if args.pkg_command == "add":
        return handle_package_add(args)
    elif args.pkg_command == "remove":
        return handle_package_remove(args)
    elif args.pkg_command == "list":
        return handle_package_list(args)
    elif args.pkg_command == "sync":
        return handle_package_sync(args)
    else:
        print("Unknown package command")
        return 1


def _route_mcp_command(args):
    """Route MCP commands to handlers."""
    from hatch.cli.cli_mcp import (
        handle_mcp_discover_hosts,
        handle_mcp_discover_servers,
        handle_mcp_list_hosts,
        handle_mcp_list_servers,
        handle_mcp_show_hosts,
        handle_mcp_show_servers,
        handle_mcp_backup_restore,
        handle_mcp_backup_list,
        handle_mcp_backup_clean,
        handle_mcp_configure,
        handle_mcp_remove_server,
        handle_mcp_remove_host,
        handle_mcp_sync,
    )

    if args.mcp_command == "discover":
        if args.discover_command == "hosts":
            return handle_mcp_discover_hosts(args)
        elif args.discover_command == "servers":
            return handle_mcp_discover_servers(args)
        else:
            print("Unknown discover command")
            return 1

    elif args.mcp_command == "list":
        if args.list_command == "hosts":
            return handle_mcp_list_hosts(args)
        elif args.list_command == "servers":
            return handle_mcp_list_servers(args)
        else:
            print("Unknown list command")
            return 1

    elif args.mcp_command == "show":
        show_command = getattr(args, 'show_command', None)
        if show_command == "hosts":
            return handle_mcp_show_hosts(args)
        elif show_command == "servers":
            return handle_mcp_show_servers(args)
        else:
            print("Unknown show command. Use 'hatch mcp show hosts' or 'hatch mcp show servers'")
            return 1

    elif args.mcp_command == "backup":
        if args.backup_command == "restore":
            return handle_mcp_backup_restore(args)
        elif args.backup_command == "list":
            return handle_mcp_backup_list(args)
        elif args.backup_command == "clean":
            return handle_mcp_backup_clean(args)
        else:
            print("Unknown backup command")
            return 1

    elif args.mcp_command == "configure":
        return handle_mcp_configure(args)

    elif args.mcp_command == "remove":
        if args.remove_command == "server":
            return handle_mcp_remove_server(args)
        elif args.remove_command == "host":
            return handle_mcp_remove_host(args)
        else:
            print("Unknown remove command")
            return 1

    elif args.mcp_command == "sync":
        return handle_mcp_sync(args)

    else:
        print("Unknown MCP command")
        return 1


def main():
    """Main entry point for Hatch CLI.

    Parses command-line arguments and routes to appropriate handlers for:
    - Package template creation
    - Package validation
    - Environment management
    - Package management
    - MCP host configuration

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

    # Set up command parsers
    _setup_create_command(subparsers)
    _setup_validate_command(subparsers)
    _setup_env_commands(subparsers)
    _setup_package_commands(subparsers)
    _setup_mcp_commands(subparsers)

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

    # Initialize managers (lazy - only when needed)
    from hatch.environment_manager import HatchEnvironmentManager
    from hatch.mcp_host_config import MCPHostConfigurationManager

    env_manager = HatchEnvironmentManager(
        environments_dir=args.envs_dir,
        cache_ttl=args.cache_ttl,
        cache_dir=args.cache_dir,
    )
    mcp_manager = MCPHostConfigurationManager()

    # Attach managers to args for handler access
    args.env_manager = env_manager
    args.mcp_manager = mcp_manager

    # Route commands
    if args.command == "create":
        from hatch.cli.cli_system import handle_create
        return handle_create(args)

    elif args.command == "validate":
        from hatch.cli.cli_system import handle_validate
        return handle_validate(args)

    elif args.command == "env":
        return _route_env_command(args)

    elif args.command == "package":
        return _route_package_command(args)

    elif args.command == "mcp":
        return _route_mcp_command(args)

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
