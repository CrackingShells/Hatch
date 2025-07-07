"""Installer registry for dependency installers.

This module provides a centralized registry for mapping dependency types to their
corresponding installer implementations, enabling dynamic lookup and delegation
of installation operations.
"""

import logging
from typing import Dict, Type, List, Optional, Any

from .installer_base import DependencyInstaller

logger = logging.getLogger("hatch.installer_registry")


class InstallerRegistry:
    """Registry for dependency installers by type.
    
    This class provides a centralized mapping between dependency types and their
    corresponding installer implementations. It enables the orchestrator to remain
    agnostic to installer details while providing extensible installer management.
    
    The registry follows these principles:
    - Single source of truth for installer-to-type mappings
    - Dynamic registration and lookup
    - Clear error handling for unsupported types
    - Extensibility for future installer types
    """

    def __init__(self):
        """Initialize the installer registry."""
        self._installers: Dict[str, Type[DependencyInstaller]] = {}
        logger.debug("Initialized installer registry")

    def register_installer(self, dep_type: str, installer_cls: Type[DependencyInstaller]) -> None:
        """Register an installer class for a dependency type.
        
        Args:
            dep_type (str): The dependency type identifier (e.g., "hatch", "python", "docker").
            installer_cls (Type[DependencyInstaller]): The installer class to register.
            
        Raises:
            ValueError: If the installer class does not implement DependencyInstaller.
            TypeError: If the installer_cls is not a class or is None.
        """
        if not isinstance(installer_cls, type):
            raise TypeError(f"installer_cls must be a class, got {type(installer_cls)}")
        
        if not issubclass(installer_cls, DependencyInstaller):
            raise ValueError(f"installer_cls must be a subclass of DependencyInstaller, got {installer_cls}")
        
        if dep_type in self._installers:
            logger.warning(f"Overriding existing installer for type '{dep_type}': {self._installers[dep_type]} -> {installer_cls}")
        
        self._installers[dep_type] = installer_cls
        logger.debug(f"Registered installer for type '{dep_type}': {installer_cls.__name__}")

    def get_installer(self, dep_type: str) -> DependencyInstaller:
        """Get an installer instance for the given dependency type.
        
        Args:
            dep_type (str): The dependency type to get an installer for.
            
        Returns:
            DependencyInstaller: A new instance of the appropriate installer.
            
        Raises:
            ValueError: If no installer is registered for the given dependency type.
        """
        if dep_type not in self._installers:
            available_types = list(self._installers.keys())
            raise ValueError(
                f"No installer registered for dependency type '{dep_type}'. "
                f"Available types: {available_types}"
            )
        
        installer_cls = self._installers[dep_type]
        installer = installer_cls()
        logger.debug(f"Created installer instance for type '{dep_type}': {installer_cls.__name__}")
        return installer

    def can_install(self, dep_type: str, dependency: Dict[str, Any]) -> bool:
        """Check if the registry can handle the given dependency.
        
        This method first checks if an installer is registered for the dependency's
        type, then delegates to the installer's can_install method for more
        detailed validation.
        
        Args:
            dependency (Dict[str, Any]): Dependency object to check.
            
        Returns:
            bool: True if the dependency can be installed, False otherwise.
        """
        if dep_type not in self._installers:
            logger.error(f"No installer registered for dependency type '{dep_type}'")
            return False
        
        try:
            installer = self.get_installer(dep_type)
            return installer.can_install(dependency)
        except Exception as e:
            logger.warning(f"Error checking if dependency can be installed: {e}")
            return False

    def get_registered_types(self) -> List[str]:
        """Get a list of all registered dependency types.
        
        Returns:
            List[str]: List of registered dependency type identifiers.
        """
        return list(self._installers.keys())

    def is_registered(self, dep_type: str) -> bool:
        """Check if an installer is registered for the given type.
        
        Args:
            dep_type (str): The dependency type to check.
            
        Returns:
            bool: True if an installer is registered for the type, False otherwise.
        """
        return dep_type in self._installers

    def unregister_installer(self, dep_type: str) -> Optional[Type[DependencyInstaller]]:
        """Unregister an installer for the given dependency type.
        
        This method is primarily intended for testing and advanced use cases.
        
        Args:
            dep_type (str): The dependency type to unregister.
            
        Returns:
            Type[DependencyInstaller]: The unregistered installer class, or None if not found.
        """
        installer_cls = self._installers.pop(dep_type, None)
        if installer_cls:
            logger.debug(f"Unregistered installer for type '{dep_type}': {installer_cls.__name__}")
        return installer_cls

    def clear(self) -> None:
        """Clear all registered installers.
        
        This method is primarily intended for testing purposes.
        """
        self._installers.clear()
        logger.debug("Cleared all registered installers")

    def __len__(self) -> int:
        """Get the number of registered installers.
        
        Returns:
            int: Number of registered installers.
        """
        return len(self._installers)

    def __contains__(self, dep_type: str) -> bool:
        """Check if a dependency type is registered.
        
        Args:
            dep_type (str): The dependency type to check.
            
        Returns:
            bool: True if the type is registered, False otherwise.
        """
        return dep_type in self._installers

    def __repr__(self) -> str:
        """Get a string representation of the registry.
        
        Returns:
            str: String representation showing registered types.
        """
        types = list(self._installers.keys())
        return f"InstallerRegistry(types={types})"


# Global singleton instance
installer_registry = InstallerRegistry()
