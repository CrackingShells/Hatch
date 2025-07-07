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

from hatch.environment_manager import HatchEnvironmentManager
from hatch.template_generator import create_package_template

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
                                   help="Don't install hatch_mcp_server in the new environment")
    env_create_parser.add_argument("--hatch_mcp_server_tag", 
                                   help="Git tag/branch reference for hatch_mcp_server installation (e.g., 'dev', 'v0.1.0')")
    
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
    
    # Show Python environment info
    python_info_parser = env_python_subparsers.add_parser("info", help="Show Python environment information")
    python_info_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_info_parser.add_argument("--detailed", action="store_true", help="Show detailed diagnostics")
    
    # Remove Python environment
    python_remove_parser = env_python_subparsers.add_parser("remove", help="Remove Python environment")
    python_remove_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_remove_parser.add_argument("--force", action="store_true", help="Force removal without confirmation")
    
    # Launch Python shell
    python_shell_parser = env_python_subparsers.add_parser("shell", help="Launch Python shell in environment")
    python_shell_parser.add_argument("--hatch_env", default=None, help="Hatch environment name in which the Python environment is located (default: current environment)")
    python_shell_parser.add_argument("--cmd", help="Command to run in the shell (optional)")
    
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
            if hasattr(args, 'python_command'):
                if args.python_command == "init":
                    python_version = getattr(args, 'python_version', None)
                    force = getattr(args, 'force', False)
                
                    if env_manager.create_python_environment_only(args.hatch_env, python_version, force):
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
                        # Ask for confirmation
                        env_name = args.hatch_env or env_manager.get_current_environment()
                        response = input(f"Remove Python environment for '{env_name}'? [y/N]: ")
                        if response.lower() not in ['y', 'yes']:
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
                else:
                    print("Unknown Python environment command")
                    return 1
            else:
                print("No Python subcommand specified")
                return 1
    
    elif args.command == "package":
        if args.pkg_command == "add":
            if env_manager.add_package_to_environment(args.package_path_or_name, args.env, args.version, 
                                                      args.force_download, args.refresh_registry):
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