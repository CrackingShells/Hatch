"""
Hatch - Package Manager for the Hatch! ecosystem

This package provides tools for managing Hatch packages, environments,
and interacting with the Hatch registry.
"""

from .cli_hatch import main
from .environment_manager import HatchEnvironmentManager
from .package_loader import HatchPackageLoader, PackageLoaderError
from .registry_retriever import RegistryRetriever
from .template_generator import create_package_template

__all__ = [
    'HatchEnvironmentManager',
    'HatchPackageLoader',
    'PackageLoaderError',
    'RegistryRetriever',
    'create_package_template',
    'main',
]