"""Environment CLI handlers for Hatch.

This module contains handlers for environment management commands:
- env create: Create a new environment
- env remove: Remove an environment
- env list: List all environments
- env use: Set current environment
- env current: Show current environment
- env python init: Initialize Python environment
- env python info: Show Python environment info
- env python remove: Remove Python environment
- env python shell: Launch Python shell
- env python add-hatch-mcp: Add hatch_mcp_server wrapper

All handlers follow the signature: (args: Namespace) -> int
"""

from argparse import Namespace
from typing import TYPE_CHECKING

from hatch.cli.cli_utils import EXIT_SUCCESS, EXIT_ERROR, request_confirmation

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

    if env_manager.create_environment(
        name,
        description,
        python_version=python_version,
        create_python_env=create_python_env,
        no_hatch_mcp_server=no_hatch_mcp_server,
        hatch_mcp_server_tag=hatch_mcp_server_tag,
    ):
        print(f"Environment created: {name}")

        # Show Python environment status
        if create_python_env and env_manager.is_python_environment_available():
            python_exec = env_manager.python_env_manager.get_python_executable(name)
            if python_exec:
                python_version_info = env_manager.python_env_manager.get_python_version(name)
                print(f"Python environment: {python_exec}")
                if python_version_info:
                    print(f"Python version: {python_version_info}")
            else:
                print("Python environment creation failed")
        elif create_python_env:
            print("Python environment requested but conda/mamba not available")

        return EXIT_SUCCESS
    else:
        print(f"Failed to create environment: {name}")
        return EXIT_ERROR


def handle_env_remove(args: Namespace) -> int:
    """Handle 'hatch env remove' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - name: Environment name to remove
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
    name = args.name

    if env_manager.remove_environment(name):
        print(f"Environment removed: {name}")
        return EXIT_SUCCESS
    else:
        print(f"Failed to remove environment: {name}")
        return EXIT_ERROR


def handle_env_list(args: Namespace) -> int:
    """Handle 'hatch env list' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
    
    Returns:
        Exit code (0 for success)
    """
    env_manager: "HatchEnvironmentManager" = args.env_manager
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
            python_info = env_manager.get_python_environment_info(env.get("name"))
            if python_info:
                python_version = python_info.get("python_version", "Unknown")
                conda_env = python_info.get("conda_env_name", "N/A")
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

    if env_manager.set_current_environment(name):
        print(f"Current environment set to: {name}")
        return EXIT_SUCCESS
    else:
        print(f"Failed to set environment: {name}")
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

    if env_manager.create_python_environment_only(
        hatch_env,
        python_version,
        force,
        no_hatch_mcp_server=no_hatch_mcp_server,
        hatch_mcp_server_tag=hatch_mcp_server_tag,
    ):
        env_name = hatch_env or env_manager.get_current_environment()
        print(f"Python environment initialized for: {env_name}")

        # Show Python environment info
        python_info = env_manager.get_python_environment_info(hatch_env)
        if python_info:
            print(f"  Python executable: {python_info['python_executable']}")
            print(f"  Python version: {python_info.get('python_version', 'Unknown')}")
            print(f"  Conda environment: {python_info.get('conda_env_name', 'N/A')}")

        return EXIT_SUCCESS
    else:
        env_name = hatch_env or env_manager.get_current_environment()
        print(f"Failed to initialize Python environment for: {env_name}")
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
        print(f"  Status: {'Active' if python_info.get('enabled', False) else 'Inactive'}")
        print(f"  Python executable: {python_info['python_executable']}")
        print(f"  Python version: {python_info.get('python_version', 'Unknown')}")
        print(f"  Conda environment: {python_info.get('conda_env_name', 'N/A')}")
        print(f"  Environment path: {python_info['environment_path']}")
        print(f"  Created: {python_info.get('created_at', 'Unknown')}")
        print(f"  Package count: {python_info.get('package_count', 0)}")
        print(f"  Packages:")
        for pkg in python_info.get("packages", []):
            print(f"    - {pkg['name']} ({pkg['version']})")

        if detailed:
            print(f"\nDiagnostics:")
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

    if not force:
        # Ask for confirmation using TTY-aware function
        env_name = hatch_env or env_manager.get_current_environment()
        if not request_confirmation(f"Remove Python environment for '{env_name}'?"):
            print("Operation cancelled")
            return EXIT_SUCCESS

    if env_manager.remove_python_environment_only(hatch_env):
        env_name = hatch_env or env_manager.get_current_environment()
        print(f"Python environment removed from: {env_name}")
        return EXIT_SUCCESS
    else:
        env_name = hatch_env or env_manager.get_current_environment()
        print(f"Failed to remove Python environment from: {env_name}")
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
        print(f"Failed to launch Python shell for: {env_name}")
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

    env_name = hatch_env or env_manager.get_current_environment()

    if env_manager.install_mcp_server(env_name, tag):
        print(f"hatch_mcp_server wrapper installed successfully in environment: {env_name}")
        return EXIT_SUCCESS
    else:
        print(f"Failed to install hatch_mcp_server wrapper in environment: {env_name}")
        return EXIT_ERROR
