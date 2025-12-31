"""Shared utilities for Hatch CLI.

This module provides common utilities used across CLI handlers:
- Exit code constants for consistent return values
- Version retrieval from package metadata
- User interaction helpers (confirmation prompts)
- Parsing utilities for CLI arguments
- Package MCP configuration helpers

These utilities are extracted from cli_hatch.py to enable cleaner
handler-based architecture and easier testing.
"""

from importlib.metadata import PackageNotFoundError, version

# Exit code constants for consistent CLI return values
EXIT_SUCCESS = 0
EXIT_ERROR = 1


def get_hatch_version() -> str:
    """Get Hatch version from package metadata.

    Returns:
        str: Version string from package metadata, or 'unknown (development mode)'
             if package is not installed.
    """
    try:
        return version("hatch")
    except PackageNotFoundError:
        return "unknown (development mode)"


import os
import sys
from typing import Optional


def request_confirmation(message: str, auto_approve: bool = False) -> bool:
    """Request user confirmation with non-TTY support following Hatch patterns.

    Args:
        message: The confirmation message to display
        auto_approve: If True, automatically approve without prompting

    Returns:
        bool: True if confirmed, False otherwise
    """
    # Check for auto-approve first
    if auto_approve or os.getenv("HATCH_AUTO_APPROVE", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return True

    # Interactive mode - request user input (works in both TTY and test environments)
    try:
        while True:
            response = input(f"{message} [y/N]: ").strip().lower()
            if response in ["y", "yes"]:
                return True
            elif response in ["n", "no", ""]:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    except (EOFError, KeyboardInterrupt):
        # Only auto-approve on EOF/interrupt if not in TTY (non-interactive environment)
        if not sys.stdin.isatty():
            return True
        return False


def parse_env_vars(env_list: Optional[list]) -> dict:
    """Parse environment variables from command line format.

    Args:
        env_list: List of strings in KEY=VALUE format

    Returns:
        dict: Dictionary of environment variable key-value pairs
    """
    if not env_list:
        return {}

    env_dict = {}
    for env_var in env_list:
        if "=" not in env_var:
            print(
                f"Warning: Invalid environment variable format '{env_var}'. Expected KEY=VALUE"
            )
            continue
        key, value = env_var.split("=", 1)
        env_dict[key.strip()] = value.strip()

    return env_dict


def parse_header(header_list: Optional[list]) -> dict:
    """Parse HTTP headers from command line format.

    Args:
        header_list: List of strings in KEY=VALUE format

    Returns:
        dict: Dictionary of header key-value pairs
    """
    if not header_list:
        return {}

    headers_dict = {}
    for header in header_list:
        if "=" not in header:
            print(f"Warning: Invalid header format '{header}'. Expected KEY=VALUE")
            continue
        key, value = header.split("=", 1)
        headers_dict[key.strip()] = value.strip()

    return headers_dict


def parse_input(input_list: Optional[list]) -> Optional[list]:
    """Parse VS Code input variable definitions from command line format.

    Format: type,id,description[,password=true]
    Example: promptString,api-key,GitHub Personal Access Token,password=true

    Args:
        input_list: List of input definition strings

    Returns:
        List of input variable definition dictionaries, or None if no inputs provided.
    """
    if not input_list:
        return None

    parsed_inputs = []
    for input_str in input_list:
        parts = [p.strip() for p in input_str.split(",")]
        if len(parts) < 3:
            print(
                f"Warning: Invalid input format '{input_str}'. Expected: type,id,description[,password=true]"
            )
            continue

        input_def = {"type": parts[0], "id": parts[1], "description": parts[2]}

        # Check for optional password flag
        if len(parts) > 3 and parts[3].lower() == "password=true":
            input_def["password"] = True

        parsed_inputs.append(input_def)

    return parsed_inputs if parsed_inputs else None


from typing import List

from hatch.mcp_host_config import MCPHostRegistry, MCPHostType


def parse_host_list(host_arg: str) -> List[str]:
    """Parse comma-separated host list or 'all'.

    Args:
        host_arg: Comma-separated host names or 'all' for all available hosts

    Returns:
        List[str]: List of host name strings

    Raises:
        ValueError: If an unknown host name is provided
    """
    if not host_arg:
        return []

    if host_arg.lower() == "all":
        available_hosts = MCPHostRegistry.detect_available_hosts()
        return [host.value for host in available_hosts]

    hosts = []
    for host_str in host_arg.split(","):
        host_str = host_str.strip()
        try:
            host_type = MCPHostType(host_str)
            hosts.append(host_type.value)
        except ValueError:
            available = [h.value for h in MCPHostType]
            raise ValueError(f"Unknown host '{host_str}'. Available: {available}")

    return hosts


import json
from pathlib import Path

from hatch.environment_manager import HatchEnvironmentManager
from hatch.mcp_host_config import MCPServerConfig


def get_package_mcp_server_config(
    env_manager: HatchEnvironmentManager, env_name: str, package_name: str
) -> MCPServerConfig:
    """Get MCP server configuration for a package using existing APIs.

    Args:
        env_manager: The environment manager instance
        env_name: Name of the environment containing the package
        package_name: Name of the package to get config for

    Returns:
        MCPServerConfig: Server configuration for the package

    Raises:
        ValueError: If package not found, not a Hatch package, or has no MCP entry point
    """
    try:
        # Get package info from environment
        packages = env_manager.list_packages(env_name)
        package_info = next(
            (pkg for pkg in packages if pkg["name"] == package_name), None
        )

        if not package_info:
            raise ValueError(
                f"Package '{package_name}' not found in environment '{env_name}'"
            )

        # Load package metadata using existing pattern from environment_manager.py:716-727
        package_path = Path(package_info["source"]["path"])
        metadata_path = package_path / "hatch_metadata.json"

        if not metadata_path.exists():
            raise ValueError(
                f"Package '{package_name}' is not a Hatch package (no hatch_metadata.json)"
            )

        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Use PackageService for schema-aware access
        from hatch_validator.package.package_service import PackageService

        package_service = PackageService(metadata)

        # Get the HatchMCP entry point (this handles both v1.2.0 and v1.2.1 schemas)
        mcp_entry_point = package_service.get_mcp_entry_point()
        if not mcp_entry_point:
            raise ValueError(
                f"Package '{package_name}' does not have a HatchMCP entry point"
            )

        # Get environment-specific Python executable
        python_executable = env_manager.get_current_python_executable()
        if not python_executable:
            # Fallback to system Python if no environment-specific Python available
            python_executable = "python"

        # Create server configuration
        server_path = str(package_path / mcp_entry_point)
        server_config = MCPServerConfig(
            name=package_name, command=python_executable, args=[server_path], env={}
        )

        return server_config

    except Exception as e:
        raise ValueError(
            f"Failed to get MCP server config for package '{package_name}': {e}"
        )
