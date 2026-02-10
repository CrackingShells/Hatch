"""Environment CLI handlers for Hatch.

This module contains handlers for environment management commands. Environments
provide isolated contexts for managing packages and their MCP server configurations.

Commands:
    Basic Environment Management:
        - hatch env create <name>: Create a new environment
        - hatch env remove <name>: Remove an environment
        - hatch env list: List all environments
        - hatch env use <name>: Set current environment
        - hatch env current: Show current environment

    Python Environment Management:
        - hatch env python init: Initialize Python virtual environment
        - hatch env python info: Show Python environment info
        - hatch env python remove: Remove Python virtual environment
        - hatch env python shell: Launch interactive Python shell
        - hatch env python add-hatch-mcp: Add hatch_mcp_server wrapper script

Handler Signature:
    All handlers follow: (args: Namespace) -> int
    - args.env_manager: HatchEnvironmentManager instance
    - Returns: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure

Example:
    $ hatch env create my-project
    $ hatch env use my-project
    $ hatch env python init
    $ hatch env python shell
"""

from argparse import Namespace
from typing import TYPE_CHECKING

from hatch.cli.cli_utils import (
    EXIT_SUCCESS,
    EXIT_ERROR,
    request_confirmation,
    ResultReporter,
    ConsequenceType,
    TableFormatter,
    ColumnDef,
    ValidationError,
    format_validation_error,
    format_info,
)

if TYPE_CHECKING:
    from hatch.environment_manager import HatchEnvironmentManager


def handle_env_create(args: Namespace) -> int:
    """Handle 'hatch env create' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - name: Environment name
            - description: Environment description
            - python_version: Optional Python version
            - no_python: Skip Python environment creation
            - no_hatch_mcp_server: Skip hatch_mcp_server installation
            - hatch_mcp_server_tag: Git tag for hatch_mcp_server

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    name = args.name
    description = getattr(args, "description", "")
    python_version = getattr(args, "python_version", None)
    create_python_env = not getattr(args, "no_python", False)
    no_hatch_mcp_server = getattr(args, "no_hatch_mcp_server", False)
    hatch_mcp_server_tag = getattr(args, "hatch_mcp_server_tag", None)
    dry_run = getattr(args, "dry_run", False)

    # Create reporter for unified output
    reporter = ResultReporter("hatch env create", dry_run=dry_run)
    reporter.add(ConsequenceType.CREATE, f"Environment '{name}'")

    if create_python_env:
        version_str = f" ({python_version})" if python_version else ""
        reporter.add(ConsequenceType.CREATE, f"Python environment{version_str}")

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    if env_manager.create_environment(
        name,
        description,
        python_version=python_version,
        create_python_env=create_python_env,
        no_hatch_mcp_server=no_hatch_mcp_server,
        hatch_mcp_server_tag=hatch_mcp_server_tag,
    ):
        # Update reporter with actual Python environment details
        if create_python_env and env_manager.is_python_environment_available():
            python_exec = env_manager.python_env_manager.get_python_executable(name)
            if python_exec:
                python_version_info = env_manager.python_env_manager.get_python_version(
                    name
                )
                # Add details as child consequences would be ideal, but for now just report success

        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(f"Failed to create environment '{name}'")
        return EXIT_ERROR


def handle_env_remove(args: Namespace) -> int:
    """Handle 'hatch env remove' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - name: Environment name to remove
            - dry_run: Preview changes without execution
            - auto_approve: Skip confirmation prompt

    Returns:
        Exit code (0 for success, 1 for error)

    Reference: R03 §3.1 (03-mutation_output_specification_v0.md)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    name = args.name
    dry_run = getattr(args, "dry_run", False)
    auto_approve = getattr(args, "auto_approve", False)

    # Create reporter for unified output
    reporter = ResultReporter("hatch env remove", dry_run=dry_run)
    reporter.add(ConsequenceType.REMOVE, f"Environment '{name}'")

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Show prompt and request confirmation unless auto-approved
    if not auto_approve:
        prompt = reporter.report_prompt()
        if prompt:
            print(prompt)

        if not request_confirmation("Proceed?"):
            format_info("Operation cancelled")
            return EXIT_SUCCESS

    if env_manager.remove_environment(name):
        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(f"Failed to remove environment '{name}'")
        return EXIT_ERROR


def handle_env_list(args: Namespace) -> int:
    """Handle 'hatch env list' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - pattern: Optional regex pattern to filter environments
            - json: Optional flag for JSON output

    Returns:
        Exit code (0 for success)

    Reference: R02 §2.1 (02-list_output_format_specification_v2.md)
    """
    import json as json_module
    import re

    env_manager: "HatchEnvironmentManager" = args.env_manager
    json_output: bool = getattr(args, "json", False)
    pattern: str = getattr(args, "pattern", None)
    environments = env_manager.list_environments()

    # Apply pattern filter if specified
    if pattern:
        try:
            regex = re.compile(pattern)
            environments = [
                env for env in environments if regex.search(env.get("name", ""))
            ]
        except re.error as e:
            format_validation_error(
                ValidationError(
                    f"Invalid regex pattern: {e}",
                    field="--pattern",
                    suggestion="Use a valid Python regex pattern",
                )
            )
            return EXIT_ERROR

    if json_output:
        # JSON output per R02 §8.1
        env_data = []
        for env in environments:
            env_name = env.get("name")
            python_version = None
            if env.get("python_environment", False):
                python_info = env_manager.get_python_environment_info(env_name)
                if python_info:
                    python_version = python_info.get("python_version")

            packages_list = env_manager.list_packages(env_name)
            pkg_names = [pkg["name"] for pkg in packages_list] if packages_list else []

            env_data.append(
                {
                    "name": env_name,
                    "is_current": env.get("is_current", False),
                    "python_version": python_version,
                    "packages": pkg_names,
                }
            )

        print(json_module.dumps({"environments": env_data}, indent=2))
        return EXIT_SUCCESS

    # Table output
    print("Environments:")

    # Define table columns per R10 §5.1 (simplified output - count only)
    columns = [
        ColumnDef(name="Name", width=15),
        ColumnDef(name="Python", width=10),
        ColumnDef(name="Packages", width=10, align="right"),
    ]
    formatter = TableFormatter(columns)

    for env in environments:
        # Name with current marker
        current_marker = "* " if env.get("is_current") else "  "
        name = f"{current_marker}{env.get('name')}"

        # Python version
        python_version = "-"
        if env.get("python_environment", False):
            python_info = env_manager.get_python_environment_info(env.get("name"))
            if python_info:
                python_version = python_info.get("python_version", "Unknown")

        # Packages - show count only per R10 §5.1
        packages_list = env_manager.list_packages(env.get("name"))
        packages_count = str(len(packages_list)) if packages_list else "0"

        formatter.add_row([name, python_version, packages_count])

    print(formatter.render())
    return EXIT_SUCCESS


def handle_env_use(args: Namespace) -> int:
    """Handle 'hatch env use' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - name: Environment name to set as current

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    name = args.name
    dry_run = getattr(args, "dry_run", False)

    # Create reporter for unified output
    reporter = ResultReporter("hatch env use", dry_run=dry_run)
    reporter.add(ConsequenceType.SET, f"Current environment → '{name}'")

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    if env_manager.set_current_environment(name):
        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(f"Failed to set environment '{name}'")
        return EXIT_ERROR


def handle_env_current(args: Namespace) -> int:
    """Handle 'hatch env current' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance

    Returns:
        Exit code (0 for success)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    current_env = env_manager.get_current_environment()
    print(f"Current environment: {current_env}")
    return EXIT_SUCCESS


def handle_env_python_init(args: Namespace) -> int:
    """Handle 'hatch env python init' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - hatch_env: Optional environment name (default: current)
            - python_version: Optional Python version
            - force: Force recreation if exists
            - no_hatch_mcp_server: Skip hatch_mcp_server installation
            - hatch_mcp_server_tag: Git tag for hatch_mcp_server

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    hatch_env = getattr(args, "hatch_env", None)
    python_version = getattr(args, "python_version", None)
    force = getattr(args, "force", False)
    no_hatch_mcp_server = getattr(args, "no_hatch_mcp_server", False)
    hatch_mcp_server_tag = getattr(args, "hatch_mcp_server_tag", None)
    dry_run = getattr(args, "dry_run", False)

    env_name = hatch_env or env_manager.get_current_environment()

    # Create reporter for unified output
    reporter = ResultReporter("hatch env python init", dry_run=dry_run)
    version_str = f" ({python_version})" if python_version else ""
    reporter.add(
        ConsequenceType.INITIALIZE, f"Python environment for '{env_name}'{version_str}"
    )

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    if env_manager.create_python_environment_only(
        hatch_env,
        python_version,
        force,
        no_hatch_mcp_server=no_hatch_mcp_server,
        hatch_mcp_server_tag=hatch_mcp_server_tag,
    ):
        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(
            f"Failed to initialize Python environment for '{env_name}'"
        )
        return EXIT_ERROR


def handle_env_python_info(args: Namespace) -> int:
    """Handle 'hatch env python info' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - hatch_env: Optional environment name (default: current)
            - detailed: Show detailed diagnostics

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    hatch_env = getattr(args, "hatch_env", None)
    detailed = getattr(args, "detailed", False)

    python_info = env_manager.get_python_environment_info(hatch_env)

    if python_info:
        env_name = hatch_env or env_manager.get_current_environment()
        print(f"Python environment info for '{env_name}':")
        print(
            f"  Status: {'Active' if python_info.get('enabled', False) else 'Inactive'}"
        )
        print(f"  Python executable: {python_info['python_executable']}")
        print(f"  Python version: {python_info.get('python_version', 'Unknown')}")
        print(f"  Conda environment: {python_info.get('conda_env_name', 'N/A')}")
        print(f"  Environment path: {python_info['environment_path']}")
        print(f"  Created: {python_info.get('created_at', 'Unknown')}")
        print(f"  Package count: {python_info.get('package_count', 0)}")
        print("  Packages:")
        for pkg in python_info.get("packages", []):
            print(f"    - {pkg['name']} ({pkg['version']})")

        if detailed:
            print("\nDiagnostics:")
            diagnostics = env_manager.get_python_environment_diagnostics(hatch_env)
            if diagnostics:
                for key, value in diagnostics.items():
                    print(f"  {key}: {value}")
            else:
                print("  No diagnostics available")

        return EXIT_SUCCESS
    else:
        env_name = hatch_env or env_manager.get_current_environment()
        print(f"No Python environment found for: {env_name}")

        # Show diagnostics for missing environment
        if detailed:
            print("\nDiagnostics:")
            general_diagnostics = env_manager.get_python_manager_diagnostics()
            for key, value in general_diagnostics.items():
                print(f"  {key}: {value}")

        return EXIT_ERROR


def handle_env_python_remove(args: Namespace) -> int:
    """Handle 'hatch env python remove' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - hatch_env: Optional environment name (default: current)
            - force: Skip confirmation prompt

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    hatch_env = getattr(args, "hatch_env", None)
    force = getattr(args, "force", False)
    dry_run = getattr(args, "dry_run", False)

    env_name = hatch_env or env_manager.get_current_environment()

    # Create reporter for unified output
    reporter = ResultReporter("hatch env python remove", dry_run=dry_run)
    reporter.add(ConsequenceType.REMOVE, f"Python environment for '{env_name}'")

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    if not force:
        # Ask for confirmation using TTY-aware function
        if not request_confirmation(f"Remove Python environment for '{env_name}'?"):
            format_info("Operation cancelled")
            return EXIT_SUCCESS

    if env_manager.remove_python_environment_only(hatch_env):
        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(f"Failed to remove Python environment from '{env_name}'")
        return EXIT_ERROR


def handle_env_python_shell(args: Namespace) -> int:
    """Handle 'hatch env python shell' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - hatch_env: Optional environment name (default: current)
            - cmd: Optional command to run in shell

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    hatch_env = getattr(args, "hatch_env", None)
    cmd = getattr(args, "cmd", None)

    if env_manager.launch_python_shell(hatch_env, cmd):
        return EXIT_SUCCESS
    else:
        env_name = hatch_env or env_manager.get_current_environment()
        reporter = ResultReporter("hatch env python shell")
        reporter.report_error(f"Failed to launch Python shell for '{env_name}'")
        return EXIT_ERROR


def handle_env_python_add_hatch_mcp(args: Namespace) -> int:
    """Handle 'hatch env python add-hatch-mcp' command.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - hatch_env: Optional environment name (default: current)
            - tag: Git tag/branch for wrapper installation

    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    hatch_env = getattr(args, "hatch_env", None)
    tag = getattr(args, "tag", None)
    dry_run = getattr(args, "dry_run", False)

    env_name = hatch_env or env_manager.get_current_environment()

    # Create reporter for unified output
    reporter = ResultReporter("hatch env python add-hatch-mcp", dry_run=dry_run)
    reporter.add(ConsequenceType.INSTALL, f"hatch_mcp_server wrapper in '{env_name}'")

    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    if env_manager.install_mcp_server(env_name, tag):
        reporter.report_result()
        return EXIT_SUCCESS
    else:
        reporter.report_error(
            f"Failed to install hatch_mcp_server wrapper in environment '{env_name}'"
        )
        return EXIT_ERROR


def handle_env_show(args: Namespace) -> int:
    """Handle 'hatch env show' command.

    Displays detailed hierarchical view of a specific environment.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - name: Environment name to show

    Returns:
        Exit code (0 for success, 1 for error)

    Reference: R02 §2.2 (02-list_output_format_specification_v2.md)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    name = args.name

    # Validate environment exists
    if not env_manager.environment_exists(name):
        format_validation_error(
            ValidationError(
                f"Environment '{name}' does not exist",
                field="name",
                suggestion="Use 'hatch env list' to see available environments",
            )
        )
        return EXIT_ERROR

    # Get environment data
    env_data = env_manager.get_environment_data(name)
    current_env = env_manager.get_current_environment()
    is_current = name == current_env

    # Header
    status = " (active)" if is_current else ""
    print(f"Environment: {name}{status}")

    # Description
    description = env_data.get("description", "")
    if description:
        print(f"  Description: {description}")

    # Created timestamp
    created_at = env_data.get("created_at", "Unknown")
    print(f"  Created: {created_at}")
    print()

    # Python Environment section
    python_info = env_manager.get_python_environment_info(name)
    print("  Python Environment:")
    if python_info:
        print(f"    Version: {python_info.get('python_version', 'Unknown')}")
        print(f"    Executable: {python_info.get('python_executable', 'N/A')}")
        conda_env = python_info.get("conda_env_name", "N/A")
        if conda_env and conda_env != "N/A":
            print(f"    Conda env: {conda_env}")
        status = "Active" if python_info.get("enabled", False) else "Inactive"
        print(f"    Status: {status}")
    else:
        print("    (not initialized)")
    print()

    # Packages section
    packages = env_manager.list_packages(name)
    pkg_count = len(packages) if packages else 0
    print(f"  Packages ({pkg_count}):")

    if packages:
        for pkg in packages:
            pkg_name = pkg.get("name", "unknown")
            print(f"    {pkg_name}")

            # Version
            version = pkg.get("version", "unknown")
            print(f"      Version: {version}")

            # Source
            source = pkg.get("source", {})
            source_type = source.get("type", "unknown")
            source_path = source.get("path", source.get("url", "N/A"))
            print(f"      Source: {source_type} ({source_path})")

            # Deployed hosts
            configured_hosts = pkg.get("configured_hosts", {})
            if configured_hosts:
                hosts_list = ", ".join(configured_hosts.keys())
                print(f"      Deployed to: {hosts_list}")
            else:
                print("      Deployed to: (none)")
            print()
    else:
        print("    (empty)")

    return EXIT_SUCCESS


def handle_env_list_hosts(args: Namespace) -> int:
    """Handle 'hatch env list hosts' command.

    Lists environment/host/server deployments from environment data.
    Shows only Hatch-managed packages and their host deployments.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional regex pattern to filter by environment name
            - server: Optional regex pattern to filter by server name
            - json: Optional flag for JSON output

    Returns:
        Exit code (0 for success, 1 for error)

    Reference: R10 §3.3 (10-namespace_consistency_specification_v2.md)
    """
    import json as json_module
    import re

    env_manager: "HatchEnvironmentManager" = args.env_manager
    env_pattern: str = getattr(args, "env", None)
    server_pattern: str = getattr(args, "server", None)
    json_output: bool = getattr(args, "json", False)

    # Compile regex patterns if provided
    env_re = None
    if env_pattern:
        try:
            env_re = re.compile(env_pattern)
        except re.error as e:
            format_validation_error(
                ValidationError(
                    f"Invalid env regex pattern: {e}",
                    field="--env",
                    suggestion="Use a valid Python regex pattern",
                )
            )
            return EXIT_ERROR

    server_re = None
    if server_pattern:
        try:
            server_re = re.compile(server_pattern)
        except re.error as e:
            format_validation_error(
                ValidationError(
                    f"Invalid server regex pattern: {e}",
                    field="--server",
                    suggestion="Use a valid Python regex pattern",
                )
            )
            return EXIT_ERROR

    # Get all environments
    environments = env_manager.list_environments()

    # Collect rows: (environment, host, server, version)
    rows = []

    for env_info in environments:
        env_name = (
            env_info.get("name", env_info) if isinstance(env_info, dict) else env_info
        )

        # Apply environment filter
        if env_re and not env_re.search(env_name):
            continue

        try:
            env_data = env_manager.get_environment_data(env_name)
            packages = (
                env_data.get("packages", []) if isinstance(env_data, dict) else []
            )

            for pkg in packages:
                pkg_name = pkg.get("name") if isinstance(pkg, dict) else None
                pkg_version = pkg.get("version", "-") if isinstance(pkg, dict) else "-"
                configured_hosts = (
                    pkg.get("configured_hosts", {}) if isinstance(pkg, dict) else {}
                )

                if not pkg_name or not configured_hosts:
                    continue

                # Apply server filter
                if server_re and not server_re.search(pkg_name):
                    continue

                # Add a row for each host deployment
                for host_name in configured_hosts.keys():
                    rows.append((env_name, host_name, pkg_name, pkg_version))
        except Exception:
            continue

    # Sort rows by environment (alphabetically), then host, then server
    rows.sort(key=lambda x: (x[0], x[1], x[2]))

    # JSON output per R10 §8
    if json_output:
        rows_data = []
        for env, host, server, version in rows:
            rows_data.append(
                {"environment": env, "host": host, "server": server, "version": version}
            )
        print(json_module.dumps({"rows": rows_data}, indent=2))
        return EXIT_SUCCESS

    # Display results
    if not rows:
        if env_pattern or server_pattern:
            print("No matching environment host deployments found")
        else:
            print("No environment host deployments found")
        return EXIT_SUCCESS

    print("Environment Host Deployments:")

    # Define table columns per R10 §3.3: Environment → Host → Server → Version
    columns = [
        ColumnDef(name="Environment", width=15),
        ColumnDef(name="Host", width=18),
        ColumnDef(name="Server", width=18),
        ColumnDef(name="Version", width=10),
    ]
    formatter = TableFormatter(columns)

    for env, host, server, version in rows:
        formatter.add_row([env, host, server, version])

    print(formatter.render())
    return EXIT_SUCCESS


def handle_env_list_servers(args: Namespace) -> int:
    """Handle 'hatch env list servers' command.

    Lists environment/server/host deployments from environment data.
    Shows only Hatch-managed packages. Undeployed packages show '-' in Host column.

    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - env: Optional regex pattern to filter by environment name
            - host: Optional regex pattern to filter by host name (use '-' for undeployed)
            - json: Optional flag for JSON output

    Returns:
        Exit code (0 for success, 1 for error)

    Reference: R10 §3.4 (10-namespace_consistency_specification_v2.md)
    """
    import json as json_module
    import re

    env_manager: "HatchEnvironmentManager" = args.env_manager
    env_pattern: str = getattr(args, "env", None)
    host_pattern: str = getattr(args, "host", None)
    json_output: bool = getattr(args, "json", False)

    # Compile regex patterns if provided
    env_re = None
    if env_pattern:
        try:
            env_re = re.compile(env_pattern)
        except re.error as e:
            format_validation_error(
                ValidationError(
                    f"Invalid env regex pattern: {e}",
                    field="--env",
                    suggestion="Use a valid Python regex pattern",
                )
            )
            return EXIT_ERROR

    # Special handling for '-' (undeployed filter)
    filter_undeployed = host_pattern == "-"
    host_re = None
    if host_pattern and not filter_undeployed:
        try:
            host_re = re.compile(host_pattern)
        except re.error as e:
            format_validation_error(
                ValidationError(
                    f"Invalid host regex pattern: {e}",
                    field="--host",
                    suggestion="Use a valid Python regex pattern",
                )
            )
            return EXIT_ERROR

    # Get all environments
    environments = env_manager.list_environments()

    # Collect rows: (environment, server, host, version)
    rows = []

    for env_info in environments:
        env_name = (
            env_info.get("name", env_info) if isinstance(env_info, dict) else env_info
        )

        # Apply environment filter
        if env_re and not env_re.search(env_name):
            continue

        try:
            env_data = env_manager.get_environment_data(env_name)
            packages = (
                env_data.get("packages", []) if isinstance(env_data, dict) else []
            )

            for pkg in packages:
                pkg_name = pkg.get("name") if isinstance(pkg, dict) else None
                pkg_version = pkg.get("version", "-") if isinstance(pkg, dict) else "-"
                configured_hosts = (
                    pkg.get("configured_hosts", {}) if isinstance(pkg, dict) else {}
                )

                if not pkg_name:
                    continue

                if configured_hosts:
                    # Package is deployed to one or more hosts
                    for host_name in configured_hosts.keys():
                        # Apply host filter
                        if filter_undeployed:
                            # Skip deployed packages when filtering for undeployed
                            continue
                        if host_re and not host_re.search(host_name):
                            continue
                        rows.append((env_name, pkg_name, host_name, pkg_version))
                else:
                    # Package is not deployed (undeployed)
                    if host_re:
                        # Skip undeployed when filtering by specific host pattern
                        continue
                    if not filter_undeployed and host_pattern:
                        # Skip undeployed when filtering by host (unless specifically filtering for undeployed)
                        continue
                    rows.append((env_name, pkg_name, "-", pkg_version))
        except Exception:
            continue

    # Sort rows by environment (alphabetically), then server, then host
    rows.sort(key=lambda x: (x[0], x[1], x[2]))

    # JSON output per R10 §8
    if json_output:
        rows_data = []
        for env, server, host, version in rows:
            rows_data.append(
                {
                    "environment": env,
                    "server": server,
                    "host": host if host != "-" else None,
                    "version": version,
                }
            )
        print(json_module.dumps({"rows": rows_data}, indent=2))
        return EXIT_SUCCESS

    # Display results
    if not rows:
        if env_pattern or host_pattern:
            print("No matching environment server deployments found")
        else:
            print("No environment server deployments found")
        return EXIT_SUCCESS

    print("Environment Servers:")

    # Define table columns per R10 §3.4: Environment → Server → Host → Version
    columns = [
        ColumnDef(name="Environment", width=15),
        ColumnDef(name="Server", width=18),
        ColumnDef(name="Host", width=18),
        ColumnDef(name="Version", width=10),
    ]
    formatter = TableFormatter(columns)

    for env, server, host, version in rows:
        formatter.add_row([env, server, host, version])

    print(formatter.render())
    return EXIT_SUCCESS
