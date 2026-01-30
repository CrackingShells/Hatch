"""MCP host configuration handlers for Hatch CLI.

This module provides handlers for MCP (Model Context Protocol) host configuration
commands. MCP enables AI assistants to interact with external tools and services
through a standardized protocol.

Supported Hosts:
    - claude-desktop: Claude Desktop application
    - claude-code: Claude Code extension
    - cursor: Cursor IDE
    - vscode: Visual Studio Code with Copilot
    - kiro: Kiro IDE
    - codex: OpenAI Codex
    - lm-studio: LM Studio
    - gemini: Google Gemini

Command Groups:
    Discovery:
        - hatch mcp discover hosts: Detect available MCP host platforms
        - hatch mcp discover servers: Find MCP servers in packages

    Listing:
        - hatch mcp list hosts: Show configured hosts in environment
        - hatch mcp list servers: Show configured servers

    Backup:
        - hatch mcp backup restore: Restore configuration from backup
        - hatch mcp backup list: List available backups
        - hatch mcp backup clean: Clean old backups

    Configuration:
        - hatch mcp configure: Add or update MCP server configuration
        - hatch mcp remove: Remove server from specific host
        - hatch mcp remove-server: Remove server from multiple hosts
        - hatch mcp remove-host: Remove all servers from a host

    Synchronization:
        - hatch mcp sync: Sync package servers to hosts

Handler Signature:
    All handlers follow: (args: Namespace) -> int
    Returns EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure.

Example:
    $ hatch mcp discover hosts
    $ hatch mcp configure claude-desktop my-server --command python --args server.py
    $ hatch mcp backup list claude-desktop --detailed
"""

from argparse import Namespace
from pathlib import Path
from typing import Optional

from hatch.environment_manager import HatchEnvironmentManager
from hatch.mcp_host_config import (
    MCPHostConfigurationManager,
    MCPHostRegistry,
    MCPHostType,
    MCPServerConfig,
)

from hatch.cli.cli_utils import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    get_package_mcp_server_config,
    TableFormatter,
    ColumnDef,
)


def handle_mcp_discover_hosts(args: Namespace) -> int:
    """Handle 'hatch mcp discover hosts' command.
    
    Detects and displays available MCP host platforms on the system.
    
    Args:
        args: Parsed command-line arguments containing:
            - json: Optional flag for JSON output
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    try:
        import json as json_module
        
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies

        json_output: bool = getattr(args, 'json', False)
        available_hosts = MCPHostRegistry.detect_available_hosts()
        
        if json_output:
            # JSON output
            hosts_data = []
            for host_type in MCPHostType:
                try:
                    strategy = MCPHostRegistry.get_strategy(host_type)
                    config_path = strategy.get_config_path()
                    is_available = host_type in available_hosts
                    
                    hosts_data.append({
                        "host": host_type.value,
                        "available": is_available,
                        "config_path": str(config_path) if config_path else None
                    })
                except Exception as e:
                    hosts_data.append({
                        "host": host_type.value,
                        "available": False,
                        "error": str(e)
                    })
            
            print(json_module.dumps({"hosts": hosts_data}, indent=2))
            return EXIT_SUCCESS
        
        # Table output
        print("Available MCP Host Platforms:")

        # Define table columns per R02 §2.3
        columns = [
            ColumnDef(name="Host", width=18),
            ColumnDef(name="Status", width=15),
            ColumnDef(name="Config Path", width="auto"),
        ]
        formatter = TableFormatter(columns)

        for host_type in MCPHostType:
            try:
                strategy = MCPHostRegistry.get_strategy(host_type)
                config_path = strategy.get_config_path()
                is_available = host_type in available_hosts

                status = "✓ Available" if is_available else "✗ Not Found"
                path_str = str(config_path) if config_path else "-"
                formatter.add_row([host_type.value, status, path_str])
            except Exception as e:
                formatter.add_row([host_type.value, f"Error", str(e)[:30]])

        print(formatter.render())
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error discovering hosts: {e}")
        return EXIT_ERROR


def handle_mcp_discover_servers(args: Namespace) -> int:
    """Handle 'hatch mcp discover servers' command.
    
    .. deprecated::
        This command is deprecated. Use 'hatch mcp list servers' instead.
    
    Discovers MCP servers available in packages within an environment.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional environment name (uses current if not specified)
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    import warnings
    import sys
    
    # Emit deprecation warning to stderr
    print(
        "Warning: 'hatch mcp discover servers' is deprecated. "
        "Use 'hatch mcp list servers' instead.",
        file=sys.stderr
    )
    
    try:
        env_manager: HatchEnvironmentManager = args.env_manager
        env_name: Optional[str] = getattr(args, 'env', None)
        
        env_name = env_name or env_manager.get_current_environment()

        if not env_manager.environment_exists(env_name):
            print(f"Error: Environment '{env_name}' does not exist")
            return EXIT_ERROR

        packages = env_manager.list_packages(env_name)
        mcp_packages = []

        for package in packages:
            try:
                # Check if package has MCP server entry point
                server_config = get_package_mcp_server_config(
                    env_manager, env_name, package["name"]
                )
                mcp_packages.append(
                    {"package": package, "server_config": server_config}
                )
            except ValueError:
                # Package doesn't have MCP server
                continue

        if not mcp_packages:
            print(f"No MCP servers found in environment '{env_name}'")
            return EXIT_SUCCESS

        print(f"MCP servers in environment '{env_name}':")
        for item in mcp_packages:
            package = item["package"]
            server_config = item["server_config"]
            print(f"  {server_config.name}:")
            print(
                f"    Package: {package['name']} v{package.get('version', 'unknown')}"
            )
            print(f"    Command: {server_config.command}")
            print(f"    Args: {server_config.args}")
            if server_config.env:
                print(f"    Environment: {server_config.env}")

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error discovering servers: {e}")
        return EXIT_ERROR


def handle_mcp_list_hosts(args: Namespace) -> int:
    """Handle 'hatch mcp list hosts' command - host-centric design.
    
    Lists host/server pairs from host configuration files. Shows ALL servers
    on hosts (both Hatch-managed and 3rd party) with Hatch management status.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - server: Optional regex pattern to filter by server name
            - json: Optional flag for JSON output
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    
    Reference: R10 §3.1 (10-namespace_consistency_specification_v2.md)
    """
    try:
        import json as json_module
        import re
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        
        env_manager: HatchEnvironmentManager = args.env_manager
        server_pattern: Optional[str] = getattr(args, 'server', None)
        json_output: bool = getattr(args, 'json', False)
        
        # Compile regex pattern if provided
        pattern_re = None
        if server_pattern:
            try:
                pattern_re = re.compile(server_pattern)
            except re.error as e:
                print(f"Error: Invalid regex pattern '{server_pattern}': {e}")
                return EXIT_ERROR
        
        # Build Hatch management lookup: {server_name: {host: env_name}}
        hatch_managed = {}
        for env_info in env_manager.list_environments():
            env_name = env_info.get("name", env_info) if isinstance(env_info, dict) else env_info
            try:
                env_data = env_manager.get_environment_data(env_name)
                packages = env_data.get("packages", []) if isinstance(env_data, dict) else getattr(env_data, 'packages', [])
                
                for pkg in packages:
                    pkg_name = pkg.get("name") if isinstance(pkg, dict) else getattr(pkg, 'name', None)
                    configured_hosts = pkg.get("configured_hosts", {}) if isinstance(pkg, dict) else getattr(pkg, 'configured_hosts', {})
                    
                    if pkg_name:
                        if pkg_name not in hatch_managed:
                            hatch_managed[pkg_name] = {}
                        for host_name in configured_hosts.keys():
                            hatch_managed[pkg_name][host_name] = env_name
            except Exception:
                continue
        
        # Get all available hosts and read their configurations
        available_hosts = MCPHostRegistry.detect_available_hosts()
        
        # Collect host/server pairs from host config files
        # Format: (host, server, is_hatch_managed, env_name)
        host_rows = []
        
        for host_type in available_hosts:
            try:
                strategy = MCPHostRegistry.get_strategy(host_type)
                host_config = strategy.read_configuration()
                host_name = host_type.value
                
                for server_name, server_config in host_config.servers.items():
                    # Apply server pattern filter if specified
                    if pattern_re and not pattern_re.search(server_name):
                        continue
                    
                    # Check if Hatch-managed
                    is_hatch_managed = False
                    env_name = None
                    
                    if server_name in hatch_managed:
                        host_info = hatch_managed[server_name].get(host_name)
                        if host_info:
                            is_hatch_managed = True
                            env_name = host_info
                    
                    host_rows.append((host_name, server_name, is_hatch_managed, env_name))
            except Exception:
                # Skip hosts that can't be read
                continue
        
        # Sort rows by host (alphabetically), then by server
        host_rows.sort(key=lambda x: (x[0], x[1]))
        
        # JSON output per R10 §8
        if json_output:
            rows_data = []
            for host, server, is_hatch, env in host_rows:
                rows_data.append({
                    "host": host,
                    "server": server,
                    "hatch_managed": is_hatch,
                    "environment": env
                })
            print(json_module.dumps({"rows": rows_data}, indent=2))
            return EXIT_SUCCESS
        
        # Display results
        if not host_rows:
            if server_pattern:
                print(f"No MCP servers matching '{server_pattern}' on any host")
            else:
                print("No MCP servers found on any available hosts")
            return EXIT_SUCCESS
        
        print("MCP Hosts:")
        
        # Define table columns per R10 §3.1: Host → Server → Hatch → Environment
        columns = [
            ColumnDef(name="Host", width=18),
            ColumnDef(name="Server", width=18),
            ColumnDef(name="Hatch", width=8),
            ColumnDef(name="Environment", width=15),
        ]
        formatter = TableFormatter(columns)
        
        for host, server, is_hatch, env in host_rows:
            hatch_status = "✅" if is_hatch else "❌"
            env_display = env if env else "-"
            formatter.add_row([host, server, hatch_status, env_display])
        
        print(formatter.render())
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error listing hosts: {e}")
        return EXIT_ERROR


def handle_mcp_list_servers(args: Namespace) -> int:
    """Handle 'hatch mcp list servers' command.
    
    Lists server/host pairs from host configuration files. Shows ALL servers
    on hosts (both Hatch-managed and 3rd party) with Hatch management status.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - host: Optional regex pattern to filter by host name
            - json: Optional flag for JSON output
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    
    Reference: R10 §3.2 (10-namespace_consistency_specification_v2.md)
    """
    try:
        import json as json_module
        import re
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        
        env_manager: HatchEnvironmentManager = args.env_manager
        host_pattern: Optional[str] = getattr(args, 'host', None)
        json_output: bool = getattr(args, 'json', False)
        
        # Compile host regex pattern if provided
        host_re = None
        if host_pattern:
            try:
                host_re = re.compile(host_pattern)
            except re.error as e:
                print(f"Error: Invalid regex pattern '{host_pattern}': {e}")
                return EXIT_ERROR
        
        # Get all available hosts
        available_hosts = MCPHostRegistry.detect_available_hosts()
        
        # Build Hatch management lookup: {server_name: {host: (env_name, version)}}
        hatch_managed = {}
        for env_info in env_manager.list_environments():
            env_name = env_info.get("name", env_info) if isinstance(env_info, dict) else env_info
            try:
                env_data = env_manager.get_environment_data(env_name)
                packages = env_data.get("packages", []) if isinstance(env_data, dict) else getattr(env_data, 'packages', [])
                
                for pkg in packages:
                    pkg_name = pkg.get("name") if isinstance(pkg, dict) else getattr(pkg, 'name', None)
                    pkg_version = pkg.get("version", "-") if isinstance(pkg, dict) else getattr(pkg, 'version', '-')
                    configured_hosts = pkg.get("configured_hosts", {}) if isinstance(pkg, dict) else getattr(pkg, 'configured_hosts', {})
                    
                    if pkg_name:
                        if pkg_name not in hatch_managed:
                            hatch_managed[pkg_name] = {}
                        for host_name in configured_hosts.keys():
                            hatch_managed[pkg_name][host_name] = (env_name, pkg_version)
            except Exception:
                continue
        
        # Collect server data from host config files
        # Format: (server_name, host, is_hatch_managed, env_name, version)
        server_rows = []
        
        for host_type in available_hosts:
            try:
                strategy = MCPHostRegistry.get_strategy(host_type)
                host_config = strategy.read_configuration()
                host_name = host_type.value
                
                # Apply host pattern filter if specified
                if host_re and not host_re.search(host_name):
                    continue
                
                for server_name, server_config in host_config.servers.items():
                    # Check if Hatch-managed
                    is_hatch_managed = False
                    env_name = "-"
                    version = "-"
                    
                    if server_name in hatch_managed:
                        host_info = hatch_managed[server_name].get(host_name)
                        if host_info:
                            is_hatch_managed = True
                            env_name, version = host_info
                    
                    server_rows.append((server_name, host_name, is_hatch_managed, env_name, version))
            except Exception:
                # Skip hosts that can't be read
                continue
        
        # Sort rows by server (alphabetically), then by host per R10 §3.2
        server_rows.sort(key=lambda x: (x[0], x[1]))
        
        # JSON output
        if json_output:
            servers_data = []
            for server_name, host, is_hatch, env, version in server_rows:
                server_entry = {
                    "server": server_name,
                    "host": host,
                    "hatch_managed": is_hatch,
                    "environment": env if is_hatch else None,
                }
                servers_data.append(server_entry)
            
            print(json_module.dumps({"rows": servers_data}, indent=2))
            return EXIT_SUCCESS

        if not server_rows:
            if host_pattern:
                print(f"No MCP servers on hosts matching '{host_pattern}'")
            else:
                print("No MCP servers found on any available hosts")
            return EXIT_SUCCESS

        print("MCP Servers:")
        
        # Define table columns per R10 §3.2: Server → Host → Hatch → Environment
        columns = [
            ColumnDef(name="Server", width=18),
            ColumnDef(name="Host", width=18),
            ColumnDef(name="Hatch", width=8),
            ColumnDef(name="Environment", width=15),
        ]
        formatter = TableFormatter(columns)

        for server_name, host, is_hatch, env, version in server_rows:
            hatch_status = "✅" if is_hatch else "❌"
            env_display = env if is_hatch else "-"
            formatter.add_row([server_name, host, hatch_status, env_display])

        print(formatter.render())
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error listing servers: {e}")
        return EXIT_ERROR


def handle_mcp_show(args: Namespace) -> int:
    """Handle 'hatch mcp show' command.
    
    Displays detailed hierarchical view of a specific MCP host configuration.
    
    Args:
        args: Parsed command-line arguments containing:
            - host: Host platform to show (e.g., claude-desktop, cursor)
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    
    Reference: R02 §2.6 (02-list_output_format_specification_v2.md)
    """
    try:
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager
        import os

        host: str = args.host

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(
                f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        # Get host strategy and configuration
        strategy = MCPHostRegistry.get_strategy(host_type)
        config_path = strategy.get_config_path()

        # Header
        print(f"MCP Host: {host}")
        print(f"  Config Path: {config_path or 'N/A'}")

        # Last modified timestamp
        if config_path and config_path.exists():
            import datetime
            mtime = os.path.getmtime(config_path)
            last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  Last Modified: {last_modified}")
        else:
            print(f"  Last Modified: N/A (config not found)")

        # Backup info
        backup_manager = MCPHostConfigBackupManager()
        backups = backup_manager.list_backups(host)
        if backups:
            print(f"  Backup Available: Yes ({len(backups)} backups)")
        else:
            print(f"  Backup Available: No")
        print()

        # Read current configuration
        try:
            host_config = strategy.read_configuration()
            servers = host_config.servers
        except Exception:
            servers = {}

        # Configured Servers section
        server_count = len(servers) if servers else 0
        print(f"  Configured Servers ({server_count}):")

        if servers:
            # Get environment manager to check Hatch management status
            env_manager: HatchEnvironmentManager = getattr(args, 'env_manager', None)
            
            for server_name, server_config in servers.items():
                # Check if Hatch-managed
                hatch_env = None
                pkg_version = None
                last_synced = None
                
                if env_manager:
                    # Search all environments for this server
                    for env_name in env_manager.list_environments():
                        env_data = env_manager.get_environment_data(env_name.get("name", env_name) if isinstance(env_name, dict) else env_name)
                        for pkg in env_data.get("packages", []):
                            if pkg.get("name") == server_name:
                                configured_hosts = pkg.get("configured_hosts", {})
                                if host in configured_hosts:
                                    hatch_env = env_name.get("name", env_name) if isinstance(env_name, dict) else env_name
                                    pkg_version = pkg.get("version", "unknown")
                                    last_synced = configured_hosts[host].get("configured_at", "N/A")
                                    break
                        if hatch_env:
                            break

                # Server header
                if hatch_env:
                    print(f"    {server_name} (Hatch-managed: {hatch_env})")
                else:
                    print(f"    {server_name} (Not Hatch-managed)")

                # Command and args
                command = getattr(server_config, 'command', None)
                if command:
                    print(f"      Command: {command}")
                
                cmd_args = getattr(server_config, 'args', None)
                if cmd_args:
                    print(f"      Args: {cmd_args}")

                # URL for remote servers
                url = getattr(server_config, 'url', None)
                if url:
                    print(f"      URL: {url}")

                # Environment variables (hide sensitive values)
                env_vars = getattr(server_config, 'env', None)
                if env_vars:
                    print(f"      Environment Variables:")
                    for key, value in env_vars.items():
                        # Hide sensitive values
                        if any(sensitive in key.upper() for sensitive in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'CREDENTIAL']):
                            print(f"        {key}: ****** (hidden)")
                        else:
                            print(f"        {key}: {value}")

                # Hatch-specific info
                if hatch_env:
                    if last_synced:
                        print(f"      Last Synced: {last_synced}")
                    if pkg_version:
                        print(f"      Package Version: {pkg_version}")

                print()
        else:
            print("    (none)")

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error showing host configuration: {e}")
        return EXIT_ERROR


def handle_mcp_show_hosts(args: Namespace) -> int:
    """Handle 'hatch mcp show hosts' command.
    
    Shows detailed hierarchical view of all MCP host configurations.
    Supports --server filter for regex pattern matching.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - server: Optional regex pattern to filter by server name
            - json: Optional flag for JSON output
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    
    Reference: R11 §2.1 (11-enhancing_show_command_v0.md)
    """
    try:
        import json as json_module
        import re
        import os
        import datetime
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager
        from hatch.cli.cli_utils import highlight
        
        env_manager: HatchEnvironmentManager = args.env_manager
        server_pattern: Optional[str] = getattr(args, 'server', None)
        json_output: bool = getattr(args, 'json', False)
        
        # Compile regex pattern if provided
        pattern_re = None
        if server_pattern:
            try:
                pattern_re = re.compile(server_pattern)
            except re.error as e:
                print(f"Error: Invalid regex pattern '{server_pattern}': {e}")
                return EXIT_ERROR
        
        # Build Hatch management lookup: {server_name: {host: (env_name, version, last_synced)}}
        hatch_managed = {}
        for env_info in env_manager.list_environments():
            env_name = env_info.get("name", env_info) if isinstance(env_info, dict) else env_info
            try:
                env_data = env_manager.get_environment_data(env_name)
                packages = env_data.get("packages", []) if isinstance(env_data, dict) else getattr(env_data, 'packages', [])
                
                for pkg in packages:
                    pkg_name = pkg.get("name") if isinstance(pkg, dict) else getattr(pkg, 'name', None)
                    pkg_version = pkg.get("version", "unknown") if isinstance(pkg, dict) else getattr(pkg, 'version', 'unknown')
                    configured_hosts = pkg.get("configured_hosts", {}) if isinstance(pkg, dict) else getattr(pkg, 'configured_hosts', {})
                    
                    if pkg_name:
                        if pkg_name not in hatch_managed:
                            hatch_managed[pkg_name] = {}
                        for host_name, host_info in configured_hosts.items():
                            last_synced = host_info.get("configured_at", "N/A") if isinstance(host_info, dict) else "N/A"
                            hatch_managed[pkg_name][host_name] = (env_name, pkg_version, last_synced)
            except Exception:
                continue
        
        # Get all available hosts
        available_hosts = MCPHostRegistry.detect_available_hosts()
        
        # Sort hosts alphabetically
        sorted_hosts = sorted(available_hosts, key=lambda h: h.value)
        
        # Collect host data for output
        hosts_data = []
        
        for host_type in sorted_hosts:
            try:
                strategy = MCPHostRegistry.get_strategy(host_type)
                host_config = strategy.read_configuration()
                host_name = host_type.value
                config_path = strategy.get_config_path()
                
                # Filter servers by pattern if specified
                filtered_servers = {}
                for server_name, server_config in host_config.servers.items():
                    if pattern_re and not pattern_re.search(server_name):
                        continue
                    filtered_servers[server_name] = server_config
                
                # Skip host if no matching servers
                if not filtered_servers:
                    continue
                
                # Get host metadata
                last_modified = None
                if config_path and config_path.exists():
                    mtime = os.path.getmtime(config_path)
                    last_modified = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                backup_manager = MCPHostConfigBackupManager()
                backups = backup_manager.list_backups(host_name)
                backup_count = len(backups) if backups else 0
                
                # Build server data
                servers_data = []
                for server_name in sorted(filtered_servers.keys()):
                    server_config = filtered_servers[server_name]
                    
                    # Check if Hatch-managed
                    hatch_info = hatch_managed.get(server_name, {}).get(host_name)
                    is_hatch_managed = hatch_info is not None
                    env_name = hatch_info[0] if hatch_info else None
                    pkg_version = hatch_info[1] if hatch_info else None
                    last_synced = hatch_info[2] if hatch_info else None
                    
                    server_data = {
                        "name": server_name,
                        "hatch_managed": is_hatch_managed,
                        "environment": env_name,
                        "version": pkg_version,
                        "command": getattr(server_config, 'command', None),
                        "args": getattr(server_config, 'args', None),
                        "url": getattr(server_config, 'url', None),
                        "env": {},
                        "last_synced": last_synced,
                    }
                    
                    # Get environment variables (hide sensitive values for display)
                    env_vars = getattr(server_config, 'env', None)
                    if env_vars:
                        for key, value in env_vars.items():
                            if any(sensitive in key.upper() for sensitive in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'CREDENTIAL']):
                                server_data["env"][key] = "****** (hidden)"
                            else:
                                server_data["env"][key] = value
                    
                    servers_data.append(server_data)
                
                hosts_data.append({
                    "host": host_name,
                    "config_path": str(config_path) if config_path else None,
                    "last_modified": last_modified,
                    "backup_count": backup_count,
                    "servers": servers_data,
                })
            except Exception:
                continue
        
        # JSON output
        if json_output:
            print(json_module.dumps({"hosts": hosts_data}, indent=2))
            return EXIT_SUCCESS
        
        # Human-readable output
        if not hosts_data:
            if server_pattern:
                print(f"No hosts with servers matching '{server_pattern}'")
            else:
                print("No MCP hosts found")
            return EXIT_SUCCESS
        
        separator = "═" * 79
        
        for host_data in hosts_data:
            # Horizontal separator
            print(separator)
            
            # Host header with highlight
            print(f"MCP Host: {highlight(host_data['host'])}")
            print(f"  Config Path: {host_data['config_path'] or 'N/A'}")
            print(f"  Last Modified: {host_data['last_modified'] or 'N/A'}")
            if host_data['backup_count'] > 0:
                print(f"  Backup Available: Yes ({host_data['backup_count']} backups)")
            else:
                print(f"  Backup Available: No")
            print()
            
            # Configured Servers section
            print(f"  Configured Servers ({len(host_data['servers'])}):")
            
            for server in host_data['servers']:
                # Server header with highlight
                if server['hatch_managed']:
                    print(f"    {highlight(server['name'])} (Hatch-managed: {server['environment']})")
                else:
                    print(f"    {highlight(server['name'])} (Not Hatch-managed)")
                
                # Command and args
                if server['command']:
                    print(f"      Command: {server['command']}")
                if server['args']:
                    print(f"      Args: {server['args']}")
                
                # URL for remote servers
                if server['url']:
                    print(f"      URL: {server['url']}")
                
                # Environment variables
                if server['env']:
                    print(f"      Environment Variables:")
                    for key, value in server['env'].items():
                        print(f"        {key}: {value}")
                
                # Hatch-specific info
                if server['hatch_managed']:
                    if server['last_synced']:
                        print(f"      Last Synced: {server['last_synced']}")
                    if server['version']:
                        print(f"      Package Version: {server['version']}")
                
                print()
        
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error showing host configurations: {e}")
        return EXIT_ERROR


def handle_mcp_backup_restore(args: Namespace) -> int:
    """Handle 'hatch mcp backup restore' command.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - host: Host platform to restore
            - backup_file: Optional specific backup file (default: latest)
            - dry_run: Preview without execution
            - auto_approve: Skip confirmation prompts
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    from hatch.cli.cli_utils import (
        request_confirmation,
        ResultReporter,
        ConsequenceType,
    )
    
    try:
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        env_manager: HatchEnvironmentManager = args.env_manager
        host: str = args.host
        backup_file: Optional[str] = getattr(args, 'backup_file', None)
        dry_run: bool = getattr(args, 'dry_run', False)
        auto_approve: bool = getattr(args, 'auto_approve', False)

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(
                f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        backup_manager = MCPHostConfigBackupManager()

        # Get backup file path
        if backup_file:
            backup_path = backup_manager.backup_root / host / backup_file
            if not backup_path.exists():
                print(f"Error: Backup file '{backup_file}' not found for host '{host}'")
                return EXIT_ERROR
        else:
            backup_path = backup_manager._get_latest_backup(host)
            if not backup_path:
                print(f"Error: No backups found for host '{host}'")
                return EXIT_ERROR
            backup_file = backup_path.name

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp backup restore", dry_run=dry_run)
        reporter.add(ConsequenceType.RESTORE, f"Backup '{backup_file}' to host '{host}'")

        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform restoration
        success = backup_manager.restore_backup(host, backup_file)

        if success:
            reporter.report_result()

            # Read restored configuration to get actual server list
            try:
                # Import strategies to trigger registration
                import hatch.mcp_host_config.strategies

                host_type = MCPHostType(host)
                strategy = MCPHostRegistry.get_strategy(host_type)
                restored_config = strategy.read_configuration()

                # Update environment tracking to match restored state
                updates_count = (
                    env_manager.apply_restored_host_configuration_to_environments(
                        host, restored_config.servers
                    )
                )
                if updates_count > 0:
                    print(
                        f"  Synchronized {updates_count} package entries with restored configuration"
                    )

            except Exception as e:
                print(f"  Warning: Could not synchronize environment tracking: {e}")

            return EXIT_SUCCESS
        else:
            print(f"[ERROR] Failed to restore backup '{backup_file}' for host '{host}'")
            return EXIT_ERROR

    except Exception as e:
        print(f"Error restoring backup: {e}")
        return EXIT_ERROR


def handle_mcp_backup_list(args: Namespace) -> int:
    """Handle 'hatch mcp backup list' command.
    
    Args:
        args: Parsed command-line arguments containing:
            - host: Host platform to list backups for
            - detailed: Show detailed backup information
            - json: Optional flag for JSON output
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    try:
        import json as json_module
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        host: str = args.host
        detailed: bool = getattr(args, 'detailed', False)
        json_output: bool = getattr(args, 'json', False)

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(
                f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        backup_manager = MCPHostConfigBackupManager()
        backups = backup_manager.list_backups(host)

        # JSON output
        if json_output:
            backups_data = []
            for backup in backups:
                backups_data.append({
                    "file": backup.file_path.name,
                    "created": backup.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "size_bytes": backup.file_size,
                    "age_days": backup.age_days
                })
            print(json_module.dumps({
                "host": host,
                "backups": backups_data
            }, indent=2))
            return EXIT_SUCCESS

        if not backups:
            print(f"No backups found for host '{host}'")
            return EXIT_SUCCESS

        print(f"Backups for host '{host}' ({len(backups)} found):")

        if detailed:
            # Define table columns per R02 §2.7
            columns = [
                ColumnDef(name="Backup File", width=40),
                ColumnDef(name="Created", width=20),
                ColumnDef(name="Size", width=12, align="right"),
                ColumnDef(name="Age (days)", width=10, align="right"),
            ]
            formatter = TableFormatter(columns)

            for backup in backups:
                created = backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                size = f"{backup.file_size:,} B"
                age = str(backup.age_days)
                formatter.add_row([backup.file_path.name, created, size, age])

            print(formatter.render())
        else:
            for backup in backups:
                created = backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"  {backup.file_path.name} (created: {created}, {backup.age_days} days ago)"
                )

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error listing backups: {e}")
        return EXIT_ERROR


def handle_mcp_backup_clean(args: Namespace) -> int:
    """Handle 'hatch mcp backup clean' command.
    
    Args:
        args: Parsed command-line arguments containing:
            - host: Host platform to clean backups for
            - older_than_days: Remove backups older than specified days
            - keep_count: Keep only the specified number of newest backups
            - dry_run: Preview without execution
            - auto_approve: Skip confirmation prompts
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    from hatch.cli.cli_utils import (
        request_confirmation,
        ResultReporter,
        ConsequenceType,
    )
    
    try:
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        host: str = args.host
        older_than_days: Optional[int] = getattr(args, 'older_than_days', None)
        keep_count: Optional[int] = getattr(args, 'keep_count', None)
        dry_run: bool = getattr(args, 'dry_run', False)
        auto_approve: bool = getattr(args, 'auto_approve', False)

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(
                f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        # Validate cleanup criteria
        if not older_than_days and not keep_count:
            print("Error: Must specify either --older-than-days or --keep-count")
            return EXIT_ERROR

        backup_manager = MCPHostConfigBackupManager()
        backups = backup_manager.list_backups(host)

        if not backups:
            print(f"No backups found for host '{host}'")
            return EXIT_SUCCESS

        # Determine which backups would be cleaned
        to_clean = []

        if older_than_days:
            for backup in backups:
                if backup.age_days > older_than_days:
                    to_clean.append(backup)

        if keep_count and len(backups) > keep_count:
            # Keep newest backups, remove oldest
            to_clean.extend(backups[keep_count:])

        # Remove duplicates while preserving order
        seen = set()
        unique_to_clean = []
        for backup in to_clean:
            if backup.file_path not in seen:
                seen.add(backup.file_path)
                unique_to_clean.append(backup)

        if not unique_to_clean:
            print(f"No backups match cleanup criteria for host '{host}'")
            return EXIT_SUCCESS

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp backup clean", dry_run=dry_run)
        for backup in unique_to_clean:
            reporter.add(ConsequenceType.CLEAN, f"{backup.file_path.name} (age: {backup.age_days} days)")

        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform cleanup
        filters = {}
        if older_than_days:
            filters["older_than_days"] = older_than_days
        if keep_count:
            filters["keep_count"] = keep_count

        cleaned_count = backup_manager.clean_backups(host, **filters)

        if cleaned_count > 0:
            reporter.report_result()
            return EXIT_SUCCESS
        else:
            print(f"No backups were cleaned for host '{host}'")
            return EXIT_SUCCESS

    except Exception as e:
        print(f"Error cleaning backups: {e}")
        return EXIT_ERROR


def handle_mcp_configure(args: Namespace) -> int:
    """Handle 'hatch mcp configure' command with ALL host-specific arguments.

    Host-specific arguments are accepted for all hosts. The reporting system will
    show unsupported fields as "UNSUPPORTED" in the conversion report rather than
    rejecting them upfront.

    The CLI creates a unified MCPServerConfig directly. Adapters handle host-specific
    validation and serialization when writing to host configuration files.

    Args:
        args: Parsed command-line arguments containing all configuration options

    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    import shlex
    from hatch.cli.cli_utils import (
        request_confirmation,
        parse_env_vars,
        parse_header,
        parse_input,
        ResultReporter,
        ConsequenceType,
    )
    from hatch.mcp_host_config.reporting import generate_conversion_report
    
    try:
        # Extract arguments from Namespace
        host: str = args.host
        server_name: str = args.server_name
        command: Optional[str] = getattr(args, 'server_command', None)
        cmd_args: Optional[list] = getattr(args, 'args', None)
        env: Optional[list] = getattr(args, 'env_var', None)
        url: Optional[str] = getattr(args, 'url', None)
        header: Optional[list] = getattr(args, 'header', None)
        timeout: Optional[int] = getattr(args, 'timeout', None)
        trust: bool = getattr(args, 'trust', False)
        cwd: Optional[str] = getattr(args, 'cwd', None)
        env_file: Optional[str] = getattr(args, 'env_file', None)
        http_url: Optional[str] = getattr(args, 'http_url', None)
        include_tools: Optional[list] = getattr(args, 'include_tools', None)
        exclude_tools: Optional[list] = getattr(args, 'exclude_tools', None)
        input_vars: Optional[list] = getattr(args, 'input', None)
        disabled: Optional[bool] = getattr(args, 'disabled', None)
        auto_approve_tools: Optional[list] = getattr(args, 'auto_approve_tools', None)
        disable_tools: Optional[list] = getattr(args, 'disable_tools', None)
        env_vars: Optional[list] = getattr(args, 'env_vars', None)
        startup_timeout: Optional[int] = getattr(args, 'startup_timeout', None)
        tool_timeout: Optional[int] = getattr(args, 'tool_timeout', None)
        enabled: Optional[bool] = getattr(args, 'enabled', None)
        bearer_token_env_var: Optional[str] = getattr(args, 'bearer_token_env_var', None)
        env_header: Optional[list] = getattr(args, 'env_header', None)
        no_backup: bool = getattr(args, 'no_backup', False)
        dry_run: bool = getattr(args, 'dry_run', False)
        auto_approve: bool = getattr(args, 'auto_approve', False)

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(
                f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        # Validate Claude Desktop/Code transport restrictions (Issue 2)
        if host_type in (MCPHostType.CLAUDE_DESKTOP, MCPHostType.CLAUDE_CODE):
            if url is not None:
                print(
                    f"Error: {host} does not support remote servers (--url). Only local servers with --command are supported."
                )
                return EXIT_ERROR

        # Validate argument dependencies
        if command and header:
            print(
                "Error: --header can only be used with --url or --http-url (remote servers), not with --command (local servers)"
            )
            return EXIT_ERROR

        if (url or http_url) and cmd_args:
            print(
                "Error: --args can only be used with --command (local servers), not with --url or --http-url (remote servers)"
            )
            return EXIT_ERROR

        # Check if server exists (for partial update support)
        manager = MCPHostConfigurationManager()
        existing_config = manager.get_server_config(host, server_name)
        is_update = existing_config is not None

        # Conditional validation: Create requires command OR url OR http_url, update does not
        if not is_update:
            if not command and not url and not http_url:
                print(
                    f"Error: When creating a new server, you must provide either --command (for local servers), --url (for SSE remote servers), or --http-url (for HTTP remote servers, Gemini only)"
                )
                return EXIT_ERROR

        # Parse environment variables, headers, and inputs
        env_dict = parse_env_vars(env)
        headers_dict = parse_header(header)
        inputs_list = parse_input(input_vars)

        # Build unified configuration data
        config_data = {"name": server_name}

        if command is not None:
            config_data["command"] = command
        if cmd_args is not None:
            # Process args with shlex.split() to handle quoted strings
            processed_args = []
            for arg in cmd_args:
                if arg:
                    try:
                        split_args = shlex.split(arg)
                        processed_args.extend(split_args)
                    except ValueError as e:
                        print(f"Warning: Invalid quote in argument '{arg}': {e}")
                        processed_args.append(arg)
            config_data["args"] = processed_args if processed_args else None
        if env_dict:
            config_data["env"] = env_dict
        if url is not None:
            config_data["url"] = url
        if headers_dict:
            config_data["headers"] = headers_dict

        # Host-specific fields (Gemini)
        if timeout is not None:
            config_data["timeout"] = timeout
        if trust:
            config_data["trust"] = trust
        if cwd is not None:
            config_data["cwd"] = cwd
        if http_url is not None:
            config_data["httpUrl"] = http_url
        if include_tools is not None:
            config_data["includeTools"] = include_tools
        if exclude_tools is not None:
            config_data["excludeTools"] = exclude_tools

        # Host-specific fields (Cursor/VS Code/LM Studio)
        if env_file is not None:
            config_data["envFile"] = env_file

        # Host-specific fields (VS Code)
        if inputs_list is not None:
            config_data["inputs"] = inputs_list

        # Host-specific fields (Kiro)
        if disabled is not None:
            config_data["disabled"] = disabled
        if auto_approve_tools is not None:
            config_data["autoApprove"] = auto_approve_tools
        if disable_tools is not None:
            config_data["disabledTools"] = disable_tools

        # Host-specific fields (Codex)
        if env_vars is not None:
            config_data["env_vars"] = env_vars
        if startup_timeout is not None:
            config_data["startup_timeout_sec"] = startup_timeout
        if tool_timeout is not None:
            config_data["tool_timeout_sec"] = tool_timeout
        if enabled is not None:
            config_data["enabled"] = enabled
        if bearer_token_env_var is not None:
            config_data["bearer_token_env_var"] = bearer_token_env_var
        if env_header is not None:
            env_http_headers = {}
            for header_spec in env_header:
                if '=' in header_spec:
                    key, env_var_name = header_spec.split('=', 1)
                    env_http_headers[key] = env_var_name
            if env_http_headers:
                config_data["env_http_headers"] = env_http_headers

        # Partial update merge logic
        if is_update:
            existing_data = existing_config.model_dump(
                exclude_unset=True, exclude={"name"}
            )

            if (url is not None or http_url is not None) and existing_config.command is not None:
                existing_data.pop("command", None)
                existing_data.pop("args", None)
                existing_data.pop("type", None)

            if command is not None and (
                existing_config.url is not None
                or getattr(existing_config, "httpUrl", None) is not None
            ):
                existing_data.pop("url", None)
                existing_data.pop("httpUrl", None)
                existing_data.pop("headers", None)
                existing_data.pop("type", None)

            merged_data = {**existing_data, **config_data}
            config_data = merged_data

        # Create unified MCPServerConfig directly
        # Adapters handle host-specific validation and serialization
        server_config = MCPServerConfig(**config_data)

        # Generate conversion report
        report = generate_conversion_report(
            operation="update" if is_update else "create",
            server_name=server_name,
            target_host=host_type,
            config=server_config,
            old_config=existing_config if is_update else None,
            dry_run=dry_run,
        )

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp configure", dry_run=dry_run)
        reporter.add_from_conversion_report(report)

        # Display prompt and handle dry-run
        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        if not request_confirmation(
            f"Proceed?", auto_approve
        ):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform configuration
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.configure_server(
            server_config=server_config, hostname=host, no_backup=no_backup
        )

        if result.success:
            reporter.report_result()
            if result.backup_path:
                print(f"  Backup: {result.backup_path}")
            return EXIT_SUCCESS
        else:
            print(
                f"[ERROR] Failed to configure MCP server '{server_name}' on host '{host}': {result.error_message}"
            )
            return EXIT_ERROR

    except Exception as e:
        print(f"Error configuring MCP server: {e}")
        return EXIT_ERROR


def handle_mcp_remove(args: Namespace) -> int:
    """Handle 'hatch mcp remove' command.
    
    Removes an MCP server configuration from a specific host.
    
    Args:
        args: Namespace with:
            - host: Target host identifier (e.g., 'claude-desktop', 'vscode')
            - server_name: Name of the server to remove
            - no_backup: If True, skip creating backup before removal
            - dry_run: If True, show what would be done without making changes
            - auto_approve: If True, skip confirmation prompt
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    from hatch.cli.cli_utils import (
        request_confirmation,
        ResultReporter,
        ConsequenceType,
    )
    
    host = args.host
    server_name = args.server_name
    no_backup = getattr(args, "no_backup", False)
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)
    
    try:
        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(
                f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp remove", dry_run=dry_run)
        reporter.add(ConsequenceType.REMOVE, f"Server '{server_name}' from '{host}'")

        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform removal
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.remove_server(
            server_name=server_name, hostname=host, no_backup=no_backup
        )

        if result.success:
            reporter.report_result()
            if result.backup_path:
                print(f"  Backup: {result.backup_path}")
            return EXIT_SUCCESS
        else:
            print(
                f"[ERROR] Failed to remove MCP server '{server_name}' from host '{host}': {result.error_message}"
            )
            return EXIT_ERROR

    except Exception as e:
        print(f"Error removing MCP server: {e}")
        return EXIT_ERROR


def handle_mcp_remove_server(args: Namespace) -> int:
    """Handle 'hatch mcp remove server' command.
    
    Removes an MCP server from multiple hosts.
    
    Args:
        args: Namespace with:
            - env_manager: Environment manager instance for tracking
            - server_name: Name of the server to remove
            - host: Comma-separated list of target hosts
            - env: Environment name (for environment-based removal)
            - no_backup: If True, skip creating backups
            - dry_run: If True, show what would be done without making changes
            - auto_approve: If True, skip confirmation prompt
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    from hatch.cli.cli_utils import (
        request_confirmation,
        parse_host_list,
        ResultReporter,
        ConsequenceType,
    )
    
    env_manager = args.env_manager
    server_name = args.server_name
    hosts = getattr(args, "host", None)
    env = getattr(args, "env", None)
    no_backup = getattr(args, "no_backup", False)
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)
    
    try:
        # Determine target hosts
        if hosts:
            target_hosts = parse_host_list(hosts)
        elif env:
            # TODO: Implement environment-based server removal
            print("Error: Environment-based removal not yet implemented")
            return EXIT_ERROR
        else:
            print("Error: Must specify either --host or --env")
            return EXIT_ERROR

        if not target_hosts:
            print("Error: No valid hosts specified")
            return EXIT_ERROR

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp remove-server", dry_run=dry_run)
        for host in target_hosts:
            reporter.add(ConsequenceType.REMOVE, f"Server '{server_name}' from '{host}'")

        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform removal on each host
        mcp_manager = MCPHostConfigurationManager()
        success_count = 0
        total_count = len(target_hosts)
        
        # Create result reporter for actual results
        result_reporter = ResultReporter("hatch mcp remove-server", dry_run=False)

        for host in target_hosts:
            result = mcp_manager.remove_server(
                server_name=server_name, hostname=host, no_backup=no_backup
            )

            if result.success:
                result_reporter.add(ConsequenceType.REMOVE, f"'{server_name}' from '{host}'")
                success_count += 1

                # Update environment tracking for current environment only
                current_env = env_manager.get_current_environment()
                if current_env:
                    env_manager.remove_package_host_configuration(
                        current_env, server_name, host
                    )
            else:
                result_reporter.add(ConsequenceType.SKIP, f"'{server_name}' from '{host}': {result.error_message}")

        # Summary
        if success_count == total_count:
            result_reporter.report_result()
            return EXIT_SUCCESS
        elif success_count > 0:
            print(f"[WARNING] Partial success: {success_count}/{total_count} hosts")
            result_reporter.report_result()
            return EXIT_ERROR
        else:
            print(f"[ERROR] Failed to remove '{server_name}' from any hosts")
            return EXIT_ERROR

    except Exception as e:
        print(f"Error removing MCP server: {e}")
        return EXIT_ERROR


def handle_mcp_remove_host(args: Namespace) -> int:
    """Handle 'hatch mcp remove host' command.
    
    Removes entire host configuration (all MCP servers from a host).
    
    Args:
        args: Namespace with:
            - env_manager: Environment manager instance for tracking
            - host_name: Name of the host to remove configuration from
            - no_backup: If True, skip creating backup
            - dry_run: If True, show what would be done without making changes
            - auto_approve: If True, skip confirmation prompt
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    from hatch.cli.cli_utils import (
        request_confirmation,
        ResultReporter,
        ConsequenceType,
    )
    
    env_manager = args.env_manager
    host_name = args.host_name
    no_backup = getattr(args, "no_backup", False)
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)
    
    try:
        # Validate host type
        try:
            host_type = MCPHostType(host_name)
        except ValueError:
            print(
                f"Error: Invalid host '{host_name}'. Supported hosts: {[h.value for h in MCPHostType]}"
            )
            return EXIT_ERROR

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp remove-host", dry_run=dry_run)
        reporter.add(ConsequenceType.REMOVE, f"All servers from host '{host_name}'")

        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform host configuration removal
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.remove_host_configuration(
            hostname=host_name, no_backup=no_backup
        )

        if result.success:
            reporter.report_result()
            if result.backup_path:
                print(f"  Backup: {result.backup_path}")

            # Update environment tracking across all environments
            updates_count = env_manager.clear_host_from_all_packages_all_envs(host_name)
            if updates_count > 0:
                print(f"  Updated {updates_count} package entries across environments")

            return EXIT_SUCCESS
        else:
            print(
                f"[ERROR] Failed to remove host configuration for '{host_name}': {result.error_message}"
            )
            return EXIT_ERROR

    except Exception as e:
        print(f"Error removing host configuration: {e}")
        return EXIT_ERROR


def handle_mcp_sync(args: Namespace) -> int:
    """Handle 'hatch mcp sync' command.
    
    Synchronizes MCP server configurations from a source to target hosts.
    
    Args:
        args: Namespace with:
            - from_env: Source environment name
            - from_host: Source host name
            - to_host: Comma-separated list of target hosts
            - servers: Comma-separated list of server names to sync
            - pattern: Pattern to filter servers
            - dry_run: If True, show what would be done without making changes
            - auto_approve: If True, skip confirmation prompt
            - no_backup: If True, skip creating backups
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    from hatch.cli.cli_utils import (
        request_confirmation,
        parse_host_list,
        ResultReporter,
        ConsequenceType,
    )
    
    from_env = getattr(args, "from_env", None)
    from_host = getattr(args, "from_host", None)
    to_hosts = getattr(args, "to_host", None)
    servers = getattr(args, "servers", None)
    pattern = getattr(args, "pattern", None)
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)
    no_backup = getattr(args, "no_backup", False)
    
    try:
        # Parse target hosts
        if not to_hosts:
            print("Error: Must specify --to-host")
            return EXIT_ERROR

        target_hosts = parse_host_list(to_hosts)

        # Parse server filters
        server_list = None
        if servers:
            server_list = [s.strip() for s in servers.split(",") if s.strip()]

        # Create ResultReporter for unified output
        reporter = ResultReporter("hatch mcp sync", dry_run=dry_run)
        
        # Build source description
        source_desc = f"environment '{from_env}'" if from_env else f"host '{from_host}'"
        
        # Add sync consequences for preview
        for target_host in target_hosts:
            reporter.add(ConsequenceType.SYNC, f"{source_desc} → '{target_host}'")

        if dry_run:
            reporter.report_result()
            if server_list:
                print(f"  Server filter: {', '.join(server_list)}")
            elif pattern:
                print(f"  Pattern filter: {pattern}")
            return EXIT_SUCCESS

        # Show prompt for confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform synchronization
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.sync_configurations(
            from_env=from_env,
            from_host=from_host,
            to_hosts=target_hosts,
            servers=server_list,
            pattern=pattern,
            no_backup=no_backup,
        )

        if result.success:
            # Create new reporter for results with actual sync details
            result_reporter = ResultReporter("hatch mcp sync", dry_run=False)
            for res in result.results:
                if res.success:
                    result_reporter.add(ConsequenceType.SYNC, f"→ {res.hostname}")
                else:
                    result_reporter.add(ConsequenceType.SKIP, f"→ {res.hostname}: {res.error_message}")
            
            result_reporter.report_result()
            print(f"  Servers synced: {result.servers_synced}")
            print(f"  Hosts updated: {result.hosts_updated}")

            return EXIT_SUCCESS
        else:
            print(f"[ERROR] Synchronization failed")
            for res in result.results:
                if not res.success:
                    print(f"  ✗ {res.hostname}: {res.error_message}")
            return EXIT_ERROR

    except ValueError as e:
        print(f"Error: {e}")
        return EXIT_ERROR
    except Exception as e:
        print(f"Error during synchronization: {e}")
        return EXIT_ERROR
