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


def handle_mcp_list_hosts(args: Namespace) -> int:
    """Handle 'hatch mcp list hosts' command - shows configured hosts in environment.
    
    Args:
        args: Parsed command-line arguments containing:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional environment name (uses current if not specified)
            - detailed: Whether to show detailed host information
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    try:
        from collections import defaultdict

        env_manager: HatchEnvironmentManager = args.env_manager
        env_name: Optional[str] = getattr(args, 'env', None)
        detailed: bool = getattr(args, 'detailed', False)

        # Resolve environment name
        target_env = env_name or env_manager.get_current_environment()

        # Validate environment exists
        if not env_manager.environment_exists(target_env):
            available_envs = env_manager.list_environments()
            print(f"Error: Environment '{target_env}' does not exist.")
            if available_envs:
                print(f"Available environments: {', '.join(available_envs)}")
            return EXIT_ERROR

        # Collect hosts from configured_hosts across all packages in environment
        hosts = defaultdict(int)
        host_details = defaultdict(list)

        try:
            env_data = env_manager.get_environment_data(target_env)
            packages = env_data.get("packages", [])

            for package in packages:
                package_name = package.get("name", "unknown")
                configured_hosts = package.get("configured_hosts", {})

                for host_name, host_config in configured_hosts.items():
                    hosts[host_name] += 1
                    if detailed:
                        config_path = host_config.get("config_path", "N/A")
                        configured_at = host_config.get("configured_at", "N/A")
                        host_details[host_name].append(
                            {
                                "package": package_name,
                                "config_path": config_path,
                                "configured_at": configured_at,
                            }
                        )

        except Exception as e:
            print(f"Error reading environment data: {e}")
            return EXIT_ERROR

        # Display results
        if not hosts:
            print(f"No configured hosts for environment '{target_env}'")
            return EXIT_SUCCESS

        print(f"Configured hosts for environment '{target_env}':")

        for host_name, package_count in sorted(hosts.items()):
            if detailed:
                print(f"\n{host_name} ({package_count} packages):")
                for detail in host_details[host_name]:
                    print(f"  - Package: {detail['package']}")
                    print(f"    Config path: {detail['config_path']}")
                    print(f"    Configured at: {detail['configured_at']}")
            else:
                print(f"  - {host_name} ({package_count} packages)")

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error listing hosts: {e}")
        return EXIT_ERROR


def handle_mcp_list_servers(args: Namespace) -> int:
    """Handle 'hatch mcp list servers' command.
    
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
            # Check if package has host configuration tracking (indicating MCP server)
            configured_hosts = package.get("configured_hosts", {})
            if configured_hosts:
                # Use the tracked server configuration from any host
                first_host = next(iter(configured_hosts.values()))
                server_config_data = first_host.get("server_config", {})

                # Create a simple server config object
                class SimpleServerConfig:
                    def __init__(self, data):
                        self.name = data.get("name", package["name"])
                        self.command = data.get("command", "unknown")
                        self.args = data.get("args", [])

                server_config = SimpleServerConfig(server_config_data)
                mcp_packages.append(
                    {"package": package, "server_config": server_config}
                )
            else:
                # Try the original method as fallback
                try:
                    server_config = get_package_mcp_server_config(
                        env_manager, env_name, package["name"]
                    )
                    mcp_packages.append(
                        {"package": package, "server_config": server_config}
                    )
                except:
                    # Package doesn't have MCP server or method failed
                    continue

        if not mcp_packages:
            print(f"No MCP servers configured in environment '{env_name}'")
            return EXIT_SUCCESS

        print(f"MCP servers in environment '{env_name}':")
        print(f"{'Server Name':<20} {'Package':<20} {'Version':<10} {'Command'}")
        print("-" * 80)

        for item in mcp_packages:
            package = item["package"]
            server_config = item["server_config"]

            server_name = server_config.name
            package_name = package["name"]
            version = package.get("version", "unknown")
            command = f"{server_config.command} {' '.join(server_config.args)}"

            print(f"{server_name:<20} {package_name:<20} {version:<10} {command}")

            # Display host configuration tracking information
            configured_hosts = package.get("configured_hosts", {})
            if configured_hosts:
                print(f"{'':>20} Configured on hosts:")
                for hostname, host_config in configured_hosts.items():
                    config_path = host_config.get("config_path", "unknown")
                    last_synced = host_config.get("last_synced", "unknown")
                    # Format the timestamp for better readability
                    if last_synced != "unknown":
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(
                                last_synced.replace("Z", "+00:00")
                            )
                            last_synced = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            pass  # Keep original format if parsing fails
                    print(
                        f"{'':>22} - {hostname}: {config_path} (synced: {last_synced})"
                    )
            else:
                print(f"{'':>20} No host configurations tracked")
            print()  # Add blank line between servers

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error listing servers: {e}")
        return EXIT_ERROR
