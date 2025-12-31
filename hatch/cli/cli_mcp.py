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
    from hatch.cli.cli_utils import request_confirmation
    
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

        if dry_run:
            print(f"[DRY RUN] Would restore backup for host '{host}':")
            print(f"[DRY RUN] Backup file: {backup_file}")
            print(f"[DRY RUN] Backup path: {backup_path}")
            return EXIT_SUCCESS

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Restore backup '{backup_file}' for host '{host}'? This will overwrite current configuration.",
            auto_approve,
        ):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform restoration
        success = backup_manager.restore_backup(host, backup_file)

        if success:
            print(
                f"[SUCCESS] Successfully restored backup '{backup_file}' for host '{host}'"
            )

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
                        f"Synchronized {updates_count} package entries with restored configuration"
                    )

            except Exception as e:
                print(f"Warning: Could not synchronize environment tracking: {e}")

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
    
    Returns:
        int: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure
    """
    try:
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        host: str = args.host
        detailed: bool = getattr(args, 'detailed', False)

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

        if not backups:
            print(f"No backups found for host '{host}'")
            return EXIT_SUCCESS

        print(f"Backups for host '{host}' ({len(backups)} found):")

        if detailed:
            print(f"{'Backup File':<40} {'Created':<20} {'Size':<10} {'Age (days)'}")
            print("-" * 80)

            for backup in backups:
                created = backup.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                size = f"{backup.file_size:,} B"
                age = backup.age_days

                print(f"{backup.file_path.name:<40} {created:<20} {size:<10} {age}")
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
    from hatch.cli.cli_utils import request_confirmation
    
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

        if dry_run:
            print(
                f"[DRY RUN] Would clean {len(unique_to_clean)} backup(s) for host '{host}':"
            )
            for backup in unique_to_clean:
                print(
                    f"[DRY RUN]   {backup.file_path.name} (age: {backup.age_days} days)"
                )
            return EXIT_SUCCESS

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Clean {len(unique_to_clean)} backup(s) for host '{host}'?", auto_approve
        ):
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
            print(f"✓ Successfully cleaned {cleaned_count} backup(s) for host '{host}'")
            return EXIT_SUCCESS
        else:
            print(f"No backups were cleaned for host '{host}'")
            return EXIT_SUCCESS

    except Exception as e:
        print(f"Error cleaning backups: {e}")
        return EXIT_ERROR
