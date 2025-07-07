"""
Defines context, status, and result data structures for dependency installation.

This module provides the InstallationContext dataclass for encapsulating
environment and configuration information required during dependency installation,
as well as InstallationStatus and InstallationResult for representing the
outcome and details of installation operations.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

@dataclass
class InstallationContext:
    """Context information for dependency installation.
    
    This class encapsulates all the environment and configuration information
    needed for installing dependencies, making the installer interface cleaner
    and more extensible.
    """
    
    environment_path: Path
    """Path to the target environment where dependencies will be installed."""
    
    environment_name: str
    """Name of the target environment."""
    
    temp_dir: Optional[Path] = None
    """Temporary directory for download/build operations."""
    
    cache_dir: Optional[Path] = None
    """Cache directory for reusable artifacts."""
    
    parallel_enabled: bool = True
    """Whether parallel installation is enabled."""
    
    force_reinstall: bool = False
    """Whether to force reinstallation of existing packages."""
    
    simulation_mode: bool = False
    """Whether to run in simulation mode (no actual installation)."""
    
    extra_config: Optional[Dict[str, Any]] = None
    """Additional installer-specific configuration."""
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value from extra_config.
        
        Args:
            key (str): Configuration key to retrieve.
            default (Any, optional): Default value if key not found.
            
        Returns:
            Any: Configuration value or default.
        """
        if self.extra_config is None:
            return default
        return self.extra_config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """Set a configuration value in extra_config.
        
        Args:
            key (str): Configuration key to set.
            value (Any): Value to set for the key.
        """
        if self.extra_config is None:
            self.extra_config = {}
        self.extra_config[key] = value


class InstallationStatus(Enum):
    """Status of an installation operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class InstallationResult:
    """Result of an installation operation.
    
    Provides detailed information about the installation outcome,
    including status, paths, and any error information.
    """
    
    dependency_name: str
    """Name of the dependency that was installed."""
    
    status: InstallationStatus
    """Final status of the installation."""
    
    installed_path: Optional[Path] = None
    """Path where the dependency was installed."""
    
    installed_version: Optional[str] = None
    """Actual version that was installed."""
    
    error_message: Optional[str] = None
    """Error message if installation failed."""
    
    artifacts: Optional[List[Path]] = None
    """List of files/directories created during installation."""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional installer-specific metadata."""