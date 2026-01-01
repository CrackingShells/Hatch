"""Package CLI handlers for Hatch.

This module contains handlers for package management commands:
- package add: Add a package to an environment
- package remove: Remove a package from an environment
- package list: List packages in an environment
- package sync: Synchronize package MCP servers to hosts

All handlers follow the signature: (args: Namespace) -> int
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
)
from hatch.mcp_host_config import (
    MCPHostConfigurationManager,
    MCPHostType,
    MCPServerConfig,
)
from hatch.mcp_host_config.models import HOST_MODEL_REGISTRY, MCPServerConfigOmni
from hatch.mcp_host_config.reporting import display_report, generate_conversion_report

if TYPE_CHECKING:
    from hatch.environment_manager import HatchEnvironmentManager


def handle_package_remove(args: Namespace) -> int:
    """Handle 'hatch package remove' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - package_name: Name of package to remove
            - env: Optional environment name (default: current)
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    package_name = args.package_name
    env = getattr(args, "env", None)

    if env_manager.remove_package(package_name, env):
        print(f"Successfully removed package: {package_name}")
        return EXIT_SUCCESS
    else:
        print(f"Failed to remove package: {package_name}")
        return EXIT_ERROR


def handle_package_list(args: Namespace) -> int:
    """Handle 'hatch package list' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional environment name (default: current)
    
    Returns:
        Exit code (0 for success)
    """
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
            host_model_class = HOST_MODEL_REGISTRY.get(host_type)
            if not host_model_class:
                print(f"✗ Error: No model registered for host '{host}'")
                continue

            for pkg_name, server_config in server_configs:
                try:
                    # Convert MCPServerConfig to Omni model
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
                        dry_run=dry_run,
                    )
                    display_report(report)

                    if dry_run:
                        print(f"[DRY RUN] Would configure {server_config.name} ({pkg_name}) on {host}")
                        success_count += 1
                        continue

                    result = mcp_manager.configure_server(
                        hostname=host,
                        server_config=host_config,
                        no_backup=no_backup,
                    )

                    if result.success:
                        print(f"✓ Configured {server_config.name} ({pkg_name}) on {host}")
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

    # Add package to environment
    if not env_manager.add_package_to_environment(
        package_path_or_name,
        env,
        version,
        force_download,
        refresh_registry,
        auto_approve,
    ):
        print(f"Failed to add package: {package_path_or_name}")
        return EXIT_ERROR

    print(f"Successfully added package: {package_path_or_name}")

    # Handle MCP host configuration if requested
    if host_arg:
        try:
            hosts = parse_host_list(host_arg)
            env_name = env or env_manager.get_current_environment()

            package_name, package_names, _ = _get_package_names_with_dependencies(
                env_manager, package_path_or_name, env_name
            )

            print(f"Configuring MCP server for package '{package_name}' on {len(hosts)} host(s)...")

            success_count, total = _configure_packages_on_hosts(
                env_manager=env_manager,
                mcp_manager=mcp_manager,
                env_name=env_name,
                package_names=package_names,
                hosts=hosts,
                no_backup=False,  # Always backup when adding packages
                dry_run=False,
            )

            if success_count > 0:
                print(f"MCP configuration completed: {success_count // len(package_names)}/{len(hosts)} hosts configured")
            else:
                print("Warning: MCP configuration failed on all hosts")

        except ValueError as e:
            print(f"Warning: MCP host configuration failed: {e}")
            # Don't fail the entire operation for MCP configuration issues

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
            print(f"Error: No MCP server configurations found for package '{package_name}' or its dependencies")
            return EXIT_ERROR

        if dry_run:
            print(f"[DRY RUN] Would synchronize MCP servers for {len(server_configs)} package(s) to hosts: {hosts}")
            for pkg_name, config in server_configs:
                print(f"[DRY RUN] - {pkg_name}: {config.name} -> {' '.join(config.args)}")

                # Generate and display conversion reports for dry-run mode
                for host in hosts:
                    try:
                        host_type = MCPHostType(host)
                        host_model_class = HOST_MODEL_REGISTRY.get(host_type)
                        if not host_model_class:
                            print(f"[DRY RUN] ✗ Error: No model registered for host '{host}'")
                            continue

                        # Convert to Omni model
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
            return EXIT_SUCCESS

        # Confirm operation unless auto-approved
        package_desc = (
            f"package '{package_name}'"
            if len(server_configs) == 1
            else f"{len(server_configs)} packages ('{package_name}' + dependencies)"
        )
        if not request_confirmation(
            f"Synchronize MCP servers for {package_desc} to {len(hosts)} host(s)?",
            auto_approve,
        ):
            print("Operation cancelled.")
            return EXIT_SUCCESS

        # Perform synchronization
        success_count, total_operations = _configure_packages_on_hosts(
            env_manager=env_manager,
            mcp_manager=mcp_manager,
            env_name=env_name,
            package_names=[pkg_name for pkg_name, _ in server_configs],
            hosts=hosts,
            no_backup=no_backup,
            dry_run=False,
        )

        # Report results
        if success_count == total_operations:
            package_desc = (
                f"package '{package_name}'"
                if len(server_configs) == 1
                else f"{len(server_configs)} packages"
            )
            print(f"Successfully synchronized {package_desc} to all {len(hosts)} host(s)")
            return EXIT_SUCCESS
        elif success_count > 0:
            print(f"Partially synchronized: {success_count}/{total_operations} operations succeeded")
            return EXIT_ERROR
        else:
            package_desc = (
                f"package '{package_name}'"
                if len(server_configs) == 1
                else f"{len(server_configs)} packages"
            )
            print(f"Failed to synchronize {package_desc} to any hosts")
            return EXIT_ERROR

    except ValueError as e:
        print(f"Error: {e}")
        return EXIT_ERROR
