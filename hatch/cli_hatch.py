"""Command-line interface for the Hatch package manager.

This module provides the CLI functionality for Hatch, allowing users to:
- Create new package templates
- Validate packages
- Manage environments
- Manage packages within environments
"""

import argparse
import logging
import sys
from pathlib import Path

from .environment_manager import HatchEnvironmentManager
from .template_generator import create_package_template

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
    pkg_add_parser.add_argument("--skip-python-deps", action="store_true", help="Skip installation of Python dependencies")
    pkg_add_parser.add_argument("--upgrade-python-deps", action="store_true", help="Upgrade existing Python dependencies")
    pkg_add_parser.add_argument("--python-interpreter", default=None, help="Specify which Python interpreter to use")
    
    # Remove package command
    pkg_remove_parser = pkg_subparsers.add_parser("remove", help="Remove a package from the current environment")
    pkg_remove_parser.add_argument("package_name", help="Name of the package to remove")
    pkg_remove_parser.add_argument("--env", "-e", default=None, help="Environment name (default: current environment)")
    
    # List packages command
    pkg_list_parser = pkg_subparsers.add_parser("list", help="List packages in an environment")
    pkg_list_parser.add_argument("--env", "-e", help="Environment name (default: current environment)")    # Parse arguments

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
        
        # Use the validator from environment manager
        is_valid, _ = env_manager.package_validator.validate_package(package_path)
        
        if is_valid:
            print(f"Package validation SUCCESSFUL: {package_path}")
            return 0
        else:
            print(f"Package validation FAILED: {package_path}")
            return 1
        
    elif args.command == "env":
        if args.env_command == "create":
            if env_manager.create_environment(args.name, args.description):
                print(f"Environment created: {args.name}")
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
            for env in environments:
                current_marker = "* " if env.get("is_current") else "  "
                description = f" - {env.get('description')}" if env.get("description") else ""
                print(f"{current_marker}{env.get('name')}{description}")
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
        else:
            parser.print_help()
            return 1
    elif args.command == "package":
        if args.pkg_command == "add":
            if env_manager.add_package_to_environment(args.package_path_or_name, args.env, args.version, 
                                                      args.force_download, args.refresh_registry,
                                                      args.skip_python_deps, args.upgrade_python_deps,
                                                      args.python_interpreter):
                print(f"Successfully added package: {args.package_path_or_name}")
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
            
        else:
            parser.print_help()
            return 1
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())