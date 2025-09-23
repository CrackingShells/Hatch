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
import sys
from pathlib import Path
from typing import Optional, List

from hatch.environment_manager import HatchEnvironmentManager
from hatch_validator import HatchPackageValidator
from hatch.template_generator import create_package_template
from hatch.mcp_host_config import MCPHostConfigurationManager, MCPHostType, MCPHostRegistry, MCPServerConfig

def parse_host_list(host_arg: str):
    """Parse comma-separated host list or 'all'."""
    if not host_arg:
        return []

    if host_arg.lower() == 'all':
        return MCPHostRegistry.detect_available_hosts()

    hosts = []
    for host_str in host_arg.split(','):
        host_str = host_str.strip()
        try:
            host_type = MCPHostType(host_str)
            hosts.append(host_type)
        except ValueError:
            available = [h.value for h in MCPHostType]
            raise ValueError(f"Unknown host '{host_str}'. Available: {available}")

    return hosts

def request_confirmation(message: str, auto_approve: bool = False) -> bool:
    """Request user confirmation with non-TTY support following Hatch patterns."""
    import os
    import sys

    # Check for auto-approve first
    if auto_approve or os.getenv('HATCH_AUTO_APPROVE', '').lower() in ('1', 'true', 'yes'):
        return True

    # Interactive mode - request user input (works in both TTY and test environments)
    try:
        while True:
            response = input(f"{message} [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    except (EOFError, KeyboardInterrupt):
        # Only auto-approve on EOF/interrupt if not in TTY (non-interactive environment)
        if not sys.stdin.isatty():
            return True
        return False

def get_package_mcp_server_config(env_manager: HatchEnvironmentManager, env_name: str, package_name: str) -> MCPServerConfig:
    """Get MCP server configuration for a package using existing APIs."""
    try:
        # Get package info from environment
        packages = env_manager.list_packages(env_name)
        package_info = next((pkg for pkg in packages if pkg['name'] == package_name), None)

        if not package_info:
            raise ValueError(f"Package '{package_name}' not found in environment '{env_name}'")

        # Load package metadata using existing pattern from environment_manager.py:716-727
        package_path = Path(package_info['source']['path'])
        metadata_path = package_path / "hatch_metadata.json"

        if not metadata_path.exists():
            raise ValueError(f"Package '{package_name}' is not a Hatch package (no hatch_metadata.json)")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Use PackageService for schema-aware access
        from hatch_validator.package.package_service import PackageService
        package_service = PackageService(metadata)

        # Get the HatchMCP entry point (this handles both v1.2.0 and v1.2.1 schemas)
        hatch_mcp_entry_point = package_service.get_hatch_mcp_entry_point()
        if not hatch_mcp_entry_point:
            raise ValueError(f"Package '{package_name}' does not have a HatchMCP entry point")

        # Get environment-specific Python executable
        python_executable = env_manager.get_current_python_executable()
        if not python_executable:
            # Fallback to system Python if no environment-specific Python available
            python_executable = "python"

        # Create server configuration
        server_path = str(package_path / hatch_mcp_entry_point)
        server_config = MCPServerConfig(
            name=package_name,
            command=python_executable,
            args=[server_path],
            env={}
        )

        return server_config

    except Exception as e:
        raise ValueError(f"Failed to get MCP server config for package '{package_name}': {e}")

def handle_mcp_discover_hosts():
    """Handle 'hatch mcp discover hosts' command."""
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

        return 0
    except Exception as e:
        print(f"Error discovering hosts: {e}")
        return 1

def handle_mcp_discover_servers(env_manager: HatchEnvironmentManager, env_name: Optional[str] = None):
    """Handle 'hatch mcp discover servers' command."""
    try:
        env_name = env_name or env_manager.get_current_environment()

        if not env_manager.environment_exists(env_name):
            print(f"Error: Environment '{env_name}' does not exist")
            return 1

        packages = env_manager.list_packages(env_name)
        mcp_packages = []

        for package in packages:
            try:
                # Check if package has MCP server entry point
                server_config = get_package_mcp_server_config(env_manager, env_name, package['name'])
                mcp_packages.append({
                    'package': package,
                    'server_config': server_config
                })
            except ValueError:
                # Package doesn't have MCP server
                continue

        if not mcp_packages:
            print(f"No MCP servers found in environment '{env_name}'")
            return 0

        print(f"MCP servers in environment '{env_name}':")
        for item in mcp_packages:
            package = item['package']
            server_config = item['server_config']
            print(f"  {server_config.name}:")
            print(f"    Package: {package['name']} v{package.get('version', 'unknown')}")
            print(f"    Command: {server_config.command}")
            print(f"    Args: {server_config.args}")
            if server_config.env:
                print(f"    Environment: {server_config.env}")

        return 0
    except Exception as e:
        print(f"Error discovering servers: {e}")
        return 1

def handle_mcp_list_hosts():
    """Handle 'hatch mcp list hosts' command."""
    try:
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies

        available_hosts = MCPHostRegistry.detect_available_hosts()
        all_hosts = list(MCPHostType)

        print("MCP host platforms status:")
        print(f"{'Host Platform':<20} {'Status':<15} {'Config Path'}")
        print("-" * 70)

        for host_type in all_hosts:
            try:
                strategy = MCPHostRegistry.get_strategy(host_type)
                config_path = strategy.get_config_path()
                is_available = host_type in available_hosts

                status = "Available" if is_available else "Not detected"
                config_display = str(config_path) if config_path else "N/A"

                print(f"{host_type.value:<20} {status:<15} {config_display}")
            except Exception as e:
                print(f"{host_type.value:<20} {'Error':<15} {str(e)}")

        return 0
    except Exception as e:
        print(f"Error listing hosts: {e}")
        return 1

def handle_mcp_list_servers(env_manager: HatchEnvironmentManager, env_name: Optional[str] = None):
    """Handle 'hatch mcp list servers' command."""
    try:
        env_name = env_name or env_manager.get_current_environment()

        if not env_manager.environment_exists(env_name):
            print(f"Error: Environment '{env_name}' does not exist")
            return 1

        packages = env_manager.list_packages(env_name)
        mcp_packages = []

        for package in packages:
            # Check if package has host configuration tracking (indicating MCP server)
            configured_hosts = package.get('configured_hosts', {})
            if configured_hosts:
                # Use the tracked server configuration from any host
                first_host = next(iter(configured_hosts.values()))
                server_config_data = first_host.get('server_config', {})

                # Create a simple server config object
                class SimpleServerConfig:
                    def __init__(self, data):
                        self.name = data.get('name', package['name'])
                        self.command = data.get('command', 'unknown')
                        self.args = data.get('args', [])

                server_config = SimpleServerConfig(server_config_data)
                mcp_packages.append({
                    'package': package,
                    'server_config': server_config
                })
            else:
                # Try the original method as fallback
                try:
                    server_config = get_package_mcp_server_config(env_manager, env_name, package['name'])
                    mcp_packages.append({
                        'package': package,
                        'server_config': server_config
                    })
                except:
                    # Package doesn't have MCP server or method failed
                    continue

        if not mcp_packages:
            print(f"No MCP servers configured in environment '{env_name}'")
            return 0

        print(f"MCP servers in environment '{env_name}':")
        print(f"{'Server Name':<20} {'Package':<20} {'Version':<10} {'Command'}")
        print("-" * 80)

        for item in mcp_packages:
            package = item['package']
            server_config = item['server_config']

            server_name = server_config.name
            package_name = package['name']
            version = package.get('version', 'unknown')
            command = f"{server_config.command} {' '.join(server_config.args)}"

            print(f"{server_name:<20} {package_name:<20} {version:<10} {command}")

            # Display host configuration tracking information
            configured_hosts = package.get('configured_hosts', {})
            if configured_hosts:
                print(f"{'':>20} Configured on hosts:")
                for hostname, host_config in configured_hosts.items():
                    config_path = host_config.get('config_path', 'unknown')
                    last_synced = host_config.get('last_synced', 'unknown')
                    # Format the timestamp for better readability
                    if last_synced != 'unknown':
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_synced.replace('Z', '+00:00'))
                            last_synced = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            pass  # Keep original format if parsing fails
                    print(f"{'':>22} - {hostname}: {config_path} (synced: {last_synced})")
            else:
                print(f"{'':>20} No host configurations tracked")
            print()  # Add blank line between servers

        return 0
    except Exception as e:
        print(f"Error listing servers: {e}")
        return 1

def handle_mcp_backup_restore(host: str, backup_file: Optional[str] = None, dry_run: bool = False, auto_approve: bool = False):
    """Handle 'hatch mcp backup restore' command."""
    try:
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}")
            return 1

        backup_manager = MCPHostConfigBackupManager()

        # Get backup file path
        if backup_file:
            backup_path = backup_manager.backup_root / host / backup_file
            if not backup_path.exists():
                print(f"Error: Backup file '{backup_file}' not found for host '{host}'")
                return 1
        else:
            backup_path = backup_manager._get_latest_backup(host)
            if not backup_path:
                print(f"Error: No backups found for host '{host}'")
                return 1
            backup_file = backup_path.name

        if dry_run:
            print(f"[DRY RUN] Would restore backup for host '{host}':")
            print(f"[DRY RUN] Backup file: {backup_file}")
            print(f"[DRY RUN] Backup path: {backup_path}")
            return 0

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Restore backup '{backup_file}' for host '{host}'? This will overwrite current configuration.",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform restoration
        success = backup_manager.restore_backup(host, backup_file)

        if success:
            print(f"[SUCCESS] Successfully restored backup '{backup_file}' for host '{host}'")
            return 0
        else:
            print(f"[ERROR] Failed to restore backup '{backup_file}' for host '{host}'")
            return 1

    except Exception as e:
        print(f"Error restoring backup: {e}")
        return 1

def handle_mcp_backup_list(host: str, detailed: bool = False):
    """Handle 'hatch mcp backup list' command."""
    try:
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}")
            return 1

        backup_manager = MCPHostConfigBackupManager()
        backups = backup_manager.list_backups(host)

        if not backups:
            print(f"No backups found for host '{host}'")
            return 0

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
                print(f"  {backup.file_path.name} (created: {created}, {backup.age_days} days ago)")

        return 0
    except Exception as e:
        print(f"Error listing backups: {e}")
        return 1

def handle_mcp_backup_clean(host: str, older_than_days: Optional[int] = None, keep_count: Optional[int] = None,
                           dry_run: bool = False, auto_approve: bool = False):
    """Handle 'hatch mcp backup clean' command."""
    try:
        from hatch.mcp_host_config.backup import MCPHostConfigBackupManager

        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}")
            return 1

        # Validate cleanup criteria
        if not older_than_days and not keep_count:
            print("Error: Must specify either --older-than-days or --keep-count")
            return 1

        backup_manager = MCPHostConfigBackupManager()
        backups = backup_manager.list_backups(host)

        if not backups:
            print(f"No backups found for host '{host}'")
            return 0

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
            return 0

        if dry_run:
            print(f"[DRY RUN] Would clean {len(unique_to_clean)} backup(s) for host '{host}':")
            for backup in unique_to_clean:
                print(f"[DRY RUN]   {backup.file_path.name} (age: {backup.age_days} days)")
            return 0

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Clean {len(unique_to_clean)} backup(s) for host '{host}'?",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform cleanup
        filters = {}
        if older_than_days:
            filters['older_than_days'] = older_than_days
        if keep_count:
            filters['keep_count'] = keep_count

        cleaned_count = backup_manager.clean_backups(host, **filters)

        if cleaned_count > 0:
            print(f"✓ Successfully cleaned {cleaned_count} backup(s) for host '{host}'")
            return 0
        else:
            print(f"No backups were cleaned for host '{host}'")
            return 0

    except Exception as e:
        print(f"Error cleaning backups: {e}")
        return 1

def parse_env_vars(env_list: Optional[list]) -> dict:
    """Parse environment variables from command line format."""
    if not env_list:
        return {}

    env_dict = {}
    for env_var in env_list:
        if '=' not in env_var:
            print(f"Warning: Invalid environment variable format '{env_var}'. Expected KEY=VALUE")
            continue
        key, value = env_var.split('=', 1)
        env_dict[key.strip()] = value.strip()

    return env_dict

def parse_headers(headers_list: Optional[list]) -> dict:
    """Parse HTTP headers from command line format."""
    if not headers_list:
        return {}

    headers_dict = {}
    for header in headers_list:
        if '=' not in header:
            print(f"Warning: Invalid header format '{header}'. Expected KEY=VALUE")
            continue
        key, value = header.split('=', 1)
        headers_dict[key.strip()] = value.strip()

    return headers_dict

def handle_mcp_configure(host: str, server_name: str, command: str, args: list,
                        env: Optional[list] = None, url: Optional[str] = None,
                        headers: Optional[list] = None, no_backup: bool = False,
                        dry_run: bool = False, auto_approve: bool = False):
    """Handle 'hatch mcp configure' command."""
    try:
        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}")
            return 1

        # Parse environment variables and headers
        env_dict = parse_env_vars(env)
        headers_dict = parse_headers(headers)

        # Create server configuration (only include headers if URL is provided)
        config_data = {
            'name': server_name,
            'command': command,
            'args': args or [],
            'env': env_dict,
            'url': url
        }

        # Only add headers if URL is provided (per MCPServerConfig validation)
        if url and headers_dict:
            config_data['headers'] = headers_dict

        server_config = MCPServerConfig(**config_data)

        if dry_run:
            print(f"[DRY RUN] Would configure MCP server '{server_name}' on host '{host}':")
            print(f"[DRY RUN] Command: {command}")
            if args:
                print(f"[DRY RUN] Args: {args}")
            if env_dict:
                print(f"[DRY RUN] Environment: {env_dict}")
            if url:
                print(f"[DRY RUN] URL: {url}")
            if headers_dict:
                print(f"[DRY RUN] Headers: {headers_dict}")
            print(f"[DRY RUN] Backup: {'Disabled' if no_backup else 'Enabled'}")
            return 0

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Configure MCP server '{server_name}' on host '{host}'?",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform configuration
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.configure_server(
            server_config=server_config,
            hostname=host,
            no_backup=no_backup
        )

        if result.success:
            print(f"[SUCCESS] Successfully configured MCP server '{server_name}' on host '{host}'")
            if result.backup_path:
                print(f"  Backup created: {result.backup_path}")
            return 0
        else:
            print(f"[ERROR] Failed to configure MCP server '{server_name}' on host '{host}': {result.error_message}")
            return 1

    except Exception as e:
        print(f"Error configuring MCP server: {e}")
        return 1

def handle_mcp_remove(host: str, server_name: str, no_backup: bool = False,
                     dry_run: bool = False, auto_approve: bool = False):
    """Handle 'hatch mcp remove' command."""
    try:
        # Validate host type
        try:
            host_type = MCPHostType(host)
        except ValueError:
            print(f"Error: Invalid host '{host}'. Supported hosts: {[h.value for h in MCPHostType]}")
            return 1

        if dry_run:
            print(f"[DRY RUN] Would remove MCP server '{server_name}' from host '{host}'")
            print(f"[DRY RUN] Backup: {'Disabled' if no_backup else 'Enabled'}")
            return 0

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Remove MCP server '{server_name}' from host '{host}'?",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform removal
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.remove_server(
            server_name=server_name,
            hostname=host,
            no_backup=no_backup
        )

        if result.success:
            print(f"[SUCCESS] Successfully removed MCP server '{server_name}' from host '{host}'")
            if result.backup_path:
                print(f"  Backup created: {result.backup_path}")
            return 0
        else:
            print(f"[ERROR] Failed to remove MCP server '{server_name}' from host '{host}': {result.error_message}")
            return 1

    except Exception as e:
        print(f"Error removing MCP server: {e}")
        return 1

def parse_host_list(host_arg: str) -> List[str]:
    """Parse comma-separated host list or 'all'."""
    if not host_arg:
        return []

    if host_arg.lower() == 'all':
        from hatch.mcp_host_config.host_management import MCPHostRegistry
        available_hosts = MCPHostRegistry.detect_available_hosts()
        return [host.value for host in available_hosts]

    hosts = []
    for host_str in host_arg.split(','):
        host_str = host_str.strip()
        try:
            host_type = MCPHostType(host_str)
            hosts.append(host_type.value)
        except ValueError:
            available = [h.value for h in MCPHostType]
            raise ValueError(f"Unknown host '{host_str}'. Available: {available}")

    return hosts

def handle_mcp_remove_server(server_name: str, hosts: Optional[str] = None,
                           env: Optional[str] = None, no_backup: bool = False,
                           dry_run: bool = False, auto_approve: bool = False):
    """Handle 'hatch mcp remove server' command."""
    try:
        # Determine target hosts
        if hosts:
            target_hosts = parse_host_list(hosts)
        elif env:
            # TODO: Implement environment-based server removal
            print("Error: Environment-based removal not yet implemented")
            return 1
        else:
            print("Error: Must specify either --host or --env")
            return 1

        if not target_hosts:
            print("Error: No valid hosts specified")
            return 1

        if dry_run:
            print(f"[DRY RUN] Would remove MCP server '{server_name}' from hosts: {', '.join(target_hosts)}")
            print(f"[DRY RUN] Backup: {'Disabled' if no_backup else 'Enabled'}")
            return 0

        # Confirm operation unless auto-approved
        hosts_str = ', '.join(target_hosts)
        if not request_confirmation(
            f"Remove MCP server '{server_name}' from hosts: {hosts_str}?",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform removal on each host
        mcp_manager = MCPHostConfigurationManager()
        success_count = 0
        total_count = len(target_hosts)

        for host in target_hosts:
            result = mcp_manager.remove_server(
                server_name=server_name,
                hostname=host,
                no_backup=no_backup
            )

            if result.success:
                print(f"[SUCCESS] Successfully removed '{server_name}' from '{host}'")
                if result.backup_path:
                    print(f"  Backup created: {result.backup_path}")
                success_count += 1
            else:
                print(f"[ERROR] Failed to remove '{server_name}' from '{host}': {result.error_message}")

        # Summary
        if success_count == total_count:
            print(f"[SUCCESS] Removed '{server_name}' from all {total_count} hosts")
            return 0
        elif success_count > 0:
            print(f"[PARTIAL SUCCESS] Removed '{server_name}' from {success_count}/{total_count} hosts")
            return 1
        else:
            print(f"[ERROR] Failed to remove '{server_name}' from any hosts")
            return 1

    except Exception as e:
        print(f"Error removing MCP server: {e}")
        return 1

def handle_mcp_remove_host(host_name: str, no_backup: bool = False,
                          dry_run: bool = False, auto_approve: bool = False):
    """Handle 'hatch mcp remove host' command."""
    try:
        # Validate host type
        try:
            host_type = MCPHostType(host_name)
        except ValueError:
            print(f"Error: Invalid host '{host_name}'. Supported hosts: {[h.value for h in MCPHostType]}")
            return 1

        if dry_run:
            print(f"[DRY RUN] Would remove entire host configuration for '{host_name}'")
            print(f"[DRY RUN] Backup: {'Disabled' if no_backup else 'Enabled'}")
            return 0

        # Confirm operation unless auto-approved
        if not request_confirmation(
            f"Remove entire host configuration for '{host_name}'? This will remove ALL MCP servers from this host.",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform host configuration removal
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.remove_host_configuration(
            hostname=host_name,
            no_backup=no_backup
        )

        if result.success:
            print(f"[SUCCESS] Successfully removed host configuration for '{host_name}'")
            if result.backup_path:
                print(f"  Backup created: {result.backup_path}")
            return 0
        else:
            print(f"[ERROR] Failed to remove host configuration for '{host_name}': {result.error_message}")
            return 1

    except Exception as e:
        print(f"Error removing host configuration: {e}")
        return 1

def handle_mcp_sync(from_env: Optional[str] = None,
                   from_host: Optional[str] = None,
                   to_hosts: Optional[str] = None,
                   servers: Optional[str] = None,
                   pattern: Optional[str] = None,
                   dry_run: bool = False,
                   auto_approve: bool = False,
                   no_backup: bool = False) -> int:
    """Handle 'hatch mcp sync' command."""
    try:
        # Parse target hosts
        if not to_hosts:
            print("Error: Must specify --to-host")
            return 1

        target_hosts = parse_host_list(to_hosts)

        # Parse server filters
        server_list = None
        if servers:
            server_list = [s.strip() for s in servers.split(',') if s.strip()]

        if dry_run:
            source_desc = f"environment '{from_env}'" if from_env else f"host '{from_host}'"
            target_desc = f"hosts: {', '.join(target_hosts)}"
            print(f"[DRY RUN] Would synchronize from {source_desc} to {target_desc}")

            if server_list:
                print(f"[DRY RUN] Server filter: {', '.join(server_list)}")
            elif pattern:
                print(f"[DRY RUN] Pattern filter: {pattern}")

            print(f"[DRY RUN] Backup: {'Disabled' if no_backup else 'Enabled'}")
            return 0

        # Confirm operation unless auto-approved
        source_desc = f"environment '{from_env}'" if from_env else f"host '{from_host}'"
        target_desc = f"{len(target_hosts)} host(s)"
        if not request_confirmation(
            f"Synchronize MCP configurations from {source_desc} to {target_desc}?",
            auto_approve
        ):
            print("Operation cancelled.")
            return 0

        # Perform synchronization
        mcp_manager = MCPHostConfigurationManager()
        result = mcp_manager.sync_configurations(
            from_env=from_env,
            from_host=from_host,
            to_hosts=target_hosts,
            servers=server_list,
            pattern=pattern,
            no_backup=no_backup
        )

        if result.success:
            print(f"[SUCCESS] Synchronization completed")
            print(f"  Servers synced: {result.servers_synced}")
            print(f"  Hosts updated: {result.hosts_updated}")

            # Show detailed results
            for res in result.results:
                if res.success:
                    backup_info = f" (backup: {res.backup_path})" if res.backup_path else ""
                    print(f"  ✓ {res.hostname}{backup_info}")
                else:
                    print(f"  ✗ {res.hostname}: {res.error_message}")

            return 0
        else:
            print(f"[ERROR] Synchronization failed")
            for res in result.results:
                if not res.success:
                    print(f"  ✗ {res.hostname}: {res.error_message}")
            return 1

    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error during synchronization: {e}")
        return 1

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
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create argument parser
    parser = argparse.ArgumentParser(description="Hatch package manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create template command
    create_parser = subparsers.add_parser("create", help="Create a new package template")
    create_parser.add_argument("name", help="Package name")
    create_parser.add_argument("--dir", "-d", default=".", help="Target directory (default: current directory)")
    create_parser.add_argument("--description", "-D", default="", help="Package description")
    
    # Validate package command
    validate_parser = subparsers.add_parser("validate", help="Validate a package")
    validate_parser.add_argument("package_dir", help="Path to package directory")
    
    # Environment management commands
    env_subparsers = subparsers.add_parser("env", help="Environment management commands").add_subparsers(
        dest="env_command", help="Environment command to execute"
    )
    
    # Create environment command
    env_create_parser = env_subparsers.add_parser("create", help="Create a new environment")
    env_create_parser.add_argument("name", help="Environment name")
    env_create_parser.add_argument("--description", "-D", default="", help="Environment description")
    env_create_parser.add_argument("--python-version", help="Python version for the environment (e.g., 3.11, 3.12)")
    env_create_parser.add_argument("--no-python", action="store_true", 
                                   help="Don't create a Python environment using conda/mamba")
    env_create_parser.add_argument("--no-hatch-mcp-server", action="store_true",
                                   help="Don't install hatch_mcp_server wrapper in the new environment")
    env_create_parser.add_argument("--hatch_mcp_server_tag", 
                                   help="Git tag/branch reference for hatch_mcp_server wrapper installation (e.g., 'dev', 'v0.1.0')")
    
    # Remove environment command
    env_remove_parser = env_subparsers.add_parser("remove", help="Remove an environment")
    env_remove_parser.add_argument("name", help="Environment name")
    
    # List environments command
    env_subparsers.add_parser("list", help="List all available environments")
    
    # Set current environment command
    env_use_parser = env_subparsers.add_parser("use", help="Set the current environment")
    env_use_parser.add_argument("name", help="Environment name")
    
    # Show current environment command
    env_subparsers.add_parser("current", help="Show the current environment")

    # Python environment management commands - advanced subcommands
    env_python_subparsers = env_subparsers.add_parser("python", help="Manage Python environments").add_subparsers(
        dest="python_command", help="Python environment command to execute"
    )
    
    # Initialize Python environment
    python_init_parser = env_python_subparsers.add_parser("init", help="Initialize Python environment")
    python_init_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_init_parser.add_argument("--python-version", help="Python version (e.g., 3.11, 3.12)")
    python_init_parser.add_argument("--force", action="store_true", help="Force recreation if exists")
    python_init_parser.add_argument("--no-hatch-mcp-server", action="store_true",
                                   help="Don't install hatch_mcp_server wrapper in the Python environment")
    python_init_parser.add_argument("--hatch_mcp_server_tag", 
                                   help="Git tag/branch reference for hatch_mcp_server wrapper installation (e.g., 'dev', 'v0.1.0')")
    
    # Show Python environment info
    python_info_parser = env_python_subparsers.add_parser("info", help="Show Python environment information")
    python_info_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_info_parser.add_argument("--detailed", action="store_true", help="Show detailed diagnostics")
    
    # Hatch MCP server wrapper management commands
    hatch_mcp_parser = env_python_subparsers.add_parser("add-hatch-mcp", help="Add hatch_mcp_server wrapper to the environment")
    ## Install MCP server command
    hatch_mcp_parser.add_argument("--hatch_env", default=None, help="Hatch environment name. It must possess a valid Python environment. (default: current environment)")
    hatch_mcp_parser.add_argument("--tag", default=None, help="Git tag/branch reference for wrapper installation (e.g., 'dev', 'v0.1.0')")
    
    # Remove Python environment
    python_remove_parser = env_python_subparsers.add_parser("remove", help="Remove Python environment")
    python_remove_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_remove_parser.add_argument("--force", action="store_true", help="Force removal without confirmation")
    
    # Launch Python shell
    python_shell_parser = env_python_subparsers.add_parser("shell", help="Launch Python shell in environment")
    python_shell_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_shell_parser.add_argument("--cmd", help="Command to run in the shell (optional)")
    
    # MCP host configuration commands
    mcp_subparsers = subparsers.add_parser("mcp", help="MCP host configuration commands").add_subparsers(
        dest="mcp_command", help="MCP command to execute"
    )

    # MCP discovery commands
    mcp_discover_subparsers = mcp_subparsers.add_parser("discover", help="Discover MCP hosts and servers").add_subparsers(
        dest="discover_command", help="Discovery command to execute"
    )

    # Discover hosts command
    mcp_discover_hosts_parser = mcp_discover_subparsers.add_parser("hosts", help="Discover available MCP host platforms")

    # Discover servers command
    mcp_discover_servers_parser = mcp_discover_subparsers.add_parser("servers", help="Discover configured MCP servers")
    mcp_discover_servers_parser.add_argument("--env", "-e", default=None, help="Environment name (default: current environment)")

    # MCP list commands
    mcp_list_subparsers = mcp_subparsers.add_parser("list", help="List MCP hosts and servers").add_subparsers(
        dest="list_command", help="List command to execute"
    )

    # List hosts command
    mcp_list_hosts_parser = mcp_list_subparsers.add_parser("hosts", help="List detected MCP host platforms with status")

    # List servers command
    mcp_list_servers_parser = mcp_list_subparsers.add_parser("servers", help="List configured MCP servers from environment")
    mcp_list_servers_parser.add_argument("--env", "-e", default=None, help="Environment name (default: current environment)")

    # MCP backup commands
    mcp_backup_subparsers = mcp_subparsers.add_parser("backup", help="Backup management commands").add_subparsers(
        dest="backup_command", help="Backup command to execute"
    )

    # Restore backup command
    mcp_backup_restore_parser = mcp_backup_subparsers.add_parser("restore", help="Restore MCP host configuration from backup")
    mcp_backup_restore_parser.add_argument("host", help="Host platform to restore (e.g., claude-desktop, cursor)")
    mcp_backup_restore_parser.add_argument("--backup-file", "-f", default=None, help="Specific backup file to restore (default: latest)")
    mcp_backup_restore_parser.add_argument("--dry-run", action="store_true", help="Preview restore operation without execution")
    mcp_backup_restore_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    # List backups command
    mcp_backup_list_parser = mcp_backup_subparsers.add_parser("list", help="List available backups for MCP host")
    mcp_backup_list_parser.add_argument("host", help="Host platform to list backups for (e.g., claude-desktop, cursor)")
    mcp_backup_list_parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed backup information")

    # Clean backups command
    mcp_backup_clean_parser = mcp_backup_subparsers.add_parser("clean", help="Clean old backups based on criteria")
    mcp_backup_clean_parser.add_argument("host", help="Host platform to clean backups for (e.g., claude-desktop, cursor)")
    mcp_backup_clean_parser.add_argument("--older-than-days", type=int, help="Remove backups older than specified days")
    mcp_backup_clean_parser.add_argument("--keep-count", type=int, help="Keep only the specified number of newest backups")
    mcp_backup_clean_parser.add_argument("--dry-run", action="store_true", help="Preview cleanup operation without execution")
    mcp_backup_clean_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    # MCP direct management commands
    mcp_configure_parser = mcp_subparsers.add_parser("configure", help="Configure MCP server directly on host")
    mcp_configure_parser.add_argument("host", help="Host platform to configure (e.g., claude-desktop, cursor)")
    mcp_configure_parser.add_argument("server_name", help="Name for the MCP server")
    mcp_configure_parser.add_argument("server_command", help="Command to execute the MCP server")
    mcp_configure_parser.add_argument("args", nargs="*", help="Arguments for the MCP server command")
    mcp_configure_parser.add_argument("--env", "-e", action="append", help="Environment variables (format: KEY=VALUE)")
    mcp_configure_parser.add_argument("--url", help="Server URL for remote MCP servers")
    mcp_configure_parser.add_argument("--headers", action="append", help="HTTP headers for remote servers (format: KEY=VALUE)")
    mcp_configure_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation before configuration")
    mcp_configure_parser.add_argument("--dry-run", action="store_true", help="Preview configuration without execution")
    mcp_configure_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    # Remove MCP commands (object-action pattern)
    mcp_remove_subparsers = mcp_subparsers.add_parser("remove", help="Remove MCP servers or host configurations").add_subparsers(
        dest="remove_command", help="Remove command to execute"
    )

    # Remove server command
    mcp_remove_server_parser = mcp_remove_subparsers.add_parser("server", help="Remove MCP server from hosts")
    mcp_remove_server_parser.add_argument("server_name", help="Name of the MCP server to remove")
    mcp_remove_server_parser.add_argument("--host", help="Target hosts (comma-separated or 'all')")
    mcp_remove_server_parser.add_argument("--env", "-e", help="Environment name (for environment-based removal)")
    mcp_remove_server_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation before removal")
    mcp_remove_server_parser.add_argument("--dry-run", action="store_true", help="Preview removal without execution")
    mcp_remove_server_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    # Remove host command
    mcp_remove_host_parser = mcp_remove_subparsers.add_parser("host", help="Remove entire host configuration")
    mcp_remove_host_parser.add_argument("host_name", help="Host platform to remove (e.g., claude-desktop, cursor)")
    mcp_remove_host_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation before removal")
    mcp_remove_host_parser.add_argument("--dry-run", action="store_true", help="Preview removal without execution")
    mcp_remove_host_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")

    # MCP synchronization command
    mcp_sync_parser = mcp_subparsers.add_parser("sync", help="Synchronize MCP configurations between environments and hosts")

    # Source options (mutually exclusive)
    sync_source_group = mcp_sync_parser.add_mutually_exclusive_group(required=True)
    sync_source_group.add_argument("--from-env", help="Source environment name")
    sync_source_group.add_argument("--from-host", help="Source host platform")

    # Target options
    mcp_sync_parser.add_argument("--to-host", required=True, help="Target hosts (comma-separated or 'all')")

    # Filter options (mutually exclusive)
    sync_filter_group = mcp_sync_parser.add_mutually_exclusive_group()
    sync_filter_group.add_argument("--servers", help="Specific server names to sync (comma-separated)")
    sync_filter_group.add_argument("--pattern", help="Regex pattern for server selection")

    # Standard options
    mcp_sync_parser.add_argument("--dry-run", action="store_true", help="Preview synchronization without execution")
    mcp_sync_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")
    mcp_sync_parser.add_argument("--no-backup", action="store_true", help="Skip backup creation before synchronization")

    # Package management commands
    pkg_subparsers = subparsers.add_parser("package", help="Package management commands").add_subparsers(
        dest="pkg_command", help="Package command to execute"
    )
    
    # Add package command
    pkg_add_parser = pkg_subparsers.add_parser("add", help="Add a package to the current environment")
    pkg_add_parser.add_argument("package_path_or_name", help="Path to package directory or name of the package")
    pkg_add_parser.add_argument("--env", "-e", default=None, help="Environment name (default: current environment)")
    pkg_add_parser.add_argument("--version", "-v", default=None, help="Version of the package (optional)")
    pkg_add_parser.add_argument("--force-download", "-f", action="store_true", help="Force download even if package is in cache")
    pkg_add_parser.add_argument("--refresh-registry", "-r", action="store_true", help="Force refresh of registry data")
    pkg_add_parser.add_argument("--auto-approve", action="store_true", help="Automatically approve changes installation of deps for automation scenario")
    # MCP host configuration integration
    pkg_add_parser.add_argument("--host", help="Comma-separated list of MCP host platforms to configure (e.g., claude-desktop,cursor)")
    pkg_add_parser.add_argument("--no-mcp-config", action="store_true", help="Skip automatic MCP host configuration even if package has MCP servers")

    # Remove package command
    pkg_remove_parser = pkg_subparsers.add_parser("remove", help="Remove a package from the current environment")
    pkg_remove_parser.add_argument("package_name", help="Name of the package to remove")
    pkg_remove_parser.add_argument("--env", "-e", default=None, help="Environment name (default: current environment)")
    
    # List packages command
    pkg_list_parser = pkg_subparsers.add_parser("list", help="List packages in an environment")
    pkg_list_parser.add_argument("--env", "-e", help="Environment name (default: current environment)")

    # Sync package MCP servers command
    pkg_sync_parser = pkg_subparsers.add_parser("sync", help="Synchronize package MCP servers to host platforms")
    pkg_sync_parser.add_argument("package_name", help="Name of the package whose MCP servers to sync")
    pkg_sync_parser.add_argument("--host", required=True, help="Comma-separated list of host platforms to sync to (or 'all')")
    pkg_sync_parser.add_argument("--env", "-e", default=None, help="Environment name (default: current environment)")
    pkg_sync_parser.add_argument("--dry-run", action="store_true", help="Preview changes without execution")
    pkg_sync_parser.add_argument("--auto-approve", action="store_true", help="Skip confirmation prompts")
    pkg_sync_parser.add_argument("--no-backup", action="store_true", help="Disable default backup behavior")

    # General arguments for the environment manager
    parser.add_argument("--envs-dir", default=Path.home() / ".hatch" / "envs", help="Directory to store environments")
    parser.add_argument("--cache-ttl", type=int, default=86400, help="Cache TTL in seconds (default: 86400 seconds --> 1 day)")
    parser.add_argument("--cache-dir", default=Path.home() / ".hatch" / "cache", help="Directory to store cached packages")
    
    args = parser.parse_args()

    # Initialize environment manager
    env_manager = HatchEnvironmentManager(
        environments_dir=args.envs_dir,
        cache_ttl=args.cache_ttl,
        cache_dir=args.cache_dir
    )

    # Initialize MCP configuration manager
    mcp_manager = MCPHostConfigurationManager()

    # Execute commands
    if args.command == "create":
        target_dir = Path(args.dir).resolve()
        package_dir = create_package_template(
            target_dir=target_dir,
            package_name=args.name,
            description=args.description
        )
        print(f"Package template created at: {package_dir}")

    elif args.command == "validate":
        package_path = Path(args.package_dir).resolve()

        # Create validator with registry data from environment manager
        validator = HatchPackageValidator(
            version="latest",
            allow_local_dependencies=True,
            registry_data=env_manager.registry_data
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
                    if category != 'valid' and category != 'metadata' and isinstance(result, dict):
                        if not result.get('valid', True) and result.get('errors'):
                            print(f"\n{category.replace('_', ' ').title()} errors:")
                            for error in result['errors']:
                                print(f"  - {error}")

            return 1
        
    elif args.command == "env":
        if args.env_command == "create":
            # Determine whether to create Python environment
            create_python_env = not args.no_python
            python_version = getattr(args, 'python_version', None)
            
            if env_manager.create_environment(args.name, args.description, 
                                            python_version=python_version,
                                            create_python_env=create_python_env,
                                            no_hatch_mcp_server=args.no_hatch_mcp_server,
                                            hatch_mcp_server_tag=args.hatch_mcp_server_tag):
                print(f"Environment created: {args.name}")
                
                # Show Python environment status
                if create_python_env and env_manager.is_python_environment_available():
                    python_exec = env_manager.python_env_manager.get_python_executable(args.name)
                    if python_exec:
                        python_version_info = env_manager.python_env_manager.get_python_version(args.name)
                        print(f"Python environment: {python_exec}")
                        if python_version_info:
                            print(f"Python version: {python_version_info}")
                    else:
                        print("Python environment creation failed")
                elif create_python_env:
                    print("Python environment requested but conda/mamba not available")
                
                return 0
            else:
                print(f"Failed to create environment: {args.name}")
                return 1
                
        elif args.env_command == "remove":
            if env_manager.remove_environment(args.name):
                print(f"Environment removed: {args.name}")
                return 0
            else:
                print(f"Failed to remove environment: {args.name}")
                return 1
                
        elif args.env_command == "list":
            environments = env_manager.list_environments()
            print("Available environments:")
            
            # Check if conda/mamba is available for status info
            conda_available = env_manager.is_python_environment_available()
            
            for env in environments:
                current_marker = "* " if env.get("is_current") else "  "
                description = f" - {env.get('description')}" if env.get("description") else ""
                
                # Show basic environment info
                print(f"{current_marker}{env.get('name')}{description}")
                
                # Show Python environment info if available
                python_env = env.get("python_environment", False)
                if python_env:
                    python_info = env_manager.get_python_environment_info(env.get('name'))
                    if python_info:
                        python_version = python_info.get('python_version', 'Unknown')
                        conda_env = python_info.get('conda_env_name', 'N/A')
                        print(f"    Python: {python_version} (conda: {conda_env})")
                    else:
                        print(f"    Python: Configured but unavailable")
                elif conda_available:
                    print(f"    Python: Not configured")
                else:
                    print(f"    Python: Conda/mamba not available")
                    
            # Show conda/mamba status
            if conda_available:
                manager_info = env_manager.python_env_manager.get_manager_info()
                print(f"\nPython Environment Manager:")
                print(f"  Conda executable: {manager_info.get('conda_executable', 'Not found')}")
                print(f"  Mamba executable: {manager_info.get('mamba_executable', 'Not found')}")
                print(f"  Preferred manager: {manager_info.get('preferred_manager', 'N/A')}")
            else:
                print(f"\nPython Environment Manager: Conda/mamba not available")
                
            return 0
            
        elif args.env_command == "use":
            if env_manager.set_current_environment(args.name):
                print(f"Current environment set to: {args.name}")
                return 0
            else:
                print(f"Failed to set environment: {args.name}")
                return 1
                
        elif args.env_command == "current":
            current_env = env_manager.get_current_environment()
            print(f"Current environment: {current_env}")
            return 0
            
        elif args.env_command == "python":
            # Advanced Python environment management
            if args.python_command == "init":
                python_version = getattr(args, 'python_version', None)
                force = getattr(args, 'force', False)
                no_hatch_mcp_server = getattr(args, 'no_hatch_mcp_server', False)
                hatch_mcp_server_tag = getattr(args, 'hatch_mcp_server_tag', None)
            
                if env_manager.create_python_environment_only(
                    args.hatch_env, 
                    python_version, 
                    force,
                    no_hatch_mcp_server=no_hatch_mcp_server,
                    hatch_mcp_server_tag=hatch_mcp_server_tag
                ):
                    print(f"Python environment initialized for: {args.hatch_env}")
                    
                    # Show Python environment info
                    python_info = env_manager.get_python_environment_info(args.hatch_env)
                    if python_info:
                        print(f"  Python executable: {python_info['python_executable']}")
                        print(f"  Python version: {python_info.get('python_version', 'Unknown')}")
                        print(f"  Conda environment: {python_info.get('conda_env_name', 'N/A')}")
                    
                    return 0
                else:
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    print(f"Failed to initialize Python environment for: {env_name}")
                    return 1
                    
            elif args.python_command == "info":
                detailed = getattr(args, 'detailed', False)
            
                python_info = env_manager.get_python_environment_info(args.hatch_env)
                
                if python_info:
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    print(f"Python environment info for '{env_name}':")
                    print(f"  Status: {'Active' if python_info.get('enabled', False) else 'Inactive'}")
                    print(f"  Python executable: {python_info['python_executable']}")
                    print(f"  Python version: {python_info.get('python_version', 'Unknown')}")
                    print(f"  Conda environment: {python_info.get('conda_env_name', 'N/A')}")
                    print(f"  Environment path: {python_info['environment_path']}")
                    print(f"  Created: {python_info.get('created_at', 'Unknown')}")
                    print(f"  Package count: {python_info.get('package_count', 0)}")
                    print(f"  Packages:")
                    for pkg in python_info.get('packages', []):
                        print(f"    - {pkg['name']} ({pkg['version']})")
                    
                    if detailed:
                        print(f"\nDiagnostics:")
                        diagnostics = env_manager.get_python_environment_diagnostics(args.hatch_env)
                        if diagnostics:
                            for key, value in diagnostics.items():
                                print(f"  {key}: {value}")
                        else:
                            print("  No diagnostics available")
                    
                    return 0
                else:
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    print(f"No Python environment found for: {env_name}")
                    
                    # Show diagnostics for missing environment
                    if detailed:
                        print("\nDiagnostics:")
                        general_diagnostics = env_manager.get_python_manager_diagnostics()
                        for key, value in general_diagnostics.items():
                            print(f"  {key}: {value}")
                    
                    return 1
                    
            elif args.python_command == "remove":
                force = getattr(args, 'force', False)
                
                if not force:
                    # Ask for confirmation using TTY-aware function
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    if not request_confirmation(f"Remove Python environment for '{env_name}'?"):
                        print("Operation cancelled")
                        return 0
                
                if env_manager.remove_python_environment_only(args.hatch_env):
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    print(f"Python environment removed from: {env_name}")
                    return 0
                else:
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    print(f"Failed to remove Python environment from: {env_name}")
                    return 1
                    
            elif args.python_command == "shell":
                cmd = getattr(args, 'cmd', None)
                
                if env_manager.launch_python_shell(args.hatch_env, cmd):
                    return 0
                else:
                    env_name = args.hatch_env or env_manager.get_current_environment()
                    print(f"Failed to launch Python shell for: {env_name}")
                    return 1
            
            elif args.python_command == "add-hatch-mcp":
                env_name = args.hatch_env or env_manager.get_current_environment()
                tag = args.tag
                
                if env_manager.install_mcp_server(env_name, tag):
                    print(f"hatch_mcp_server wrapper installed successfully in environment: {env_name}")
                    return 0
                else:
                    print(f"Failed to install hatch_mcp_server wrapper in environment: {env_name}")
                    return 1
            
            else:
                print("Unknown Python environment command")
                return 1
            
    
    elif args.command == "package":
        if args.pkg_command == "add":
            # Add package to environment
            if env_manager.add_package_to_environment(args.package_path_or_name, args.env, args.version,
                                                      args.force_download, args.refresh_registry, args.auto_approve):
                print(f"Successfully added package: {args.package_path_or_name}")

                # Handle MCP host configuration if requested
                if hasattr(args, 'host') and args.host and not args.no_mcp_config:
                    try:
                        hosts = parse_host_list(args.host)
                        env_name = args.env or env_manager.get_current_environment()

                        # Get the package name from the path/name argument
                        package_name = args.package_path_or_name
                        if '/' in package_name or '\\' in package_name:
                            # Extract package name from path
                            package_name = Path(package_name).name

                        # Get MCP server configuration for the newly added package
                        server_config = get_package_mcp_server_config(env_manager, env_name, package_name)

                        print(f"Configuring MCP server for package '{package_name}' on {len(hosts)} host(s)...")

                        # Configure on each host
                        success_count = 0
                        for host in hosts: # 'host', here, is a string
                            try:
                                result = mcp_manager.configure_server(
                                    hostname=host,
                                    server_config=server_config,
                                    no_backup=False  # Always backup when adding packages
                                )

                                if result.success:
                                    print(f"✓ Configured {server_config.name} on {host}")
                                    success_count += 1
                                else:
                                    print(f"✗ Failed to configure {server_config.name} on {host}: {result.error_message}")

                            except Exception as e:
                                print(f"✗ Error configuring {server_config.name} on {host}: {e}")

                        if success_count > 0:
                            print(f"MCP configuration completed: {success_count}/{len(hosts)} hosts configured")
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
                print(f"{pkg['name']} ({pkg['version']})\tHatch compliant: {pkg['hatch_compliant']}\tsource: {pkg['source']['uri']}\tlocation: {pkg['source']['path']}")
            return 0

        elif args.pkg_command == "sync":
            try:
                # Parse host list
                hosts = parse_host_list(args.host)
                env_name = args.env or env_manager.get_current_environment()

                # Get MCP server configuration for the package
                server_config = get_package_mcp_server_config(env_manager, env_name, args.package_name)

                if args.dry_run:
                    print(f"[DRY RUN] Would synchronize MCP server for package '{args.package_name}' to hosts: {[h for h in hosts]}")
                    print(f"[DRY RUN] Server config: {server_config.name} -> {' '.join(server_config.args)}")
                    return 0

                # Confirm operation unless auto-approved
                if not request_confirmation(
                    f"Synchronize MCP server for package '{args.package_name}' to {len(hosts)} host(s)?",
                    args.auto_approve
                ):
                    print("Operation cancelled.")
                    return 0

                # Perform synchronization to each host
                success_count = 0
                for host in hosts: # 'host', here, is a string
                    try:
                        result = mcp_manager.configure_server(
                            hostname=host,
                            server_config=server_config,
                            no_backup=args.no_backup
                        )

                        if result.success:
                            print(f"[SUCCESS] Successfully configured {server_config.name} on {host}")
                            success_count += 1

                            # Update package metadata with host configuration tracking
                            try:
                                server_config_dict = {
                                    "name": server_config.name,
                                    "command": server_config.command,
                                    "args": server_config.args
                                }

                                env_manager.update_package_host_configuration(
                                    env_name=env_name,
                                    package_name=args.package_name,
                                    hostname=host,
                                    server_config=server_config_dict
                                )
                            except Exception as e:
                                # Log but don't fail the sync operation
                                print(f"[WARNING] Failed to update package metadata: {e}")
                        else:
                            print(f"[ERROR] Failed to configure {server_config.name} on {host}: {result.error_message}")

                    except Exception as e:
                        print(f"[ERROR] Error configuring {server_config.name} on {host}: {e}")

                # Report results
                if success_count == len(hosts):
                    print(f"Successfully synchronized package '{args.package_name}' to all {len(hosts)} host(s)")
                    return 0
                elif success_count > 0:
                    print(f"Partially synchronized package '{args.package_name}': {success_count}/{len(hosts)} hosts succeeded")
                    return 1
                else:
                    print(f"Failed to synchronize package '{args.package_name}' to any hosts")
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
                return handle_mcp_list_hosts()
            elif args.list_command == "servers":
                return handle_mcp_list_servers(env_manager, args.env)
            else:
                print("Unknown list command")
                return 1

        elif args.mcp_command == "backup":
            if args.backup_command == "restore":
                return handle_mcp_backup_restore(
                    args.host, args.backup_file, args.dry_run, args.auto_approve
                )
            elif args.backup_command == "list":
                return handle_mcp_backup_list(args.host, args.detailed)
            elif args.backup_command == "clean":
                return handle_mcp_backup_clean(
                    args.host, args.older_than_days, args.keep_count,
                    args.dry_run, args.auto_approve
                )
            else:
                print("Unknown backup command")
                return 1

        elif args.mcp_command == "configure":
            return handle_mcp_configure(
                args.host, args.server_name, args.server_command, args.args,
                args.env, args.url, args.headers, args.no_backup,
                args.dry_run, args.auto_approve
            )

        elif args.mcp_command == "remove":
            if args.remove_command == "server":
                return handle_mcp_remove_server(
                    args.server_name, args.host, args.env, args.no_backup,
                    args.dry_run, args.auto_approve
                )
            elif args.remove_command == "host":
                return handle_mcp_remove_host(
                    args.host_name, args.no_backup,
                    args.dry_run, args.auto_approve
                )
            else:
                print("Unknown remove command")
                return 1

        elif args.mcp_command == "sync":
            return handle_mcp_sync(
                from_env=getattr(args, 'from_env', None),
                from_host=getattr(args, 'from_host', None),
                to_hosts=args.to_host,
                servers=getattr(args, 'servers', None),
                pattern=getattr(args, 'pattern', None),
                dry_run=args.dry_run,
                auto_approve=args.auto_approve,
                no_backup=args.no_backup
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