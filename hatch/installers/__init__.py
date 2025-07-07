"""Installer framework for Hatch dependency management.

This package provides a robust, extensible installer interface and concrete
implementations for different dependency types including Hatch packages,
Python packages, system packages, and Docker containers.
"""

from hatch.installers.installer_base import DependencyInstaller, InstallationError, InstallationContext
from hatch.installers.hatch_installer import HatchInstaller
from hatch.installers.python_installer import PythonInstaller
from hatch.installers.system_installer import SystemInstaller
from hatch.installers.docker_installer import DockerInstaller
from hatch.installers.registry import InstallerRegistry, installer_registry

__all__ = [
    "DependencyInstaller",
    "InstallationError", 
    "InstallationContext",
    #"HatchInstaller", # Not necessary to expose directly, the registry will handle it
    #"PythonInstaller", # Not necessary to expose directly, the registry will handle it
    #"SystemInstaller", # Not necessary to expose directly, the registry will handle it
    #"DockerInstaller", # Not necessary to expose directly, the registry will handle it
    "InstallerRegistry",
    "installer_registry"
]
