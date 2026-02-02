"""Package CLI handlers for Hatch.

This module contains handlers for package management commands. Packages are
MCP server implementations that can be installed into environments and
configured on MCP host platforms.

Commands:
    - hatch package add <name>: Add a package to an environment
    - hatch package remove <name>: Remove a package from an environment
    - hatch package list: List packages in an environment
    - hatch package sync <name>: Synchronize package MCP servers to hosts

Package Workflow:
    1. Add package to environment: hatch package add my-mcp-server
    2. Configure on hosts: hatch mcp configure claude-desktop my-mcp-server ...
    3. Or sync automatically: hatch package sync my-mcp-server --host all

Handler Signature:
    All handlers follow: (args: Namespace) -> int
    - args.env_manager: HatchEnvironmentManager instance
    - Returns: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure

Internal Helpers:
    _configure_packages_on_hosts(): Shared logic for configuring packages on hosts

Example:
    $ hatch package add mcp-server-fetch
    $ hatch package list
    $ hatch package sync mcp-server-fetch --host claude-desktop,cursor
"""

import json
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, Optional

from hatch_validator.package.package_service import PackageService

from hatch.cli.cli_utils import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    request_confirmation,
    parse_host_list,
    get_package_mcp_server_config,
    ResultReporter,
    ConsequenceType,
)
from hatch.mcp_host_config import (
    MCPHostConfigurationManager,
    MCPHostType,
    MCPServerConfig,
)
from hatch.mcp_host_config.reporting import generate_conversion_report

if TYPE_CHECKING:
    from hatch.environment_manager import HatchEnvironmentManager


def handle_package_remove(args: Namespace) -> int:
    """Handle 'hatch package remove' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - package_name: Name of package to remove
            - env: Optional environment name (default: current)
            - dry_run: Preview changes without execution
            - auto_approve: Skip confirmation prompt
    
    Returns:
        Exit code (0 for success, 1 for error)
    
    Reference: R03 §3.1 (03-mutation_output_specification_v0.md)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    package_name = args.package_name
    env = getattr(args, "env", None)
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)

    # Create reporter for unified output
    reporter = ResultReporter("hatch package remove", dry_run=dry_run)
    reporter.add(ConsequenceType.REMOVE, f"Package '{package_name}'")

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Show prompt and request confirmation unless auto-approved
    if not auto_approve:
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)
        
        if not request_confirmation("Proceed?"):
            print("Operation cancelled.")
            return EXIT_SUCCESS

    if env_manager.remove_package(package_name, env):
        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(f"Failed to remove package '{package_name}'")
        return EXIT_ERROR


def handle_package_list(args: Namespace) -> int:
    """Handle 'hatch package list' command.
    
    .. deprecated::
        This command is deprecated. Use 'hatch env list' instead,
        which shows packages inline with environment information.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional environment name (default: current)
    
    Returns:
        Exit code (0 for success)
    """
    import sys
    
    # Emit deprecation warning to stderr
    print(
        "Warning: 'hatch package list' is deprecated. "
        "Use 'hatch env list' instead, which shows packages inline.",
        file=sys.stderr
    )
    
    env_manager: "HatchEnvironmentManager" = args.env_manager
    env = getattr(args, "env", None)

    packages = env_manager.list_packages(env)

    if not packages:
        print(f"No packages found in environment: {env}")
        return EXIT_SUCCESS

    print(f"Packages in environment '{env}':")
    for pkg in packages:
        print(
            f"{pkg['name']} ({pkg['version']})\tHatch compliant: {pkg['hatch_compliant']}\tsource: {pkg['source']['uri']}\tlocation: {pkg['source']['path']}"
        )
    return EXIT_SUCCESS



def _get_package_names_with_dependencies(
    env_manager: "HatchEnvironmentManager",
    package_path_or_name: str,
    env_name: str,
) -> Tuple[str, List[str], Optional[PackageService]]:
    """Get package name and its dependencies.
    
    Args:
        env_manager: HatchEnvironmentManager instance
        package_path_or_name: Package path or name
        env_name: Environment name
    
    Returns:
        Tuple of (package_name, list_of_all_package_names, package_service_or_none)
    """
    package_name = package_path_or_name
    package_service = None
    package_names = []

    # Check if it's a local package path
    pkg_path = Path(package_path_or_name)
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
                            "dependencies": {},
                        }
                        package_service = PackageService(metadata)
                        break

            if package_service is None:
                print(
                    f"Warning: Could not find package '{package_name}' in environment '{env_name}'. Skipping dependency analysis."
                )
        except Exception as e:
            print(
                f"Warning: Could not load package metadata for '{package_name}': {e}. Skipping dependency analysis."
            )

    # Get dependency names if we have package service
    if package_service:
        # Get Hatch dependencies
        dependencies = package_service.get_dependencies()
        hatch_deps = dependencies.get("hatch", [])
        package_names = [dep.get("name") for dep in hatch_deps if dep.get("name")]

        # Resolve local dependency paths to actual names
        for i in range(len(package_names)):
            dep_path = Path(package_names[i])
            if dep_path.exists() and dep_path.is_dir():
                try:
                    with open(dep_path / "hatch_metadata.json", "r") as f:
                        dep_metadata = json.load(f)
                        dep_service = PackageService(dep_metadata)
                    package_names[i] = dep_service.get_field("name")
                except Exception as e:
                    print(
                        f"Warning: Could not resolve dependency path '{package_names[i]}': {e}"
                    )

    # Add the main package to the list
    package_names.append(package_name)

    return package_name, package_names, package_service


def _configure_packages_on_hosts(
    env_manager: "HatchEnvironmentManager",
    mcp_manager: MCPHostConfigurationManager,
    env_name: str,
    package_names: List[str],
    hosts: List[str],
    no_backup: bool = False,
    dry_run: bool = False,
    reporter: Optional[ResultReporter] = None,
) -> Tuple[int, int]:
    """Configure MCP servers for packages on specified hosts.
    
    This is shared logic used by both package add and package sync commands.
    
    Args:
        env_manager: HatchEnvironmentManager instance
        mcp_manager: MCPHostConfigurationManager instance
        env_name: Environment name
        package_names: List of package names to configure
        hosts: List of host names to configure on
        no_backup: Skip backup creation
        dry_run: Preview only, don't execute
        reporter: Optional ResultReporter for unified output
    
    Returns:
        Tuple of (success_count, total_operations)
    """
    # Get MCP server configurations for all packages
    server_configs: List[Tuple[str, MCPServerConfig]] = []
    for pkg_name in package_names:
        try:
            config = get_package_mcp_server_config(env_manager, env_name, pkg_name)
            server_configs.append((pkg_name, config))
        except Exception as e:
            print(f"Warning: Could not get MCP configuration for package '{pkg_name}': {e}")

    if not server_configs:
        return 0, 0

    total_operations = len(server_configs) * len(hosts)
    success_count = 0

    for host in hosts:
        try:
            # Convert string to MCPHostType enum
            host_type = MCPHostType(host)

            for pkg_name, server_config in server_configs:
                try:
                    # Generate conversion report for field-level details
                    report = generate_conversion_report(
                        operation="create",
                        server_name=server_config.name,
                        target_host=host_type,
                        config=server_config,
                        dry_run=dry_run,
                    )
                    
                    # Add to reporter if provided
                    if reporter:
                        reporter.add_from_conversion_report(report)

                    if dry_run:
                        success_count += 1
                        continue

                    # Pass MCPServerConfig directly - adapters handle serialization
                    result = mcp_manager.configure_server(
                        hostname=host,
                        server_config=server_config,
                        no_backup=no_backup,
                    )

                    if result.success:
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
                            print(f"[WARNING] Failed to update package metadata for {pkg_name}: {e}")
                    else:
                        print(f"✗ Failed to configure {server_config.name} ({pkg_name}) on {host}: {result.error_message}")

                except Exception as e:
                    print(f"✗ Error configuring {server_config.name} ({pkg_name}) on {host}: {e}")

        except ValueError as e:
            print(f"✗ Invalid host '{host}': {e}")
            continue

    return success_count, total_operations



def handle_package_add(args: Namespace) -> int:
    """Handle 'hatch package add' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - mcp_manager: MCPHostConfigurationManager instance
            - package_path_or_name: Package path or name
            - env: Optional environment name
            - version: Optional version
            - force_download: Force download even if cached
            - refresh_registry: Force registry refresh
            - auto_approve: Skip confirmation prompts
            - host: Optional comma-separated host list for MCP configuration
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    mcp_manager: MCPHostConfigurationManager = args.mcp_manager
    
    package_path_or_name = args.package_path_or_name
    env = getattr(args, "env", None)
    version = getattr(args, "version", None)
    force_download = getattr(args, "force_download", False)
    refresh_registry = getattr(args, "refresh_registry", False)
    auto_approve = getattr(args, "auto_approve", False)
    host_arg = getattr(args, "host", None)
    dry_run = getattr(args, "dry_run", False)

    # Create reporter for unified output
    reporter = ResultReporter("hatch package add", dry_run=dry_run)
    
    # Add package to environment
    reporter.add(ConsequenceType.ADD, f"Package '{package_path_or_name}'")
    
    if not env_manager.add_package_to_environment(
        package_path_or_name,
        env,
        version,
        force_download,
        refresh_registry,
        auto_approve,
    ):
        reporter.report_error(f"Failed to add package '{package_path_or_name}'")
        return EXIT_ERROR

    # Handle MCP host configuration if requested
    if host_arg:
        try:
            hosts = parse_host_list(host_arg)
            env_name = env or env_manager.get_current_environment()

            package_name, package_names, _ = _get_package_names_with_dependencies(
                env_manager, package_path_or_name, env_name
            )

            success_count, total = _configure_packages_on_hosts(
                env_manager=env_manager,
                mcp_manager=mcp_manager,
                env_name=env_name,
                package_names=package_names,
                hosts=hosts,
                no_backup=False,  # Always backup when adding packages
                dry_run=dry_run,
                reporter=reporter,
            )

        except ValueError as e:
            print(f"Warning: MCP host configuration failed: {e}")
            # Don't fail the entire operation for MCP configuration issues

    # Report results
    reporter.report_result()
    return EXIT_SUCCESS


def handle_package_sync(args: Namespace) -> int:
    """Handle 'hatch package sync' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - mcp_manager: MCPHostConfigurationManager instance
            - package_name: Package name to sync
            - host: Comma-separated host list (required)
            - env: Optional environment name
            - dry_run: Preview only
            - auto_approve: Skip confirmation
            - no_backup: Skip backup creation
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    mcp_manager: MCPHostConfigurationManager = args.mcp_manager
    
    package_name = args.package_name
    host_arg = args.host
    env = getattr(args, "env", None)
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)
    no_backup = getattr(args, "no_backup", False)

    # Create reporter for unified output
    reporter = ResultReporter("hatch package sync", dry_run=dry_run)

    try:
        # Parse host list
        hosts = parse_host_list(host_arg)
        env_name = env or env_manager.get_current_environment()

        # Get all packages to sync (main package + dependencies)
        package_names = [package_name]

        # Try to get dependencies for the main package
        try:
            env_data = env_manager.get_environment_data(env_name)
            if env_data:
                # Find the main package in the environment
                main_package = None
                for pkg in env_data.packages:
                    if pkg.name == package_name:
                        main_package = pkg
                        break

                if main_package:
                    # Create a minimal metadata structure for PackageService
                    metadata = {
                        "name": main_package.name,
                        "version": main_package.version,
                        "dependencies": {},
                    }
                    package_service = PackageService(metadata)

                    # Get Hatch dependencies
                    dependencies = package_service.get_dependencies()
                    hatch_deps = dependencies.get("hatch", [])
                    dep_names = [dep.get("name") for dep in hatch_deps if dep.get("name")]

                    # Add dependencies to the sync list (before main package)
                    package_names = dep_names + [package_name]
                else:
                    print(
                        f"Warning: Package '{package_name}' not found in environment '{env_name}'. Syncing only the specified package."
                    )
            else:
                print(
                    f"Warning: Could not access environment '{env_name}'. Syncing only the specified package."
                )
        except Exception as e:
            print(
                f"Warning: Could not analyze dependencies for '{package_name}': {e}. Syncing only the specified package."
            )

        # Get MCP server configurations for all packages
        server_configs: List[Tuple[str, MCPServerConfig]] = []
        for pkg_name in package_names:
            try:
                config = get_package_mcp_server_config(env_manager, env_name, pkg_name)
                server_configs.append((pkg_name, config))
            except Exception as e:
                print(f"Warning: Could not get MCP configuration for package '{pkg_name}': {e}")

        if not server_configs:
            reporter.report_error(
                f"No MCP server configurations found for package '{package_name}' or its dependencies"
            )
            return EXIT_ERROR

        # Build consequences for preview/confirmation
        for pkg_name, config in server_configs:
            for host in hosts:
                try:
                    host_type = MCPHostType(host)
                    report = generate_conversion_report(
                        operation="create",
                        server_name=config.name,
                        target_host=host_type,
                        config=config,
                        dry_run=dry_run,
                    )
                    reporter.add_from_conversion_report(report)
                except ValueError:
                    reporter.add(ConsequenceType.SKIP, f"Invalid host '{host}'")

        # Show preview and get confirmation
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS

        # Confirm operation unless auto-approved
        if not request_confirmation("Proceed?", auto_approve):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform synchronization (reporter already has consequences from preview)
        success_count, total_operations = _configure_packages_on_hosts(
            env_manager=env_manager,
            mcp_manager=mcp_manager,
            env_name=env_name,
            package_names=[pkg_name for pkg_name, _ in server_configs],
            hosts=hosts,
            no_backup=no_backup,
            dry_run=False,
            reporter=None,  # Don't add again, we already have consequences
        )

        # Report results
        reporter.report_result()
        
        if success_count == total_operations:
            return EXIT_SUCCESS
        elif success_count > 0:
            return EXIT_ERROR
        else:
            return EXIT_ERROR

    except ValueError as e:
        reporter.report_error(str(e))
        return EXIT_ERROR
