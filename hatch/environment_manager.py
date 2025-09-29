"""Environment Manager for Hatch package system.

This module provides the core functionality for managing isolated environments
for Hatch packages.
"""
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from hatch_validator.registry.registry_service import RegistryService, RegistryError
from hatch.registry_retriever import RegistryRetriever
from hatch_validator.package.package_service import PackageService
from hatch.package_loader import HatchPackageLoader
from hatch.installers.dependency_installation_orchestrator import DependencyInstallerOrchestrator
from hatch.installers.installation_context import InstallationContext
from hatch.python_environment_manager import PythonEnvironmentManager, PythonEnvironmentError
from hatch.mcp_host_config.models import MCPServerConfig

class HatchEnvironmentError(Exception):
    """Exception raised for environment-related errors."""
    pass


class HatchEnvironmentManager:
    """Manages Hatch environments for package installation and isolation.
    
    This class handles:
    1. Creating and managing isolated environments
    2. Environment lifecycle and state management  
    3. Delegating package installation to the DependencyInstallerOrchestrator
    4. Managing environment metadata and persistence
    """
    def __init__(self, 
                 environments_dir: Optional[Path] = None,
                 cache_ttl: int = 86400,  # Default TTL is 24 hours
                 cache_dir: Optional[Path] = None,
                 simulation_mode: bool = False,
                 local_registry_cache_path: Optional[Path] = None):
        """Initialize the Hatch environment manager.
        
        Args:
            environments_dir (Path, optional): Directory to store environments. Defaults to ~/.hatch/envs.
            cache_ttl (int): Time-to-live for cache in seconds. Defaults to 86400 (24 hours).
            cache_dir (Path, optional): Directory to store local cache files. Defaults to ~/.hatch.
            simulation_mode (bool): Whether to operate in local simulation mode. Defaults to False.
            local_registry_cache_path (Path, optional): Path to local registry file. Defaults to None.
        
        """

        self.logger = logging.getLogger("hatch.environment_manager")
        self.logger.setLevel(logging.INFO)
        # Set up environment directories
        self.environments_dir = environments_dir or (Path.home() / ".hatch" / "envs")
        self.environments_dir.mkdir(exist_ok=True)

        self.environments_file = self.environments_dir / "environments.json"
        self.current_env_file = self.environments_dir / "current_env"
        
        
        # Initialize Python environment manager
        self.python_env_manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
        
        # Initialize dependencies
        self.package_loader = HatchPackageLoader(cache_dir=cache_dir)
        self.retriever = RegistryRetriever(cache_ttl=cache_ttl,
                                      local_cache_dir=cache_dir,
                                      simulation_mode=simulation_mode,
                                      local_registry_cache_path=local_registry_cache_path)
        self.registry_data = self.retriever.get_registry()
        
        # Initialize services for dependency management
        self.registry_service = RegistryService(self.registry_data)
        
        self.dependency_orchestrator = DependencyInstallerOrchestrator(
            package_loader=self.package_loader,
            registry_service=self.registry_service,
            registry_data=self.registry_data
        )

        # Load environments into cache
        self._environments = self._load_environments()
        self._current_env_name = self._load_current_env_name()
        # Set correct Python executable info to the one of default environment
        self._configure_python_executable(self._current_env_name)

    def _initialize_environments_file(self):
        """Create the initial environments file with default environment."""
        default_environments = {}
        
        with open(self.environments_file, 'w') as f:
            json.dump(default_environments, f, indent=2)
        
        self.logger.info("Initialized environments file with default environment")
    
    def _initialize_current_env_file(self):
        """Create the current environment file pointing to the default environment."""
        with open(self.current_env_file, 'w') as f:
            f.write("default")
        
        self.logger.info("Initialized current environment to default")
    
    def _load_environments(self) -> Dict:
        """Load environments from the environments file.

        This method attempts to read the environments from the JSON file.
        If the file is not found or contains invalid JSON, it initializes
        the file with a default environment and returns that.

        Returns:
            Dict: Dictionary of environments loaded from the file.
        """

        try:
            with open(self.environments_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.info(f"Failed to load environments: {e}. Initializing with default environment.")
            
            # Touch the files with default values
            self._initialize_environments_file()
            self._initialize_current_env_file()

            # Load created default environment
            with open(self.environments_file, 'r') as f:
                _environments = json.load(f)

            # Assign to cache
            self._environments = _environments

            # Actually create the default environment
            self.create_environment("default", description="Default environment")

            return _environments

    
    def _load_current_env_name(self) -> str:
        """Load current environment name from disk."""
        try:
            with open(self.current_env_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            self._initialize_current_env_file()
            return "default"
    
    def get_environments(self) -> Dict:
        """Get environments from cache."""
        return self._environments
    
    def reload_environments(self):
        """Reload environments from disk."""
        self._environments = self._load_environments()
        self._current_env_name = self._load_current_env_name()
        self.logger.info("Reloaded environments from disk")
    
    def _save_environments(self):
        """Save environments to the environments file."""
        try:
            with open(self.environments_file, 'w') as f:
                json.dump(self._environments, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save environments: {e}")
            raise HatchEnvironmentError(f"Failed to save environments: {e}")
    
    def get_current_environment(self) -> str:
        """Get the name of the current environment from cache."""
        return self._current_env_name
    
    def get_current_environment_data(self) -> Dict:
        """Get the data for the current environment."""
        return self._environments[self._current_env_name]

    def get_environment_data(self, env_name: str) -> Dict:
        """Get the data for a specific environment.

        Args:
            env_name: Name of the environment

        Returns:
            Dict: Environment data

        Raises:
            KeyError: If environment doesn't exist
        """
        return self._environments[env_name]
    
    def set_current_environment(self, env_name: str) -> bool:
        """
        Set the current environment.
        
        Args:
            env_name: Name of the environment to set as current
            
        Returns:
            bool: True if successful, False if environment doesn't exist
        """
        # Check if environment exists
        if env_name not in self._environments:
            self.logger.error(f"Environment does not exist: {env_name}")
            return False
        
        # Set current environment
        try:
            with open(self.current_env_file, 'w') as f:
                f.write(env_name)
            
            # Update cache
            self._current_env_name = env_name
            
            # Configure Python executable for dependency installation
            self._configure_python_executable(env_name)
            
            self.logger.info(f"Current environment set to: {env_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set current environment: {e}")
            return False
    
    def _configure_python_executable(self, env_name: str) -> None:
        """Configure the Python executable for the current environment.
        
        This method sets the Python executable in the dependency orchestrator's
        InstallationContext so that python_installer.py uses the correct interpreter.
        
        Args:
            env_name: Name of the environment to configure Python for
        """
        # Get Python executable from Python environment manager
        python_executable = self.python_env_manager.get_python_executable(env_name)
        
        if python_executable:
            # Configure the dependency orchestrator with the Python executable
            python_env_vars = self.python_env_manager.get_environment_activation_info(env_name)
            self.dependency_orchestrator.set_python_env_vars(python_env_vars)
        else:
            # Use system Python as fallback
            system_python = sys.executable
            python_env_vars = {"PYTHON": system_python}
            self.dependency_orchestrator.set_python_env_vars(python_env_vars)
    
    def get_current_python_executable(self) -> Optional[str]:
        """Get the Python executable for the current environment.
        
        Returns:
            str: Path to Python executable, None if no current environment or no Python env
        """
        if not self._current_env_name:
            return None
        
        return self.python_env_manager.get_python_executable(self._current_env_name)
    
    def list_environments(self) -> List[Dict]:
        """
        List all available environments.
        
        Returns:
            List[Dict]: List of environment information dictionaries
        """
        result = []
        for name, env_data in self._environments.items():
            env_info = env_data.copy()
            env_info["is_current"] = (name == self._current_env_name)
            result.append(env_info)
        
        return result
    
    def create_environment(self, name: str, description: str = "", 
                          python_version: Optional[str] = None, 
                          create_python_env: bool = True,
                          no_hatch_mcp_server: bool = False,
                          hatch_mcp_server_tag: Optional[str] = None) -> bool:
        """
        Create a new environment.
        
        Args:
            name: Name of the environment
            description: Description of the environment
            python_version: Python version for the environment (e.g., "3.11", "3.12")
            create_python_env: Whether to create a Python environment using conda/mamba
            no_hatch_mcp_server: Whether to skip installing hatch_mcp_server in the environment
            hatch_mcp_server_tag: Git tag/branch reference for hatch_mcp_server installation
            
        Returns:
            bool: True if created successfully, False if environment already exists
        """
        # Allow alphanumeric characters and underscores
        if not name or not all(c.isalnum() or c == '_' for c in name):
            self.logger.error("Environment name must be alphanumeric or underscore")
            return False
        
        # Check if environment already exists
        if name in self._environments:
            self.logger.warning(f"Environment already exists: {name}")
            return False
        
        # Create Python environment if requested and conda/mamba is available
        python_env_info = None
        if create_python_env and self.python_env_manager.is_available():
            try:
                python_env_created = self.python_env_manager.create_python_environment(
                    name, python_version=python_version
                )
                if python_env_created:
                    self.logger.info(f"Created Python environment for {name}")
                    
                    # Get detailed Python environment information
                    python_info = self.python_env_manager.get_environment_info(name)
                    if python_info:
                        python_env_info = {
                            "enabled": True,
                            "conda_env_name": python_info.get("conda_env_name"),
                            "python_executable": python_info.get("python_executable"),
                            "created_at": datetime.datetime.now().isoformat(),
                            "version": python_info.get("python_version"),
                            "requested_version": python_version,
                            "manager": python_info.get("manager", "conda")
                        }
                    else:
                        # Fallback if detailed info is not available
                        python_env_info = {
                            "enabled": True,
                            "conda_env_name": f"hatch_{name}",
                            "python_executable": None,
                            "created_at": datetime.datetime.now().isoformat(),
                            "version": None,
                            "requested_version": python_version,
                            "manager": "conda"
                        }
                else:
                    self.logger.warning(f"Failed to create Python environment for {name}")
            except PythonEnvironmentError as e:
                self.logger.error(f"Failed to create Python environment: {e}")
                # Continue with Hatch environment creation even if Python env creation fails
        elif create_python_env:
            self.logger.warning("Python environment creation requested but conda/mamba not available")
        
        # Create new Hatch environment with enhanced metadata
        env_data = {
            "name": name,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "packages": [],
            "python_environment": python_env_info is not None,  # Legacy field for backward compatibility
            "python_version": python_version,  # Legacy field for backward compatibility
            "python_env": python_env_info  # Enhanced metadata structure
        }
        
        self._environments[name] = env_data
        
        self._save_environments()
        self.logger.info(f"Created environment: {name}")
        
        # Install hatch_mcp_server by default unless opted out
        if not no_hatch_mcp_server and python_env_info is not None:
            try:
                self._install_hatch_mcp_server(name, hatch_mcp_server_tag)
            except Exception as e:
                self.logger.warning(f"Failed to install hatch_mcp_server wrapper in environment {name}: {e}")
                # Don't fail environment creation if MCP wrapper installation fails
        
        return True
    
    def _install_hatch_mcp_server(self, env_name: str, tag: Optional[str] = None) -> None:
        """Install hatch_mcp_server wrapper package in the specified environment.
        
        Args:
            env_name (str): Name of the environment to install MCP wrapper in.
            tag (str, optional): Git tag/branch reference for the installation. Defaults to None (uses default branch).
            
        Raises:
            HatchEnvironmentError: If installation fails.
        """
        try:
            # Construct the package URL with optional tag
            if tag:
                package_git_url = f"git+https://github.com/CrackingShells/Hatch-MCP-Server.git@{tag}"
            else:
                package_git_url = "git+https://github.com/CrackingShells/Hatch-MCP-Server.git"
            
            # Create dependency structure following the schema
            mcp_dep = {
                "name": f"hatch_mcp_server @ {package_git_url}",
                "version_constraint": "*",
                "package_manager": "pip",
                "type": "python",
                "uri": package_git_url
            }
            
            # Get environment path
            env_path = self.get_environment_path(env_name)
            
            # Create installation context
            context = InstallationContext(
                environment_path=env_path,
                environment_name=env_name,
                temp_dir=env_path / ".tmp",
                cache_dir=self.package_loader.cache_dir if hasattr(self.package_loader, 'cache_dir') else None,
                parallel_enabled=False,
                force_reinstall=False,
                simulation_mode=False,
                extra_config={
                    "package_loader": self.package_loader,
                    "registry_service": self.registry_service,
                    "registry_data": self.registry_data
                }
            )
            
            # Configure Python environment variables if available
            python_executable = self.python_env_manager.get_python_executable(env_name)
            if python_executable:
                python_env_vars = {"PYTHON": python_executable}
                self.dependency_orchestrator.set_python_env_vars(python_env_vars)
                context.set_config("python_env_vars", python_env_vars)
            
            # Install using the orchestrator
            self.logger.info(f"Installing hatch_mcp_server wrapper in environment {env_name}")
            self.logger.info(f"Using python executable: {python_executable}")
            installed_package = self.dependency_orchestrator.install_single_dep(mcp_dep, context)
            
            self._save_environments()
            self.logger.info(f"Successfully installed hatch_mcp_server wrapper in environment {env_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to install hatch_mcp_server wrapper: {e}")
            raise HatchEnvironmentError(f"Failed to install hatch_mcp_server wrapper: {e}") from e

    def install_mcp_server(self, env_name: Optional[str] = None, tag: Optional[str] = None) -> bool:
        """Install hatch_mcp_server wrapper package in an existing environment.
        
        Args:
            env_name (str, optional): Name of the hatch environment. Uses current environment if None.
            tag (str, optional): Git tag/branch reference for the installation. Defaults to None (uses default branch).
            
        Returns:
            bool: True if installation succeeded, False otherwise.
        """
        if env_name is None:
            env_name = self._current_env_name
            
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment does not exist: {env_name}")
            return False
            
        # Check if environment has Python support
        env_data = self._environments[env_name]
        if not env_data.get("python_env"):
            self.logger.error(f"Environment {env_name} does not have Python support")
            return False
            
        try:
            self._install_hatch_mcp_server(env_name, tag)
            return True
        except Exception as e:
            self.logger.error(f"Failed to install MCP wrapper in environment {env_name}: {e}")
            return False

    def remove_environment(self, name: str) -> bool:
        """
        Remove an environment.

        Args:
            name: Name of the environment to remove

        Returns:
            bool: True if removed successfully, False otherwise
        """
        # Cannot remove default environment
        if name == "default":
            self.logger.error("Cannot remove default environment")
            return False

        # Check if environment exists
        if name not in self._environments:
            self.logger.warning(f"Environment does not exist: {name}")
            return False

        # If removing current environment, switch to default
        if name == self._current_env_name:
            self.set_current_environment("default")

        # Clean up MCP server configurations for all packages in this environment
        env_data = self._environments[name]
        packages = env_data.get("packages", [])
        if packages:
            self.logger.info(f"Cleaning up MCP server configurations for {len(packages)} packages in environment {name}")
            try:
                from .mcp_host_config.host_management import MCPHostConfigurationManager
                mcp_manager = MCPHostConfigurationManager()

                for pkg in packages:
                    package_name = pkg.get("name")
                    configured_hosts = pkg.get("configured_hosts", {})

                    if configured_hosts and package_name:
                        for hostname in configured_hosts.keys():
                            try:
                                # Remove server from host configuration file
                                result = mcp_manager.remove_server(
                                    server_name=package_name,  # In current 1:1 design, package name = server name
                                    hostname=hostname,
                                    no_backup=False  # Create backup for safety
                                )

                                if result.success:
                                    self.logger.info(f"Removed MCP server '{package_name}' from host '{hostname}' (env removal)")
                                else:
                                    self.logger.warning(f"Failed to remove MCP server '{package_name}' from host '{hostname}': {result.error_message}")
                            except Exception as e:
                                self.logger.warning(f"Error removing MCP server '{package_name}' from host '{hostname}': {e}")

            except ImportError:
                self.logger.warning("MCP host configuration manager not available for cleanup")
            except Exception as e:
                self.logger.warning(f"Error during MCP server cleanup for environment removal: {e}")

        # Remove Python environment if it exists
        if env_data.get("python_environment", False):
            try:
                self.python_env_manager.remove_python_environment(name)
                self.logger.info(f"Removed Python environment for {name}")
            except PythonEnvironmentError as e:
                self.logger.warning(f"Failed to remove Python environment: {e}")

        # Remove environment
        del self._environments[name]

        # Save environments and update cache
        self._save_environments()
        self.logger.info(f"Removed environment: {name}")
        return True
    
    def environment_exists(self, name: str) -> bool:
        """
        Check if an environment exists.
        
        Args:
            name: Name of the environment to check
            
        Returns:
            bool: True if environment exists, False otherwise
        """
        return name in self._environments
    
    def add_package_to_environment(self, package_path_or_name: str, 
                                  env_name: Optional[str] = None, 
                                  version_constraint: Optional[str] = None,
                                  force_download: bool = False,
                                  refresh_registry: bool = False,
                                  auto_approve: bool = False) -> bool:
        """Add a package to an environment.
        
        This method delegates all installation orchestration to the DependencyInstallerOrchestrator
        while maintaining responsibility for environment lifecycle and state management.

        Args:
            package_path_or_name (str): Path to local package or name of remote package.
            env_name (str, optional): Environment to add to. Defaults to current environment.
            version_constraint (str, optional): Version constraint for remote packages. Defaults to None.
            force_download (bool, optional): Force download even if package is cached. When True, 
                bypass the package cache and download directly from the source. Defaults to False.
            refresh_registry (bool, optional): Force refresh of registry data. When True, 
                fetch the latest registry data before resolving dependencies. Defaults to False.
            auto_approve (bool, optional): Skip user consent prompt for automation scenarios. Defaults to False.
            
        Returns:
            bool: True if successful, False otherwise.
        """        
        env_name = env_name or self._current_env_name
        
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        
        # Refresh registry if requested
        if refresh_registry:
            self.refresh_registry(force_refresh=True)
        
        try:
            # Get currently installed packages for filtering
            existing_packages = {}
            for pkg in self._environments[env_name].get("packages", []):
                existing_packages[pkg["name"]] = pkg["version"]
            
            # Delegate installation to orchestrator
            success, installed_packages = self.dependency_orchestrator.install_dependencies(
                package_path_or_name=package_path_or_name,
                env_path=self.get_environment_path(env_name),
                env_name=env_name,
                existing_packages=existing_packages,
                version_constraint=version_constraint,
                force_download=force_download,
                auto_approve=auto_approve
            )
            
            if success:
                # Update environment metadata with installed Hatch packages
                for pkg_info in installed_packages:
                    if pkg_info["type"] == "hatch":
                        self._add_package_to_env_data(
                            env_name=env_name,
                            package_name=pkg_info["name"],
                            package_version=pkg_info["version"],
                            package_type=pkg_info["type"],
                            source=pkg_info["source"]
                        )
                
                self.logger.info(f"Successfully installed {len(installed_packages)} packages to environment {env_name}")
                return True
            else:
                self.logger.info("Package installation was cancelled or failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add package to environment: {e}")
            return False

    def _add_package_to_env_data(self, env_name: str, package_name: str, 
                               package_version: str, package_type: str, 
                               source: str) -> None:
        """Update environment data with package information."""
        if env_name not in self._environments:
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        # Check if package already exists
        for i, pkg in enumerate(self._environments[env_name].get("packages", [])):
            if pkg.get("name") == package_name:
                # Replace existing package entry
                self._environments[env_name]["packages"][i] = {
                    "name": package_name,
                    "version": package_version,
                    "type": package_type,
                    "source": source,
                    "installed_at": datetime.datetime.now().isoformat()
                }
                self._save_environments()
                return
        
        # if it doesn't exist add new package entry
        self._environments[env_name]["packages"] += [{
            "name": package_name,
            "version": package_version,
            "type": package_type,
            "source": source,
            "installed_at": datetime.datetime.now().isoformat()
        }]

        self._save_environments()

    def update_package_host_configuration(self, env_name: str, package_name: str,
                                        hostname: str, server_config: dict) -> bool:
        """Update package metadata with host configuration tracking.

        Enforces constraint: Only one environment can control a package-host combination.
        Automatically cleans up conflicting configurations from other environments.

        Args:
            env_name (str): Environment name
            package_name (str): Package name
            hostname (str): Host identifier (e.g., 'gemini', 'claude-desktop')
            server_config (dict): Server configuration data

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            if env_name not in self._environments:
                self.logger.error(f"Environment {env_name} does not exist")
                return False

            # Step 1: Clean up conflicting configurations from other environments
            conflicts_removed = self._cleanup_package_host_conflicts(
                target_env=env_name,
                package_name=package_name,
                hostname=hostname
            )

            # Step 2: Update target environment configuration
            success = self._update_target_environment_configuration(
                env_name, package_name, hostname, server_config
            )

            # Step 3: User notification for conflict resolution
            if conflicts_removed > 0 and success:
                self.logger.warning(
                    f"Package '{package_name}' host configuration for '{hostname}' "
                    f"transferred from {conflicts_removed} other environment(s) to '{env_name}'"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to update package host configuration: {e}")
            return False

    def _cleanup_package_host_conflicts(self, target_env: str, package_name: str, hostname: str) -> int:
        """Remove conflicting package-host configurations from other environments.

        This method enforces the constraint that only one environment can control
        a package-host combination by removing conflicting configurations from
        all environments except the target environment.

        Args:
            target_env (str): Environment that should control the configuration
            package_name (str): Package name
            hostname (str): Host identifier

        Returns:
            int: Number of conflicting configurations removed
        """
        conflicts_removed = 0

        for env_name, env_data in self._environments.items():
            if env_name == target_env:
                continue  # Skip target environment

            packages = env_data.get("packages", [])
            for i, pkg in enumerate(packages):
                if pkg.get("name") == package_name:
                    configured_hosts = pkg.get("configured_hosts", {})
                    if hostname in configured_hosts:
                        # Remove the conflicting host configuration
                        del configured_hosts[hostname]
                        conflicts_removed += 1

                        # Update package metadata
                        pkg["configured_hosts"] = configured_hosts
                        self._environments[env_name]["packages"][i] = pkg

                        self.logger.info(
                            f"Removed conflicting '{hostname}' configuration for package '{package_name}' "
                            f"from environment '{env_name}'"
                        )

        if conflicts_removed > 0:
            self._save_environments()

        return conflicts_removed

    def _update_target_environment_configuration(self, env_name: str, package_name: str,
                                               hostname: str, server_config: dict) -> bool:
        """Update the target environment's package host configuration.

        This method handles the actual configuration update for the target environment
        after conflicts have been cleaned up.

        Args:
            env_name (str): Environment name
            package_name (str): Package name
            hostname (str): Host identifier
            server_config (dict): Server configuration data

        Returns:
            bool: True if update successful, False otherwise
        """
        # Find the package in the environment
        packages = self._environments[env_name].get("packages", [])
        for i, pkg in enumerate(packages):
            if pkg.get("name") == package_name:
                # Initialize configured_hosts if it doesn't exist
                if "configured_hosts" not in pkg:
                    pkg["configured_hosts"] = {}

                # Add or update host configuration
                from datetime import datetime
                pkg["configured_hosts"][hostname] = {
                    "config_path": self._get_host_config_path(hostname),
                    "configured_at": datetime.now().isoformat(),
                    "last_synced": datetime.now().isoformat(),
                    "server_config": server_config
                }

                # Update the package in the environment
                self._environments[env_name]["packages"][i] = pkg
                self._save_environments()

                self.logger.info(f"Updated host configuration for package {package_name} on {hostname}")
                return True

        self.logger.error(f"Package {package_name} not found in environment {env_name}")
        return False

    def remove_package_host_configuration(self, env_name: str, package_name: str, hostname: str) -> bool:
        """Remove host configuration tracking for a specific package.

        Args:
            env_name: Environment name
            package_name: Package name (maps to server name in current 1:1 design)
            hostname: Host identifier to remove

        Returns:
            bool: True if removal occurred, False if package/host not found
        """
        try:
            if env_name not in self._environments:
                self.logger.warning(f"Environment {env_name} does not exist")
                return False

            packages = self._environments[env_name].get("packages", [])
            for pkg in packages:
                if pkg.get("name") == package_name:
                    configured_hosts = pkg.get("configured_hosts", {})
                    if hostname in configured_hosts:
                        del configured_hosts[hostname]
                        self._save_environments()
                        self.logger.info(f"Removed host {hostname} from package {package_name} in env {env_name}")
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to remove package host configuration: {e}")
            return False

    def clear_host_from_all_packages_all_envs(self, hostname: str) -> int:
        """Remove host from all packages across all environments.

        Args:
            hostname: Host identifier to remove globally

        Returns:
            int: Number of package entries updated
        """
        updates_count = 0

        try:
            for env_name, env_data in self._environments.items():
                packages = env_data.get("packages", [])
                for pkg in packages:
                    configured_hosts = pkg.get("configured_hosts", {})
                    if hostname in configured_hosts:
                        del configured_hosts[hostname]
                        updates_count += 1
                        self.logger.info(f"Removed host {hostname} from package {pkg.get('name')} in env {env_name}")

            if updates_count > 0:
                self._save_environments()

            return updates_count

        except Exception as e:
            self.logger.error(f"Failed to clear host from all packages: {e}")
            return 0

    def apply_restored_host_configuration_to_environments(self, hostname: str, restored_servers: Dict[str, MCPServerConfig]) -> int:
        """Update environment tracking to match restored host configuration.

        Args:
            hostname: Host that was restored
            restored_servers: Dict mapping server_name -> server_config from restored host file

        Returns:
            int: Number of package entries updated across all environments
        """
        updates_count = 0

        try:
            from datetime import datetime
            current_time = datetime.now().isoformat()

            for env_name, env_data in self._environments.items():
                packages = env_data.get("packages", [])
                for pkg in packages:
                    package_name = pkg.get("name")
                    configured_hosts = pkg.get("configured_hosts", {})

                    # Check if this package corresponds to a restored server
                    if package_name in restored_servers:
                        # Server exists in restored config - ensure tracking exists and is current
                        server_config = restored_servers[package_name]
                        configured_hosts[hostname] = {
                            "config_path": self._get_host_config_path(hostname),
                            "configured_at": configured_hosts.get(hostname, {}).get("configured_at", current_time),
                            "last_synced": current_time,
                            "server_config": server_config.model_dump(exclude_none=True)
                        }
                        updates_count += 1
                        self.logger.info(f"Updated host {hostname} tracking for package {package_name} in env {env_name}")

                    elif hostname in configured_hosts:
                        # Server not in restored config but was previously tracked - remove stale tracking
                        del configured_hosts[hostname]
                        updates_count += 1
                        self.logger.info(f"Removed stale host {hostname} tracking for package {package_name} in env {env_name}")

            if updates_count > 0:
                self._save_environments()

            return updates_count

        except Exception as e:
            self.logger.error(f"Failed to apply restored host configuration: {e}")
            return 0

    def _get_host_config_path(self, hostname: str) -> str:
        """Get configuration file path for a host.

        Args:
            hostname (str): Host identifier

        Returns:
            str: Configuration file path
        """
        # Map hostnames to their typical config paths
        host_config_paths = {
            'gemini': '~/.gemini/settings.json',
            'claude-desktop': '~/.claude/claude_desktop_config.json',
            'claude-code': '.claude/mcp_config.json',
            'vscode': '.vscode/settings.json',
            'cursor': '~/.cursor/mcp.json',
            'lmstudio': '~/.lmstudio/mcp.json'
        }

        return host_config_paths.get(hostname, f'~/.{hostname}/config.json')

    def get_environment_path(self, env_name: str) -> Path:
        """
        Get the path to the environment directory.
        
        Args:
            env_name: Name of the environment
            
        Returns:
            Path: Path to the environment directory
            
        Raises:
            HatchEnvironmentError: If environment doesn't exist
        """
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        env_path = self.environments_dir / env_name
        env_path.mkdir(exist_ok=True)
        return env_path
    
    def list_packages(self, env_name: Optional[str] = None) -> List[Dict]:
        """
        List all packages installed in an environment.
        
        Args:
            env_name: Name of the environment (uses current if None)
            
        Returns:
            List[Dict]: List of package information dictionaries
            
        Raises:
            HatchEnvironmentError: If environment doesn't exist
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        packages = []
        for pkg in self._environments[env_name].get("packages", []):
            # Add full package info including paths
            pkg_info = pkg.copy()
            pkg_info["path"] = str(self.get_environment_path(env_name) / pkg["name"])
            # Check if the package is Hatch compliant (has hatch_metadata.json)
            pkg_path = self.get_environment_path(env_name) / pkg["name"]
            pkg_info["hatch_compliant"] = (pkg_path / "hatch_metadata.json").exists()
            
            # Add source information
            pkg_info["source"] = {
                "uri": pkg.get("source", "unknown"),
                "path": str(pkg_path)
            }
            
            packages.append(pkg_info)
        
        return packages
    
    def remove_package(self, package_name: str, env_name: Optional[str] = None) -> bool:
        """
        Remove a package from an environment.

        Args:
            package_name: Name of the package to remove
            env_name: Environment to remove from (uses current if None)

        Returns:
            bool: True if successful, False otherwise
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False

        # Check if package exists in environment
        env_packages = self._environments[env_name].get("packages", [])
        pkg_index = None
        package_to_remove = None
        for i, pkg in enumerate(env_packages):
            if pkg.get("name") == package_name:
                pkg_index = i
                package_to_remove = pkg
                break

        if pkg_index is None:
            self.logger.warning(f"Package {package_name} not found in environment {env_name}")
            return False

        # Clean up MCP server configurations from all configured hosts
        configured_hosts = package_to_remove.get("configured_hosts", {})
        if configured_hosts:
            self.logger.info(f"Cleaning up MCP server configurations for package {package_name}")
            try:
                from .mcp_host_config.host_management import MCPHostConfigurationManager
                mcp_manager = MCPHostConfigurationManager()

                for hostname in configured_hosts.keys():
                    try:
                        # Remove server from host configuration file
                        result = mcp_manager.remove_server(
                            server_name=package_name,  # In current 1:1 design, package name = server name
                            hostname=hostname,
                            no_backup=False  # Create backup for safety
                        )

                        if result.success:
                            self.logger.info(f"Removed MCP server '{package_name}' from host '{hostname}'")
                        else:
                            self.logger.warning(f"Failed to remove MCP server '{package_name}' from host '{hostname}': {result.error_message}")
                    except Exception as e:
                        self.logger.warning(f"Error removing MCP server '{package_name}' from host '{hostname}': {e}")

            except ImportError:
                self.logger.warning("MCP host configuration manager not available for cleanup")
            except Exception as e:
                self.logger.warning(f"Error during MCP server cleanup: {e}")

        # Remove package from filesystem
        pkg_path = self.get_environment_path(env_name) / package_name
        try:
            import shutil
            if pkg_path.exists():
                shutil.rmtree(pkg_path)
        except Exception as e:
            self.logger.error(f"Failed to remove package files for {package_name}: {e}")
            return False

        # Remove package from environment data
        env_packages.pop(pkg_index)
        self._save_environments()

        self.logger.info(f"Removed package {package_name} from environment {env_name}")
        return True

    def get_servers_entry_points(self, env_name: Optional[str] = None) -> List[str]:
        """
        Get the list of entry points for the MCP servers of each package in an environment.
        
        Args:
            env_name: Environment to get servers from (uses current if None)
            
        Returns:
            List[str]: List of server entry points
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        ep = []
        for pkg in self._environments[env_name].get("packages", []):
            # Open the package's metadata file
            with open(self.environments_dir / env_name / pkg["name"] / "hatch_metadata.json", 'r') as f:
                hatch_metadata = json.load(f)

            package_service = PackageService(hatch_metadata)

            # retrieve entry points
            ep += [(self.environments_dir / env_name / pkg["name"] / package_service.get_hatch_mcp_entry_point()).resolve()]

        return ep

    def refresh_registry(self, force_refresh: bool = True) -> None:
        """Refresh the registry data from the source.
        
        This method forces a refresh of the registry data to ensure the environment manager
        has the most recent package information available. After refreshing, it updates the
        orchestrator and associated services to use the new registry data.
        
        Args:
            force_refresh (bool, optional): Force refresh the registry even if cache is valid.
                When True, bypasses all caching mechanisms and fetches directly from source.
                Defaults to True.
                
        Raises:
            Exception: If fetching the registry data fails for any reason.
        """
        self.logger.info("Refreshing registry data...")
        try:
            self.registry_data = self.retriever.get_registry(force_refresh=force_refresh)
            # Update registry service with new registry data
            self.registry_service = RegistryService(self.registry_data)
            
            # Update orchestrator with new registry data
            self.dependency_orchestrator.registry_service = self.registry_service
            self.dependency_orchestrator.registry_data = self.registry_data
            
            self.logger.info("Registry data refreshed successfully")
        except Exception as e:
            self.logger.error(f"Failed to refresh registry data: {e}")
            raise
    
    def is_python_environment_available(self) -> bool:
        """Check if Python environment management is available.
        
        Returns:
            bool: True if conda/mamba is available, False otherwise.
        """
        return self.python_env_manager.is_available()
    
    def get_python_environment_info(self, env_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get comprehensive Python environment information for an environment.
        
        Args:
            env_name (str, optional): Environment name. Defaults to current environment.
            
        Returns:
            dict: Comprehensive Python environment info, None if no Python environment exists.
            
        Raises:
            HatchEnvironmentError: If no environment name provided and no current environment set.
        """
        if env_name is None:
            env_name = self.get_current_environment()
            if not env_name:
                raise HatchEnvironmentError("No environment name provided and no current environment set")
        
        if env_name not in self._environments:
            return None
            
        env_data = self._environments[env_name]
        
        # Check if Python environment exists
        if not env_data.get("python_environment", False):
            return None
        
        # Start with enhanced metadata from Hatch environment
        python_env_data = env_data.get("python_env", {})
        
        # Get real-time information from Python environment manager
        live_info = self.python_env_manager.get_environment_info(env_name)
        
        # Combine metadata with live information
        result = {
            # Basic identification
            "environment_name": env_name,
            "enabled": python_env_data.get("enabled", True),
            
            # Conda/mamba information
            "conda_env_name": python_env_data.get("conda_env_name") or (live_info.get("conda_env_name") if live_info else None),
            "manager": python_env_data.get("manager", "conda"),
            
            # Python executable and version
            "python_executable": live_info.get("python_executable") if live_info else python_env_data.get("python_executable"),
            "python_version": live_info.get("python_version") if live_info else python_env_data.get("version"),
            "requested_version": python_env_data.get("requested_version"),
            
            # Paths and timestamps
            "environment_path": live_info.get("environment_path") if live_info else None,
            "created_at": python_env_data.get("created_at"),
            
            # Package information
            "package_count": live_info.get("package_count", 0) if live_info else 0,
            "packages": live_info.get("packages", []) if live_info else [],
            
            # Status information
            "exists": live_info is not None,
            "accessible": live_info.get("python_executable") is not None if live_info else False
        }
        
        return result
    
    def list_python_environments(self) -> List[str]:
        """List all environments that have Python environments.
        
        Returns:
            list: List of environment names with Python environments.
        """
        return self.python_env_manager.list_environments()
    
    def create_python_environment_only(self, env_name: Optional[str] = None, python_version: Optional[str] = None, 
                                      force: bool = False, no_hatch_mcp_server: bool = False,
                                      hatch_mcp_server_tag: Optional[str] = None) -> bool:
        """Create only a Python environment without creating a Hatch environment.
        
        Useful for adding Python environments to existing Hatch environments.
        
        Args:
            env_name (str, optional): Environment name. Defaults to current environment.
            python_version (str, optional): Python version (e.g., "3.11"). Defaults to None.
            force (bool, optional): Whether to recreate if exists. Defaults to False.
            no_hatch_mcp_server (bool, optional): Whether to skip installing hatch_mcp_server wrapper in the environment. Defaults to False.
            hatch_mcp_server_tag (str, optional): Git tag/branch reference for hatch_mcp_server wrapper installation. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            HatchEnvironmentError: If no environment name provided and no current environment set.
        """
        if env_name is None:
            env_name = self.get_current_environment()
            if not env_name:
                raise HatchEnvironmentError("No environment name provided and no current environment set")
        
        if env_name not in self._environments:
            self.logger.error(f"Hatch environment {env_name} must exist first")
            return False
        
        try:
            success = self.python_env_manager.create_python_environment(
                env_name, python_version=python_version, force=force
            )
            
            if success:
                # Get detailed Python environment information
                python_info = self.python_env_manager.get_environment_info(env_name)
                if python_info:
                    python_env_info = {
                        "enabled": True,
                        "conda_env_name": python_info.get("conda_env_name"),
                        "python_executable": python_info.get("python_executable"),
                        "created_at": datetime.datetime.now().isoformat(),
                        "version": python_info.get("python_version"),
                        "requested_version": python_version,
                        "manager": python_info.get("manager", "conda")
                    }
                else:
                    # Fallback if detailed info is not available
                    python_env_info = {
                        "enabled": True,
                        "conda_env_name": f"hatch-{env_name}",
                        "python_executable": None,
                        "created_at": datetime.datetime.now().isoformat(),
                        "version": None,
                        "requested_version": python_version,
                        "manager": "conda"
                    }
                
                # Update environment metadata with enhanced structure
                self._environments[env_name]["python_environment"] = True  # Legacy field
                self._environments[env_name]["python_env"] = python_env_info  # Enhanced structure
                if python_version:
                    self._environments[env_name]["python_version"] = python_version  # Legacy field
                self._save_environments()
                
                # Reconfigure Python executable if this is the current environment
                if env_name == self._current_env_name:
                    self._configure_python_executable(env_name)
                
                # Install hatch_mcp_server by default unless opted out
                if not no_hatch_mcp_server:
                    try:
                        self._install_hatch_mcp_server(env_name, hatch_mcp_server_tag)
                    except Exception as e:
                        self.logger.warning(f"Failed to install hatch_mcp_server wrapper in environment {env_name}: {e}")
                        # Don't fail environment creation if MCP wrapper installation fails
            
            return success
        except PythonEnvironmentError as e:
            self.logger.error(f"Failed to create Python environment: {e}")
            return False
    
    def remove_python_environment_only(self, env_name: Optional[str] = None) -> bool:
        """Remove only the Python environment, keeping the Hatch environment.
        
        Args:
            env_name (str, optional): Environment name. Defaults to current environment.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            HatchEnvironmentError: If no environment name provided and no current environment set.
        """
        if env_name is None:
            env_name = self.get_current_environment()
            if not env_name:
                raise HatchEnvironmentError("No environment name provided and no current environment set")
        
        if env_name not in self._environments:
            self.logger.warning(f"Hatch environment {env_name} does not exist")
            return False
        
        try:
            success = self.python_env_manager.remove_python_environment(env_name)
            
            if success:
                # Update environment metadata - remove Python environment info
                self._environments[env_name]["python_environment"] = False  # Legacy field
                self._environments[env_name]["python_env"] = None  # Enhanced structure
                self._environments[env_name].pop("python_version", None)  # Legacy field cleanup
                self._save_environments()
                
                # Reconfigure Python executable if this is the current environment
                if env_name == self._current_env_name:
                    self._configure_python_executable(env_name)
            
            return success
        except PythonEnvironmentError as e:
            self.logger.error(f"Failed to remove Python environment: {e}")
            return False
    
    def get_python_environment_diagnostics(self, env_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get detailed diagnostics for a Python environment.
        
        Args:
            env_name (str, optional): Environment name. Defaults to current environment.
            
        Returns:
            dict: Diagnostics information or None if environment doesn't exist.
            
        Raises:
            HatchEnvironmentError: If no environment name provided and no current environment set.
        """
        if env_name is None:
            env_name = self.get_current_environment()
            if not env_name:
                raise HatchEnvironmentError("No environment name provided and no current environment set")
        
        if env_name not in self._environments:
            return None
            
        try:
            return self.python_env_manager.get_environment_diagnostics(env_name)
        except PythonEnvironmentError as e:
            self.logger.error(f"Failed to get diagnostics for {env_name}: {e}")
            return None
    
    def get_python_manager_diagnostics(self) -> Dict[str, Any]:
        """Get general diagnostics for the Python environment manager.
        
        Returns:
            dict: General diagnostics information.
        """
        try:
            return self.python_env_manager.get_manager_diagnostics()
        except Exception as e:
            self.logger.error(f"Failed to get manager diagnostics: {e}")
            return {"error": str(e)}
    
    def launch_python_shell(self, env_name: Optional[str] = None, cmd: Optional[str] = None) -> bool:
        """Launch a Python shell or execute a command in the environment.
        
        Args:
            env_name (str, optional): Environment name. Defaults to current environment.
            cmd (str, optional): Command to execute. If None, launches interactive shell. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
            
        Raises:
            HatchEnvironmentError: If no environment name provided and no current environment set.
        """
        if env_name is None:
            env_name = self.get_current_environment()
            if not env_name:
                raise HatchEnvironmentError("No environment name provided and no current environment set")
        
        if env_name not in self._environments:
            self.logger.error(f"Environment {env_name} does not exist")
            return False
            
        if not self._environments[env_name].get("python_environment", False):
            self.logger.error(f"No Python environment configured for {env_name}")
            return False
            
        try:
            return self.python_env_manager.launch_shell(env_name, cmd)
        except PythonEnvironmentError as e:
            self.logger.error(f"Failed to launch shell for {env_name}: {e}")
            return False