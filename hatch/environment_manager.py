"""Environment Manager for Hatch package system.

This module provides the core functionality for managing isolated environments
for Hatch packages.
"""
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from hatch_validator import HatchPackageValidator
from .registry_retriever import RegistryRetriever
from .package_loader import HatchPackageLoader, PackageLoaderError
from .registry_explorer import find_package, find_package_version, get_package_release_url
from .python_dependency_manager import PythonDependencyManager, PythonDependencyError


class HatchEnvironmentError(Exception):
    """Exception raised for environment-related errors."""
    pass


class HatchEnvironmentManager:
    """Manages Hatch environments for package installation and isolation.
    
    This class handles:
    1. Creating and managing isolated environments
    2. Adding packages to environments
    3. Resolving and managing dependencies using a DependencyResolver
    4. Installing packages with the HatchPackageLoader
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
          # Initialize dependencies
        self.package_loader = HatchPackageLoader(cache_dir=cache_dir)
        self.python_dependency_manager = PythonDependencyManager(self.environments_dir)

        # Get dependency resolver from imported module
        self.retriever = RegistryRetriever(cache_ttl=cache_ttl,
                                      local_cache_dir=cache_dir,
                                      simulation_mode=simulation_mode,
                                      local_registry_cache_path=local_registry_cache_path)
        self.registry_data = self.retriever.get_registry()
        self.package_validator = HatchPackageValidator(registry_data=self.registry_data)
        self.dependency_resolver = self.package_validator.dependency_resolver

    def _initialize_environments_file(self):
        """Create the initial environments file with default environment."""
        default_environments = {
            "default": {
                "name": "default",
                "description": "Default environment",
                "created_at": datetime.datetime.now().isoformat(),
                "packages": []
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
            
            self.logger.info(f"Current environment set to: {env_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set current environment: {e}")
            return False
    
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
    def create_environment(self, name: str, description: str = "") -> bool:
        """Create a new environment.
        
        Args:
            name (str): Name of the environment.
            description (str): Description of the environment.
            
        Returns:
            bool: True if created successfully, False if environment already exists.
        """
        # Allow alphanumeric characters and underscores
        if not name or not all(c.isalnum() or c == '_' for c in name):
            self.logger.error("Environment name must be alphanumeric or underscore")
            return False
        
        # Check if environment already exists
        if name in self._environments:
            self.logger.warning(f"Environment already exists: {name}")
            return False
        
        # Create new environment
        self._environments[name] = {
            "name": name,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "packages": []
        }
        
        # Create virtual environment for Python dependencies
        try:
            self.python_dependency_manager.create_virtual_environment(name)
            self.logger.info(f"Created Python virtual environment for: {name}")
        except PythonDependencyError as e:
            self.logger.warning(f"Failed to create virtual environment for {name}: {e}")
            # Continue with environment creation even if venv creation fails
        
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
                                  skip_python_deps: bool = False,
                                  upgrade_python_deps: bool = False,
                                  python_interpreter: Optional[str] = None) -> bool:        
        """Add a package to an environment.
        
        This complex method handles the process of adding either a local or remote package 
        to an environment, including dependency resolution and installation. It performs 
        the following steps:
        1. Determines if the package is local or remote
        2. Gets package metadata and dependencies
        3. Checks for circular dependencies
        4. Installs missing dependencies 
        5. Installs the main package
        
        Args:
            package_path_or_name (str): Path to local package or name of remote package.
            env_name (str, optional): Environment to add to. Defaults to current environment.
            version_constraint (str, optional): Version constraint for remote packages. Defaults to None.
            force_download (bool, optional): Force download even if package is cached. When True, 
                bypass the package cache and download directly from the source. Defaults to False.
            refresh_registry (bool, optional): Force refresh of registry data. When True, 
                fetch the latest registry data before resolving dependencies. Defaults to False.
            skip_python_deps (bool, optional): Skip installation of Python dependencies. Defaults to False.
            upgrade_python_deps (bool, optional): Upgrade existing Python dependencies. Defaults to False.
            python_interpreter (str, optional): Specify which Python interpreter to use. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        
        # Refresh registry if requested or if force_download is specified
        if refresh_registry or force_download:
            self.refresh_registry(force_refresh=True)
            
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        # Check if package is local or remote
        package_path = Path(package_path_or_name)
        is_local_package = package_path.exists() and package_path.is_dir()

        local_deps, remote_deps = [], []
        if is_local_package:
            # Get the hatch_dependencies from the local pkg's metadata
            with open(package_path / "hatch_metadata.json", 'r') as f:
                hatch_metadata = json.load(f)
            package_name = hatch_metadata.get("name", Path(package_path).name)
            package_version = hatch_metadata.get("version", "0.0.0")
            hatch_dependencies = hatch_metadata.get("hatch_dependencies", [])
            local_deps, remote_deps = self._get_deps_from_all_local_packages(hatch_dependencies)

        else:
            # For remote packages, there can only be remote dependencies
            package_name = package_path_or_name
            if not version_constraint:
                # Find package in registry data
                package_registry_data = find_package(self.registry_data, package_name)
                if not package_registry_data:
                    self.logger.error(f"Package {package_name} not found in registry")
                    return False
                # Find the information about the package version    
                package_version_data = find_package_version(package_registry_data, version_constraint)
                if not package_version_data:
                    self.logger.error(f"Package {package_name} with version constraint {version_constraint} not found in registry")
                    return False
                else:
                    package_version = package_version_data.get("version")

            remote_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                package_name, package_version).get("dependencies", [])
                
        # and the package we're trying to install
        current_dependencies = []
        
        # Get currently installed packages
        installed_packages = {}
        for pkg in self._environments[env_name].get("packages", []):
            installed_packages[pkg["name"]] = pkg["version"]
            
            # For each installed package, get its dependencies to build the dependency graph
            if pkg["type"] == "local":
                # For local packages, use metadata file to get dependencies
                pkg_install_path = self.get_environment_path(env_name) / pkg["name"]
                if (pkg_install_path / "hatch_metadata.json").exists():
                    with open(pkg_install_path / "hatch_metadata.json", 'r') as f:
                        pkg_metadata = json.load(f)
                    pkg_deps = pkg_metadata.get("hatch_dependencies", [])
                    
                    # Transform the dependencies to correct format
                    processed_deps = []
                    for dep in pkg_deps:
                        if dep.get("name"):  # Make sure the dependency has a name
                            processed_deps.append(dep.get("name"))
                    
                    current_dependencies.append({"name": pkg["name"], "dependencies": processed_deps})
            else:
                # For remote packages, use the registry data
                pkg_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                    pkg["name"], pkg["version"]).get("dependencies", [])
                
                # Transform the dependencies to correct format
                processed_deps = []
                for dep in pkg_deps:
                    if dep.get("name"):  # Make sure the dependency has a name
                        processed_deps.append(dep.get("name"))
                
                current_dependencies.append({"name": pkg["name"], "dependencies": processed_deps})
        
        # Add the new package to check if it would create a circular dependency
        if is_local_package:
            hatch_deps = hatch_metadata.get("hatch_dependencies", [])
            processed_deps = []
            for dep in hatch_deps:
                if dep.get("name"):  # Make sure the dependency has a name
                    processed_deps.append(dep.get("name"))
                    
            current_dependencies.append({
                "name": package_name,
                "dependencies": processed_deps
            })
        else:
            pkg_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                package_name, package_version).get("dependencies", [])
            
            processed_deps = []
            for dep in pkg_deps:
                if dep.get("name"):  # Make sure the dependency has a name
                    processed_deps.append(dep.get("name"))
                    
            current_dependencies.append({
                "name": package_name,
                "dependencies": processed_deps
            })
        
        self.logger.debug(f"Checking for circular dependencies in: {current_dependencies}")
        
        # Check for circular dependencies
        has_cycles, cycles = self.package_validator.dependency_resolver.detect_dependency_cycles(
            current_dependencies)
            
        if has_cycles:
            self.logger.error(f"Circular dependency detected: {cycles}")
            return False

        # Find missing dependencies
        local_missing_deps = self._filter_for_missing_dependencies(local_deps, env_name)
        remote_missing_deps = self._filter_for_missing_dependencies(remote_deps, env_name)

        # Install missing dependencies
        ## Delegate to package loader
        for dep in local_missing_deps:
            try:
                self.package_loader.install_local_package(
                    dep["path"],
                    self.get_environment_path(env_name),
                    dep["name"]
                )
                with open(dep["path"] / "hatch_metadata.json", 'r') as f:
                    hatch_metadata = json.load(f)
                self._add_package_to_env_data(env_name, dep["name"], hatch_metadata.get("version"), "local", "local")
            except PackageLoaderError as e:
                self.logger.error(f"Failed to install local package {dep['name']}: {e}")
                return False
        for dep in remote_missing_deps:
            try:
                # First, download the package to cache
                package_registry_data = find_package(self.registry_data, dep['name'])     
                self.logger.debug(f"Package registry data: {json.dumps(package_registry_data, indent=2)}")
                package_url, package_version = get_package_release_url(package_registry_data, dep["version_constraint"])
                self.package_loader.install_remote_package(package_url,
                                                            dep["name"],
                                                            package_version,
                                                            self.get_environment_path(env_name),
                                                            force_download)
                self._add_package_to_env_data(env_name, dep["name"], package_version, "remote", "registry")
            except PackageLoaderError as e:
                self.logger.error(f"Failed to install remote package {dep['name']}: {e}")
                return False        # Get package metadata before installation to check Python dependencies
        if is_local_package:
            # For local packages, metadata is already available
            with open(package_path / "hatch_metadata.json", 'r') as f:
                package_metadata = json.load(f)
            package_name = package_metadata.get("name", Path(package_path).name)
            package_version = package_metadata.get("version", "0.0.0")
        else:
            # For remote packages, we need to download and extract metadata first
            package_registry_data = find_package(self.registry_data, package_path_or_name)
            if not package_registry_data:
                self.logger.error(f"Package {package_path_or_name} not found in registry")
                return False

            package_url, package_version = get_package_release_url(package_registry_data, version_constraint)
            if not package_url:
                self.logger.error(f"Could not find release URL for package {package_path_or_name} with version constraint {version_constraint}")
                return False
            
            # Download and extract package to get metadata (but don't install yet)
            try:
                package_metadata = self.package_loader.get_remote_package_metadata(
                    package_url, package_path_or_name, package_version)
            except PackageLoaderError as e:
                self.logger.error(f"Failed to get metadata for package {package_path_or_name}: {e}")
                return False

        # Install Python dependencies for the main package (if not skipped)
        # This happens BEFORE installing the main Hatch package to ensure dependencies are available
        if not skip_python_deps:
            try:
                # Install Python dependencies using the metadata we just obtained
                if not self.python_dependency_manager.install_python_dependencies(
                    package_metadata, env_name, upgrade_python_deps, python_interpreter):
                    self.logger.error(f"Failed to install Python dependencies for {package_path_or_name}")
                    return False
            except PythonDependencyError as e:
                self.logger.error(f"Python dependency installation failed for {package_path_or_name}: {e}")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error during Python dependency installation for {package_path_or_name}: {e}")
                return False
        else:
            self.logger.info(f"Skipping Python dependency installation for {package_path_or_name} as requested")

        # Now install the main package and add it to environment data
        try:
            if is_local_package:
                # Install the local package
                self.package_loader.install_local_package(
                    package_path,
                    self.get_environment_path(env_name),
                    Path(package_path).name
                )
                self._add_package_to_env_data(env_name, package_name, package_version, "local", "local")
            else:
                # Install the remote package (we already have the URL and version)
                self.package_loader.install_remote_package(
                    package_url,
                    package_path_or_name,
                    package_version,
                    self.get_environment_path(env_name),
                    force_download
                )
                self._add_package_to_env_data(env_name, package_path_or_name, package_version, "remote", "registry")
        except PackageLoaderError as e:
            self.logger.error(f"Failed to install package {package_path_or_name}: {e}")
            return False

        return True

    def _get_deps_from_all_local_packages(self, hatch_dependencies: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Retrieves the local and remote dependencies from the hatch_dependencies list of a package.
        
        This method uses a breadth-first search approach to gather all dependencies,
        separating them into local and remote categories.
        
        Args:
            hatch_dependencies: List of dependencies from the package's metadata.
            
        Returns:
            Tuple[List[Dict], List[str]]: A tuple containing:
                - List of local dependencies with path information
                - List of remote dependencies with version constraints
        """
        deps_queue = hatch_dependencies.copy()
        local_deps = []
        remote_deps_queue = []
        
        while deps_queue:
            dep = deps_queue.pop(0)
            if dep.get("type").get("type") == "local":
                local_deps += [{"name": dep.get("name"), "path": dep.get("type").get("path")}]
                deps_queue += local_deps[-1].get("hatch_dependencies", [])
            else:
                remote_deps_queue.append(dep)

        remote_deps = []
        while remote_deps_queue:
            dep = remote_deps_queue.pop(0)
            remote_deps += [{"name": dep.get("name"), "version_constraint": dep.get("version_constraint")}]
            new_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                dep.get("name"), dep.get("version_constraint"))
            remote_deps_queue += new_deps.get("dependencies", [])

        return local_deps, remote_deps

    def _filter_for_missing_dependencies(self, dependencies: List[Dict], env_name: str) -> List[Dict]:
        """Determine which dependencies are not installed in the environment."""
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        # Get currently installed packages
        installed_packages = {}
        for pkg in self._environments[env_name].get("packages", []):
            installed_packages[pkg["name"]] = pkg["version"]
        
        # Find missing dependencies
        missing_deps = []
        for dep in dependencies:
            dep_name = dep.get("name")
            if dep_name not in installed_packages:
                missing_deps.append(dep)
                continue
            
            # Check version constraints
            constraint = dep.get("version_constraint")
            if constraint and not self.package_validator.dependency_resolver.is_version_compatible(
                    installed_packages[dep_name], constraint):
                missing_deps.append(dep)
        
        return missing_deps
    
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
        associated validators and resolvers to use the new registry data.
        
        The refresh process follows these steps:
        1. Fetch the latest registry data from the configured source
        2. Update the internal registry_data cache
        3. Recreate the package validator with the new data
        4. Update the dependency resolver reference
        
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
            # Update package validator with new registry data
            self.package_validator = HatchPackageValidator(registry_data=self.registry_data)
            self.dependency_resolver = self.package_validator.dependency_resolver
            self.logger.info("Registry data refreshed successfully")
        except Exception as e:
            self.logger.error(f"Failed to refresh registry data: {e}")
            raise