"""System CLI handlers for Hatch.

This module contains handlers for system-level commands that operate on
packages as a whole rather than within environments.

Commands:
    - hatch create <name>: Create a new package template from scratch
    - hatch validate <path>: Validate a package against the Hatch schema

Package Creation:
    The create command generates a complete package template with:
    - pyproject.toml with Hatch metadata
    - Source directory structure
    - README and LICENSE files
    - Basic MCP server implementation

Package Validation:
    The validate command checks:
    - pyproject.toml structure and required fields
    - Hatch-specific metadata (mcp_server entry points)
    - Package dependencies and version constraints

Handler Signature:
    All handlers follow: (args: Namespace) -> int
    Returns: EXIT_SUCCESS (0) on success, EXIT_ERROR (1) on failure

Example:
    $ hatch create my-mcp-server --description "My custom MCP server"
    $ hatch validate ./my-mcp-server
"""

from argparse import Namespace
from pathlib import Path

from hatch_validator import HatchPackageValidator

from hatch.cli.cli_utils import EXIT_SUCCESS, EXIT_ERROR
from hatch.template_generator import create_package_template


def handle_create(args: Namespace) -> int:
    """Handle 'hatch create' command.
    
    Args:
        args: Namespace with:
            - name: Package name
            - dir: Target directory (default: current directory)
            - description: Package description (optional)
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    target_dir = Path(args.dir).resolve()
    description = getattr(args, "description", "")
    
    try:
        package_dir = create_package_template(
            target_dir=target_dir,
            package_name=args.name,
            description=description,
        )
        print(f"Package template created at: {package_dir}")
        return EXIT_SUCCESS
    except Exception as e:
        print(f"Failed to create package template: {e}")
        return EXIT_ERROR


def handle_validate(args: Namespace) -> int:
    """Handle 'hatch validate' command.
    
    Args:
        args: Namespace with:
            - env_manager: HatchEnvironmentManager instance
            - package_dir: Path to package directory
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    from hatch.environment_manager import HatchEnvironmentManager
    
    env_manager: HatchEnvironmentManager = args.env_manager
    package_path = Path(args.package_dir).resolve()

    # Create validator with registry data from environment manager
    validator = HatchPackageValidator(
        version="latest",
        allow_local_dependencies=True,
        registry_data=env_manager.registry_data,
    )

    # Validate the package
    is_valid, validation_results = validator.validate_package(package_path)

    if is_valid:
        print(f"Package validation SUCCESSFUL: {package_path}")
        return EXIT_SUCCESS
    else:
        print(f"Package validation FAILED: {package_path}")

        # Print detailed validation results if available
        if validation_results and isinstance(validation_results, dict):
            for category, result in validation_results.items():
                if (
                    category != "valid"
                    and category != "metadata"
                    and isinstance(result, dict)
                ):
                    if not result.get("valid", True) and result.get("errors"):
                        print(f"\n{category.replace('_', ' ').title()} errors:")
                        for error in result["errors"]:
                            print(f"  - {error}")

        return EXIT_ERROR
