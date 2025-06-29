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
from .registry_retriever import RegistryRetriever
from .package_loader import HatchPackageLoader
from .installers.dependency_installation_orchestrator import DependencyInstallerOrchestrator
from .python_environment_manager import PythonEnvironmentManager, PythonEnvironmentError

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
        
        # Initialize files if they don't exist
        if not self.environments_file.exists():
            self._initialize_environments_file()
        
        if not self.current_env_file.exists():
            self._initialize_current_env_file()

        # Load environments into cache
        self._environments = self._load_environments()
        self._current_env_name = self._load_current_env_name()
        
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
        
        # Configure Python executable for current environment
        if self._current_env_name:
            self._configure_python_executable(self._current_env_name)

    def _initialize_environments_file(self):
        """Create the initial environments file with default environment."""
        default_environments = {
            "default": {
                "name": "default",
                "description": "Default environment",
                "created_at": datetime.datetime.now().isoformat(),
                "packages": [],
                "python_environment": False,  # Legacy field
                "python_version": None,  # Legacy field
                "python_env": None  # Enhanced metadata structure
            }
        }
        
        with open(self.environments_file, 'w') as f:
            json.dump(default_environments, f, indent=2)
        
        self.logger.info("Initialized environments file with default environment")
    
    def _initialize_current_env_file(self):
        """Create the current environment file pointing to the default environment."""
        with open(self.current_env_file, 'w') as f:
            f.write("default")
        
        self.logger.info("Initialized current environment to default")
    
    def _load_environments(self) -> Dict:
        """Load environments from the environments file."""
        try:
            with open(self.environments_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Failed to load environments: {e}")
            self._initialize_environments_file()
            return {"default": {"name": "default", "description": "Default environment", 
                    "created_at": datetime.datetime.now().isoformat(), "packages": []}}
    
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
            self.dependency_orchestrator.set_python_executable(python_executable)
            self.logger.info(f"Configured Python executable for {env_name}: {python_executable}")
        else:
            # Use system Python as fallback
            system_python = sys.executable
            self.dependency_orchestrator.set_python_executable(system_python)
            self.logger.info(f"Using system Python for {env_name}: {system_python}")
    
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
                          create_python_env: bool = True) -> bool:
        """
        Create a new environment.
        
        Args:
            name: Name of the environment
            description: Description of the environment
            python_version: Python version for the environment (e.g., "3.11", "3.12")
            create_python_env: Whether to create a Python environment using conda/mamba
            
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
                            "conda_env_name": f"hatch-{name}",
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
        return True
    
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
        
        # Remove Python environment if it exists
        env_data = self._environments[name]
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
        for i, pkg in enumerate(env_packages):
            if pkg.get("name") == package_name:
                pkg_index = i
                break
        
        if pkg_index is None:
            self.logger.warning(f"Package {package_name} not found in environment {env_name}")
            return False
        
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

            # retrieve entry points
            ep += [(self.environments_dir / env_name / pkg["name"] / hatch_metadata.get("entry_point")).resolve()]

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
    
    def get_python_environment_info(self, env_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive Python environment information for an environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            dict: Comprehensive Python environment info, None if no Python environment exists.
        """
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
    
    def create_python_environment_only(self, env_name: str, python_version: Optional[str] = None, 
                                      force: bool = False) -> bool:
        """Create only a Python environment without creating a Hatch environment.
        
        Useful for adding Python environments to existing Hatch environments.
        
        Args:
            env_name (str): Environment name.
            python_version (str, optional): Python version (e.g., "3.11").
            force (bool, optional): Whether to recreate if exists.
            
        Returns:
            bool: True if successful, False otherwise.
        """
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
            
            return success
        except PythonEnvironmentError as e:
            self.logger.error(f"Failed to create Python environment: {e}")
            return False
    
    def remove_python_environment_only(self, env_name: str) -> bool:
        """Remove only the Python environment, keeping the Hatch environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            bool: True if successful, False otherwise.
        """
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
    
    def get_python_environment_diagnostics(self, env_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed diagnostics for a Python environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            dict: Diagnostics information or None if environment doesn't exist.
        """
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
    
    def launch_python_shell(self, env_name: str, cmd: Optional[str] = None) -> bool:
        """Launch a Python shell or execute a command in the environment.
        
        Args:
            env_name (str): Environment name.
            cmd (str, optional): Command to execute. If None, launches interactive shell.
            
        Returns:
            bool: True if successful, False otherwise.
        """
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