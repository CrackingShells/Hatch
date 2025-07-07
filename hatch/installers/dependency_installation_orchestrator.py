"""Dependency installation orchestrator for coordinating package installation.

This module provides centralized orchestration for all dependency installation
across different dependency types, with centralized user consent management
and delegation to specific installers.
"""

import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from hatch_validator.package.package_service import PackageService
from hatch_validator.registry.registry_service import RegistryService
from hatch_validator.utils.hatch_dependency_graph import HatchDependencyGraphBuilder
from hatch_validator.utils.version_utils import VersionConstraintValidator, VersionConstraintError
from hatch_validator.core.validation_context import ValidationContext

from hatch.package_loader import HatchPackageLoader


# Mandatory to insure the installers are registered in the singleton `installer_registry` correctly at import time
from hatch.installers.hatch_installer import HatchInstaller
from hatch.installers.python_installer import PythonInstaller
from hatch.installers.system_installer import SystemInstaller
from hatch.installers.docker_installer import DockerInstaller

from hatch.installers.registry import installer_registry
from hatch.installers.installer_base import InstallationError
from hatch.installers.installation_context import InstallationContext, InstallationStatus


class DependencyInstallationError(Exception):
    """Exception raised for dependency installation-related errors."""
    pass


class DependencyInstallerOrchestrator:
    """Orchestrates dependency installation across all supported dependency types.
    
    This class coordinates the installation of dependencies by:
    1. Resolving all dependencies for a given package using the validator
    2. Aggregating installation plans across all dependency types
    3. Managing centralized user consent
    4. Delegating to appropriate installers via the registry
    5. Handling installation order and error recovery
    
    The orchestrator strictly uses PackageService for all metadata access to ensure
    compatibility across different package schema versions.
    """

    def __init__(self, 
                 package_loader: HatchPackageLoader,
                 registry_service: RegistryService,
                 registry_data: Dict[str, Any]):
        """Initialize the dependency installation orchestrator.
        
        Args:
            package_loader (HatchPackageLoader): Package loader for file operations.
            registry_service (RegistryService): Service for registry operations.
            registry_data (Dict[str, Any]): Registry data for dependency resolution.
        """
        self.logger = logging.getLogger("hatch.dependency_orchestrator")
        self.package_loader = package_loader
        self.registry_service = registry_service
        self.registry_data = registry_data
        
        # Python executable configuration for context
        self._python_env_vars = Optional[Dict[str, str]]  # Environment variables for Python execution
        
        # These will be set during package resolution
        self.package_service: Optional[PackageService] = None
        self.dependency_graph_builder: Optional[HatchDependencyGraphBuilder] = None
        self._resolved_package_path: Optional[Path] = None
        self._resolved_package_type: Optional[str] = None
        self._resolved_package_location: Optional[str] = None

    def set_python_env_vars(self, python_env_vars: Dict[str, str]) -> None:
        """Set the environment variables for the Python executable.
        
        Args:
            python_env_vars (Dict[str, str]): Environment variables to set for Python execution.
        """
        self._python_env_vars = python_env_vars

    def get_python_env_vars(self) -> Optional[Dict[str, str]]:
        """Get the configured environment variables for the Python executable.

        Returns:
            Dict[str, str]: Environment variables for Python execution, None if not configured.
        """
        return self._python_env_vars

    def install_single_dep(self, dep: Dict[str, Any], context: InstallationContext) -> Dict[str, Any]:
        """Install a single dependency into the specified environment context.

        This method installs a single dependency using the appropriate installer from the registry.
        It extracts the core installation logic from _execute_install_plan for reuse in other contexts.
        This method operates with auto_approve=True and does not require user consent.

        Args:
            dep (Dict[str, Any]): Dependency dictionary following the schema for the dependency type.
                                 For Python dependencies, should include: name, version_constraint, package_manager.
                                 Example: {"name": "numpy", "version_constraint": "*", "package_manager": "pip", "type": "python"}
            context (InstallationContext): Installation context with environment path and configuration.

        Returns:
            Dict[str, Any]: Installed package information containing:
                - name: Package name
                - version: Installed version  
                - type: Dependency type
                - source: Package source URI

        Raises:
            DependencyInstallationError: If installation fails or dependency type is not supported.
        """
        # Ensure dependency has type information
        dep_type = dep.get("type")
        if not dep_type:
            raise DependencyInstallationError(f"Dependency missing 'type' field: {dep}")

        # Check if installer is registered for this dependency type
        if not installer_registry.is_registered(dep_type):
            raise DependencyInstallationError(f"No installer registered for dependency type: {dep_type}")

        installer = installer_registry.get_installer(dep_type)

        try:
            self.logger.info(f"Installing {dep_type} dependency: {dep['name']}")
            result = installer.install(dep, context)
            if result.status == InstallationStatus.COMPLETED:
                installed_package = {
                    "name": dep["name"],
                    "version": dep.get("resolved_version", dep.get("version")),
                    "type": dep_type,
                    "source": dep.get("uri", "unknown")
                }
                self.logger.info(f"Successfully installed {dep_type} dependency: {dep['name']}")
                return installed_package
            else:
                raise DependencyInstallationError(f"Failed to install {dep['name']}: {result.error_message}")

        except InstallationError as e:
            self.logger.error(f"Installation error for {dep_type} dependency {dep['name']}: {e.error_code}\n{e.message}")
            raise DependencyInstallationError(f"Installation error for {dep['name']}: {e}") from e

        except Exception as e:
            self.logger.error(f"Error installing {dep_type} dependency {dep['name']}: {e}")
            raise DependencyInstallationError(f"Error installing {dep['name']}: {e}") from e

    def install_dependencies(self, 
                           package_path_or_name: str,
                           env_path: Path,
                           env_name: str,
                           existing_packages: Dict[str, str],
                           version_constraint: Optional[str] = None,
                           force_download: bool = False,
                           auto_approve: bool = False) -> Tuple[bool, List[Dict[str, Any]]]:
        """Install all dependencies for a package with centralized consent management.

        This method orchestrates the complete dependency installation process by
        leveraging existing validator components and the installer registry. It handles
        all dependency types (hatch, python, system, docker) and provides centralized
        user consent management.
        
        Args:
            package_path_or_name (str): Path to local package or name of remote package.
            env_path (Path): Path to the environment directory.
            env_name (str): Name of the environment.
            existing_packages (Dict[str, str]): Currently installed packages {name: version}.
            version_constraint (str, optional): Version constraint for remote packages. Defaults to None.
            force_download (bool, optional): Force download even if package is cached. Defaults to False.
            auto_approve (bool, optional): Skip user consent prompt for automation. Defaults to False.
            
        Returns:
            Tuple[bool, List[Dict[str, Any]]]: Success status and list of installed packages.
            
        Raises:
            DependencyInstallationError: If installation fails at any stage.
        """
        try:
            # Step 1: Resolve package and load metadata using PackageService
            self._resolve_and_load_package(package_path_or_name, version_constraint, force_download)
            
            # Step 2: Get all dependencies organized by type
            dependencies_by_type = self._get_all_dependencies()
            
            # Step 3: Filter for missing dependencies by type and track satisfied ones
            missing_dependencies_by_type, satisfied_dependencies_by_type = self._filter_missing_dependencies_by_type(dependencies_by_type, existing_packages)
            
            # Step 4: Aggregate installation plan
            install_plan = self._aggregate_install_plan(missing_dependencies_by_type, satisfied_dependencies_by_type)
            
            # Step 5: Print installation summary for user review
            self._print_installation_summary(install_plan)

            # Step 6: Request user consent
            if not auto_approve:
                if not self._request_user_consent(install_plan):
                    self.logger.info("Installation cancelled by user")
                    return False, []
            else:
                self.logger.warning("Auto-approval enabled, proceeding with installation without user consent")
            
            # Step 7: Execute installation plan using installer registry
            installed_packages = self._execute_install_plan(install_plan, env_path, env_name)
            
            return True, installed_packages
            
        except Exception as e:
            self.logger.error(f"Dependency installation failed: {e}")
            raise DependencyInstallationError(f"Installation failed: {e}") from e

    def _resolve_and_load_package(self, 
                                package_path_or_name: str, 
                                version_constraint: Optional[str] = None,
                                force_download: bool = False) -> None:
        """Resolve package information and load metadata using PackageService.
        
        Args:
            package_path_or_name (str): Path to local package or name of remote package.
            version_constraint (str, optional): Version constraint for remote packages.
            force_download (bool, optional): Force download even if package is cached.
            
        Raises:
            DependencyInstallationError: If package cannot be resolved or loaded.
        """
        path = Path(package_path_or_name)
        
        if path.exists() and path.is_dir():
            # Local package
            metadata_path = path / "hatch_metadata.json"
            if not metadata_path.exists():
                raise DependencyInstallationError(f"Local package missing hatch_metadata.json: {path}")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self._resolved_package_path = path
            self._resolved_package_type = "local"
            self._resolved_package_location = str(path.resolve())
            
        else:
            # Remote package
            if not self.registry_service.package_exists(package_path_or_name):
                raise DependencyInstallationError(f"Package {package_path_or_name} does not exist in registry")
            
            try:
                compatible_version = self.registry_service.find_compatible_version(
                    package_path_or_name, version_constraint)
            except VersionConstraintError as e:
                raise DependencyInstallationError(f"Version constraint error: {e}") from e
            
            location = self.registry_service.get_package_uri(package_path_or_name, compatible_version)
            downloaded_path = self.package_loader.download_package(
                location, package_path_or_name, compatible_version, force_download=force_download)
            
            metadata_path = downloaded_path / "hatch_metadata.json"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            self._resolved_package_path = downloaded_path
            self._resolved_package_type = "remote"
            self._resolved_package_location = location
        
        # Load metadata using PackageService for schema-aware access
        self.package_service = PackageService(metadata)
        if not self.package_service.is_loaded():
            raise DependencyInstallationError("Failed to load package metadata")

    def _get_install_ready_hatch_dependencies(self) -> List[Dict[str, Any]]:
        """Get install-ready Hatch dependencies using validator components.
        
        This method only processes Hatch package dependencies, not python, system, or docker.
        
        Returns:
            List[Dict[str, Any]]: List of install-ready Hatch dependencies.
            
        Raises:
            DependencyInstallationError: If dependency resolution fails.
        """
        try:
            # Use validator components for Hatch dependency resolution
            self.dependency_graph_builder = HatchDependencyGraphBuilder(
                self.package_service, self.registry_service)
            
            context = ValidationContext(
                package_dir=self._resolved_package_path,
                registry_data=self.registry_data,
                allow_local_dependencies=True
            )
            
            # This only returns Hatch dependencies in install order
            hatch_dependencies = self.dependency_graph_builder.get_install_ready_dependencies(context)
            return hatch_dependencies
            
        except Exception as e:
            raise DependencyInstallationError(f"Error building Hatch dependency graph: {e}") from e

    def _get_all_dependencies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all dependencies from package metadata organized by type.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dependencies organized by type (hatch, python, system, docker).
            
        Raises:
            DependencyInstallationError: If dependency extraction fails.
        """
        try:
            # Get all dependencies using PackageService
            all_deps = self.package_service.get_dependencies()
            
            dependencies_by_type = {
                "hatch": [],
                "python": [],
                "system": [],
                "docker": []
            }
            
            # Get Hatch dependencies using validator (properly ordered)
            dependencies_by_type["hatch"] = self._get_install_ready_hatch_dependencies()
            # Adding the type information to each Hatch dependency
            for dep in dependencies_by_type["hatch"]:
                dep["type"] = "hatch"
            
            # Get other dependency types directly from PackageService
            for dep_type in ["python", "system", "docker"]:
                raw_deps = all_deps.get(dep_type, [])
                for dep in raw_deps:

                    # Add type information and ensure required fields
                    dep_with_type = dep.copy()
                    dep_with_type["type"] = dep_type
                    if not installer_registry.can_install(dep_type, dep_with_type):
                        raise DependencyInstallationError(
                            f"No registered installer can handle dependency with type '{dep_type}': {dep_with_type}"
                        )

                    dependencies_by_type[dep_type].append(dep_with_type)
            
            return dependencies_by_type
            
        except Exception as e:
            raise DependencyInstallationError(f"Error extracting dependencies: {e}") from e

    def _filter_missing_dependencies_by_type(self, 
                                           dependencies_by_type: Dict[str, List[Dict[str, Any]]], 
                                           existing_packages: Dict[str, str]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]:
        """Filter dependencies by type to find those not already installed and track satisfied ones.
        
        For non-Hatch dependencies, we always include them in missing list as the third-party 
        package manager will handle version checking and installation.
        
        Args:
            dependencies_by_type (Dict[str, List[Dict[str, Any]]]): All dependencies organized by type.
            existing_packages (Dict[str, str]): Currently installed packages {name: version}.
            
        Returns:
            Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[Dict[str, Any]]]]: 
                (missing_dependencies_by_type, satisfied_dependencies_by_type)
        """
        missing_deps_by_type = {}
        satisfied_deps_by_type = {}
        
        for dep_type, dependencies in dependencies_by_type.items():
            missing_deps = []
            satisfied_deps = []
            
            for dep in dependencies:
                dep_name = dep.get("name")
                
                # For non-Hatch dependencies, always consider them as needing installation
                # as the third-party package manager will handle version compatibility
                if dep_type != "hatch":
                    missing_deps.append(dep)
                    continue
                
                # Hatch dependency processing
                if dep_name not in existing_packages:
                    missing_deps.append(dep)
                    continue
                
                # Check version constraints for Hatch dependencies
                constraint = dep.get("version_constraint")
                installed_version = existing_packages[dep_name]
                
                if constraint:
                    is_compatible, compatibility_msg = VersionConstraintValidator.is_version_compatible(
                        installed_version, constraint)
                    if not is_compatible:
                        missing_deps.append(dep)
                    else:
                        # Add satisfied dependency with installation info
                        satisfied_dep = dep.copy()
                        satisfied_dep["installed_version"] = installed_version
                        satisfied_dep["compatibility_status"] = compatibility_msg
                        satisfied_deps.append(satisfied_dep)
                else:
                    # No constraint specified, any installed version satisfies
                    satisfied_dep = dep.copy()
                    satisfied_dep["installed_version"] = installed_version
                    satisfied_dep["compatibility_status"] = "No version constraint specified"
                    satisfied_deps.append(satisfied_dep)
            
            missing_deps_by_type[dep_type] = missing_deps
            satisfied_deps_by_type[dep_type] = satisfied_deps
        
        return missing_deps_by_type, satisfied_deps_by_type

    def _aggregate_install_plan(self, 
                                missing_dependencies_by_type: Dict[str, List[Dict[str, Any]]],
                                satisfied_dependencies_by_type: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Aggregate installation plan across all dependency types.
        
        Args:
            missing_dependencies_by_type (Dict[str, List[Dict[str, Any]]]): Missing dependencies by type.
            satisfied_dependencies_by_type (Dict[str, List[Dict[str, Any]]]): Already satisfied dependencies by type.
            
        Returns:
            Dict[str, Any]: Complete installation plan with dependencies grouped by type.
        """
        # Use PackageService for all metadata access
        plan = {
            "main_package": {
                "name": self.package_service.get_field("name"),
                "version": self.package_service.get_field("version"),
                "type": self._resolved_package_type,
                "location": self._resolved_package_location
            },
            "dependencies_to_install": missing_dependencies_by_type,
            "dependencies_satisfied": satisfied_dependencies_by_type,
            "total_to_install": 1 + sum(len(deps) for deps in missing_dependencies_by_type.values()),
            "total_satisfied": sum(len(deps) for deps in satisfied_dependencies_by_type.values())
        }
        
        return plan
    
    def _print_installation_summary(self, install_plan: Dict[str, Any]) -> None:
        """Print a summary of the installation plan for user review.
        
        Args:
            install_plan (Dict[str, Any]): Complete installation plan.
        """
        print("\n" + "="*60)
        print("DEPENDENCY INSTALLATION PLAN")
        print("="*60)
        
        main_pkg = install_plan['main_package']
        print(f"Main Package: {main_pkg['name']} v{main_pkg['version']}")
        print(f"Package Type: {main_pkg['type']}")
        
        # Show satisfied dependencies first
        total_satisfied = install_plan.get("total_satisfied", 0)
        if total_satisfied > 0:
            print(f"\nDependencies already satisfied: {total_satisfied}")
            
            for dep_type, deps in install_plan.get("dependencies_satisfied", {}).items():
                if deps:
                    print(f"\n{dep_type.title()} Dependencies (Satisfied):")
                    for dep in deps:
                        installed_version = dep.get("installed_version", "unknown")
                        constraint = dep.get("version_constraint", "any")
                        compatibility = dep.get("compatibility_status", "")
                        print(f"  ✓ {dep['name']} {constraint} (installed: {installed_version})")
                        if compatibility and compatibility != "No version constraint specified":
                            print(f"    {compatibility}")
        
        # Show dependencies to install
        total_to_install = sum(len(deps) for deps in install_plan.get("dependencies_to_install", {}).values())
        if total_to_install > 0:
            print(f"\nDependencies to install: {total_to_install}")
            
            for dep_type, deps in install_plan.get("dependencies_to_install", {}).items():
                if deps:
                    print(f"\n{dep_type.title()} Dependencies (To Install):")
                    for dep in deps:
                        constraint = dep.get("version_constraint", "any")
                        print(f"  → {dep['name']} {constraint}")
        else:
            print("\nNo additional dependencies to install.")
        
        print(f"\nTotal packages to install: {install_plan.get('total_to_install', 1)}")
        if total_satisfied > 0:
            print(f"Total dependencies already satisfied: {total_satisfied}")
        print("="*60)

    def _request_user_consent(self, install_plan: Dict[str, Any]) -> bool:
        """Request user consent for the installation plan.
        
        Args:
            install_plan (Dict[str, Any]): Complete installation plan.
            
        Returns:
            bool: True if user approves, False otherwise.
        """        
        # Request confirmation
        while True:
            response = input("\nProceed with installation? [y/N]: ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no', '']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")

    def _execute_install_plan(self, 
                            install_plan: Dict[str, Any], 
                            env_path: Path, 
                            env_name: str) -> List[Dict[str, Any]]:
        """Execute the installation plan using the installer registry.
        
        Args:
            install_plan (Dict[str, Any]): Installation plan to execute.
            env_path (Path): Environment path for installation.
            env_name (str): Environment name.
            
        Returns:
            List[Dict[str, Any]]: List of successfully installed packages.
            
        Raises:
            DependencyInstallationError: If installation fails.
        """
        installed_packages = []
        
        # Create comprehensive installation context
        context = InstallationContext(
            environment_path=env_path,
            environment_name=env_name,
            temp_dir=env_path / ".tmp",
            cache_dir=self.package_loader.cache_dir if hasattr(self.package_loader, 'cache_dir') else None,
            parallel_enabled=False,  # Future enhancement
            force_reinstall=False,   # Future enhancement
            simulation_mode=False,   # Future enhancement
            extra_config={
                "package_loader": self.package_loader,
                "registry_service": self.registry_service,
                "registry_data": self.registry_data,
                "main_package_path": self._resolved_package_path,
                "main_package_type": self._resolved_package_type
            }
        )

        # Configure Python environment variables if available
        if self._python_env_vars:
            context.set_config("python_env_vars", self._python_env_vars)

        try:
            # Install dependencies by type using appropriate installers
            for dep_type, dependencies in install_plan["dependencies_to_install"].items():
                if not dependencies:
                    continue
                
                if not installer_registry.is_registered(dep_type):
                    self.logger.warning(f"No installer registered for dependency type: {dep_type}")
                    continue
                
                installer = installer_registry.get_installer(dep_type)
                
                for dep in dependencies:
                    # Use the extracted install_single_dep method
                    installed_package = self.install_single_dep(dep, context)
                    installed_packages.append(installed_package)
                    
            # Install main package last
            main_pkg_info = self._install_main_package(context)
            installed_packages.append(main_pkg_info)
            
            return installed_packages
            
        except Exception as e:
            self.logger.error(f"Installation execution failed: {e}")
            raise DependencyInstallationError(f"Installation execution failed: {e}") from e

    def _install_main_package(self, context: InstallationContext) -> Dict[str, Any]:
        """Install the main package using package_loader directly.
        
        The main package installation bypasses the installer registry and uses
        the package_loader directly since it's not a dependency but the primary package.
        
        Args:
            context (InstallationContext): Installation context.
            
        Returns:
            Dict[str, Any]: Installed package information.
            
        Raises:
            DependencyInstallationError: If main package installation fails.
        """
        try:
            # Get package information using PackageService
            package_name = self.package_service.get_field("name")
            package_version = self.package_service.get_field("version")
            
            # Install using package_loader directly
            if self._resolved_package_type == "local":
                # For local packages, install from resolved path
                installed_path = self.package_loader.install_local_package(
                    source_path=self._resolved_package_path,
                    target_dir=context.environment_path,
                    package_name=package_name
                )
            else:
                # For remote packages, install from downloaded path
                installed_path = self.package_loader.install_local_package(
                    source_path=self._resolved_package_path,  # Downloaded path
                    target_dir=context.environment_path,
                    package_name=package_name
                )
            
            self.logger.info(f"Successfully installed main package {package_name} to {installed_path}")
            
            return {
                "name": package_name,
                "version": package_version,
                "type": "hatch",
                "source": self._resolved_package_location
            }
            
        except Exception as e:
            raise DependencyInstallationError(f"Failed to install main package: {e}") from e
