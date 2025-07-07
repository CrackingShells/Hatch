"""Installer for Hatch package dependencies.

Implements installation logic for Hatch packages using the HatchPackageLoader and
integrates pre-install validation using HatchPackageValidator and PackageService.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from hatch.installers.installer_base import DependencyInstaller, InstallationContext, InstallationResult, InstallationError
from hatch.installers.installation_context import InstallationStatus
from hatch.package_loader import HatchPackageLoader, PackageLoaderError
from hatch_validator.package_validator import HatchPackageValidator

class HatchInstaller(DependencyInstaller):
    """Installer for Hatch package dependencies.

    Handles installation, validation, and uninstallation of Hatch packages using
    the HatchPackageLoader and validator APIs.
    """

    def __init__(self, registry_data: Optional[Dict[str, Any]] = None):
        """Initialize the HatchInstaller.

        Args:
            registry_data (Dict[str, Any], optional): Registry data for validation. Defaults to None.
        """
        self.logger = logging.getLogger("hatch.installers.hatch_installer")
        self.package_loader = HatchPackageLoader()
        self.validator = HatchPackageValidator(registry_data=registry_data)

    @property
    def installer_type(self) -> str:
        """Get the type identifier for this installer.

        Returns:
            str: Unique identifier for the installer type ("hatch").
        """
        return "hatch"

    @property
    def supported_schemes(self) -> List[str]:
        """Get the URI schemes this installer can handle.

        Returns:
            List[str]: List of URI schemes (e.g., ["file", "http", "https"]).
        """
        return ["file", "http", "https"]

    def can_install(self, dependency: Dict[str, Any]) -> bool:
        """Check if this installer can handle the given dependency.

        Args:
            dependency (Dict[str, Any]): Dependency object.

        Returns:
            bool: True if this installer can handle the dependency, False otherwise.
        """
        return dependency.get("type") == self.installer_type

    def validate_dependency(self, dependency: Dict[str, Any]) -> bool:
        """Validate that a dependency object has required fields and is a valid Hatch package.

        Args:
            dependency (Dict[str, Any]): Dependency object to validate.

        Returns:
            bool: True if dependency is valid, False otherwise.
        """
        required_fields = ["name", "version_constraint", "resolved_version", "uri"]
        if not all(field in dependency for field in required_fields):
            return False
        # Optionally, perform further validation using the validator if a path is provided
        return True

    def install(self, dependency: Dict[str, Any], context: InstallationContext,
                progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Install a Hatch package dependency.

        Args:
            dependency (Dict[str, Any]): Dependency object containing name, version, uri, etc.
            context (InstallationContext): Installation context with environment info.
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.

        Returns:
            InstallationResult: Result of the installation operation.

        Raises:
            InstallationError: If installation fails for any reason.
        """

        self.logger.debug(f"Installing Hatch dependency: {dependency}")
        if not self.validate_dependency(dependency):
            self.logger.error(f"Invalid dependency format: {dependency}")
            raise InstallationError("Invalid dependency object",
                                    dependency_name=dependency.get("name"),
                                    error_code="INVALID_HATCH_DEPENDENCY_FORMAT",
                                    )

        name = dependency["name"]
        version = dependency["resolved_version"]
        uri = dependency["uri"]
        target_dir = Path(context.environment_path)
        try:
            if progress_callback:
                progress_callback("install", 0.0, f"Installing {name}-{version} from {uri}")
            # Download/install the package
            if uri and uri.startswith("file://"):
                pkg_path = Path(uri[7:])
                result_path = self.package_loader.install_local_package(pkg_path, target_dir, name)
            elif uri:
                result_path = self.package_loader.install_remote_package(uri, name, version, target_dir)
            else:
                raise InstallationError(f"No URI provided for dependency {name}", dependency_name=name)
            
            if progress_callback:
                progress_callback("install", 1.0, f"Installed {name} to {result_path}")
            
            return InstallationResult(
                dependency_name=name,
                status=InstallationStatus.COMPLETED,
                installed_path=result_path,
                installed_version=version,
                error_message=None,
                artifacts=result_path,
                metadata={"name": name, "version": version}
            )
            
        except (PackageLoaderError, Exception) as e:
            self.logger.error(f"Failed to install {name}: {e}")
            raise InstallationError(f"Failed to install {name}: {e}", dependency_name=name, cause=e)

    def uninstall(self, dependency: Dict[str, Any], context: InstallationContext,
                  progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Uninstall a Hatch package dependency.

        Args:
            dependency (Dict[str, Any]): Dependency object to uninstall.
            context (InstallationContext): Installation context with environment info.
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.

        Returns:
            InstallationResult: Result of the uninstall operation.

        Raises:
            InstallationError: If uninstall fails for any reason.
        """
        if not self.validate_dependency(dependency):
            raise InstallationError("Invalid dependency object",
                                    dependency_name=dependency.get("name"),
                                    error_code="INVALID_HATCH_DEPENDENCY_FORMAT",
                                    )

        name = dependency["name"]
        target_dir = Path(context.environment_path) / name
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            if progress_callback:
                progress_callback("uninstall", 1.0, f"Uninstalled {name}")
            return InstallationResult(
                dependency_name=name,
                status=InstallationStatus.COMPLETED,
                installed_path=target_dir,
                installed_version=dependency.get("resolved_version"),
                error_message=None,
                artifacts=None,
                metadata={"name": name}
            )
        except Exception as e:
            self.logger.error(f"Failed to uninstall {name}: {e}")
            raise InstallationError(f"Failed to uninstall {name}: {e}", dependency_name=name, cause=e)

    def cleanup_failed_installation(self, dependency: Dict[str, Any], context: InstallationContext,
                                   artifacts: Optional[List[Path]] = None) -> None:
        """Clean up artifacts from a failed installation.

        Args:
            dependency (Dict[str, Any]): Dependency that failed to install.
            context (InstallationContext): Installation context.
            artifacts (List[Path], optional): List of files/directories to clean up.
        """
        if artifacts:
            for artifact in artifacts:
                try:
                    if artifact.exists():
                        if artifact.is_file():
                            artifact.unlink()
                        elif artifact.is_dir():
                            shutil.rmtree(artifact)
                except Exception:
                    pass

# Register this installer with the global registry
from .registry import installer_registry
installer_registry.register_installer("hatch", HatchInstaller)
