"""MCP host configuration handlers for Hatch CLI.

This module provides handlers for MCP (Model Context Protocol) host configuration
commands including:
- Discovery: detect available hosts and servers
- Listing: show configured hosts and servers
- Backup: manage configuration backups
- Configuration: add/update/remove MCP servers
- Synchronization: sync configurations across hosts

All handlers follow the standardized signature: (args: Namespace) -> int
where args contains the parsed command-line arguments and the return value
is the exit code (0 for success, non-zero for errors).
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
)


def handle_mcp_discover_hosts(args: Namespace) -> int:
    """Handle 'hatch mcp discover hosts' command.
    
    Detects and displays available MCP host platforms on the system.
    
    Args:
        args: Parsed command-line arguments (currently unused but required
              for standardized handler signature)
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    try:
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies

        available_hosts = MCPHostRegistry.detect_available_hosts()
        print("Available MCP host platforms:")

        for host_type in MCPHostType:
            try:
                strategy = MCPHostRegistry.get_strategy(host_type)
                config_path = strategy.get_config_path()
                is_available = host_type in available_hosts

                status = "✓ Available" if is_available else "✗ Not detected"
                print(f"  {host_type.value}: {status}")
                if config_path:
                    print(f"    Config path: {config_path}")
            except Exception as e:
                print(f"  {host_type.value}: Error - {e}")

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error discovering hosts: {e}")
        return EXIT_ERROR


def handle_mcp_discover_servers(args: Namespace) -> int:
    """Handle 'hatch mcp discover servers' command.
    
    Discovers MCP servers available in packages within an environment.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional environment name (uses current if not specified)
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
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
