"""Abstract base class for dependency installers.

This module defines the core installer interface that all concrete installers
must implement, ensuring consistent behavior across different dependency types.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from .installation_context import InstallationContext, InstallationResult


class InstallationError(Exception):
    """Exception raised for installation-related errors.
    
    This exception provides structured error information that can be used
    for error reporting and recovery strategies.
    """
    
    def __init__(self, message: str, dependency_name: Optional[str] = None, 
                 error_code: Optional[str] = None, cause: Optional[Exception] = None):
        """Initialize the installation error.
        
        Args:
            message (str): Human-readable error message.
            dependency_name (str, optional): Name of the dependency that failed.
            error_code (str, optional): Machine-readable error code.
            cause (Exception, optional): Underlying exception that caused this error.
        """
        self.message = message
        self.dependency_name = dependency_name
        self.error_code = error_code
        self.cause = cause


class DependencyInstaller(ABC):
    """Abstract base class for dependency installers.
    
    This class defines the core interface that all concrete installers must implement.
    It provides a consistent API for installing and managing dependencies across
    different types (Hatch packages, Python packages, system packages, Docker containers).
    
    The installer design follows these principles:
    - Single responsibility: Each installer handles one dependency type
    - Extensibility: New dependency types can be added by implementing this interface
    - Observability: Progress reporting through callbacks
    - Error handling: Structured exceptions and rollback support
    - Testability: Clear interface for mocking and testing
    """
    
    @property
    @abstractmethod
    def installer_type(self) -> str:
        """Get the type identifier for this installer.
        
        Returns:
            str: Unique identifier for the installer type (e.g., "hatch", "python", "docker").
        """
        pass
    
    @property
    @abstractmethod
    def supported_schemes(self) -> List[str]:
        """Get the URI schemes this installer can handle.
        
        Returns:
            List[str]: List of URI schemes (e.g., ["file", "http", "https"] for local/remote packages).
        """
        pass
    
    @abstractmethod
    def can_install(self, dependency: Dict[str, Any]) -> bool:
        """Check if this installer can handle the given dependency.
        
        This method allows the installer registry to determine which installer
        should be used for a specific dependency.
        
        Args:
            dependency (Dict[str, Any]): Dependency object with keys like 'type', 'name', 'uri', etc.
            
        Returns:
            bool: True if this installer can handle the dependency, False otherwise.
        """
        pass
    
    @abstractmethod
    def install(self, dependency: Dict[str, Any], context: InstallationContext,
                progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Install a dependency.
        
        This is the core method that performs the actual installation of a dependency
        into the specified environment.
        
        Args:
            dependency (Dict[str, Any]): Dependency object containing:
                - name (str): Name of the dependency
                - version_constraint (str): Version constraint
                - resolved_version (str): Specific version to install
                - uri (str, optional): Download/source URI
                - type (str): Dependency type
                - Additional installer-specific fields
            context (InstallationContext): Installation context with environment info
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.
                Parameters: (operation_name, progress_percentage, status_message)
                
        Returns:
            InstallationResult: Result of the installation operation.
            
        Raises:
            InstallationError: If installation fails for any reason.
        """
        pass
    
    def uninstall(self, dependency: Dict[str, Any], context: InstallationContext,
                  progress_callback: Optional[Callable[[str, float, str], None]] = None) -> InstallationResult:
        """Uninstall a dependency.
        
        Default implementation raises NotImplementedError. Concrete installers
        can override this method to provide uninstall functionality.
        
        Args:
            dependency (Dict[str, Any]): Dependency object to uninstall.
            context (InstallationContext): Installation context with environment info.
            progress_callback (Callable[[str, float, str], None], optional): Progress reporting callback.
                
        Returns:
            InstallationResult: Result of the uninstall operation.
            
        Raises:
            NotImplementedError: If uninstall is not supported by this installer.
            InstallationError: If uninstall fails for any reason.
        """
        raise NotImplementedError(f"Uninstall not implemented for {self.installer_type} installer")
    
    def validate_dependency(self, dependency: Dict[str, Any]) -> bool:
        """Validate that a dependency object has required fields.
        
        This method can be overridden by concrete installers to perform
        installer-specific validation.
        
        Args:
            dependency (Dict[str, Any]): Dependency object to validate.
            
        Returns:
            bool: True if dependency is valid, False otherwise.
        """
        required_fields = ["name", "version_constraint", "resolved_version"]
        return all(field in dependency for field in required_fields)
    
    def get_installation_info(self, dependency: Dict[str, Any], context: InstallationContext) -> Dict[str, Any]:
        """Get information about what would be installed without actually installing.
        
        This method can be used for dry-run scenarios or to provide installation
        previews to users.
        
        Args:
            dependency (Dict[str, Any]): Dependency object to analyze.
            context (InstallationContext): Installation context.
            
        Returns:
            Dict[str, Any]: Information about the planned installation.
        """
        return {
            "installer_type": self.installer_type,
            "dependency_name": dependency.get("name"),
            "resolved_version": dependency.get("resolved_version"),
            "target_path": str(context.environment_path),
            "supported": self.can_install(dependency)
        }
    
    def cleanup_failed_installation(self, dependency: Dict[str, Any], context: InstallationContext,
                                   artifacts: Optional[List[Path]] = None) -> None:
        """Clean up artifacts from a failed installation.
        
        This method is called when an installation fails and needs to be rolled back.
        Concrete installers can override this to perform specific cleanup operations.
        
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
                            import shutil
                            shutil.rmtree(artifact)
                except Exception:
                    # Log but don't raise - cleanup is best effort
                    pass
