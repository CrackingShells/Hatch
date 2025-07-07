"""Basic test for installer registry functionality.

This test verifies that all installers are properly registered and can be
retrieved from the registry.
"""

import sys
from pathlib import Path
import unittest

# Add the parent directory to the path so we can import hatch modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# It is mandatory to import the installer classes to ensure they are registered
from hatch.installers.hatch_installer import HatchInstaller
from hatch.installers.python_installer import PythonInstaller
from hatch.installers.system_installer import SystemInstaller
from hatch.installers.docker_installer import DockerInstaller
from hatch.installers import installer_registry, DependencyInstaller


class TestInstallerRegistry(unittest.TestCase):
    """Test suite for the installer registry."""

    def test_registered_types(self):
        """Test that all expected installer types are registered."""
        registered_types = installer_registry.get_registered_types()
        expected_types = ["hatch", "python", "system", "docker"]
        for expected_type in expected_types:
            self.assertIn(expected_type, registered_types, f"{expected_type} installer should be registered")

    def test_get_installer_instance(self):
        """Test that the registry returns a valid installer instance for each type."""
        for dep_type in ["hatch", "python", "system", "docker"]:
            installer = installer_registry.get_installer(dep_type)
            self.assertIsInstance(installer, DependencyInstaller)
            self.assertEqual(installer.installer_type, dep_type)

    def test_error_on_unknown_type(self):
        """Test that requesting an unknown type raises ValueError."""
        with self.assertRaises(ValueError):
            installer_registry.get_installer("unknown_type")

    def test_registry_repr_and_len(self):
        """Test __repr__ and __len__ methods for coverage."""
        repr_str = repr(installer_registry)
        self.assertIn("InstallerRegistry", repr_str)
        self.assertGreaterEqual(len(installer_registry), 4)


if __name__ == "__main__":
    unittest.main()
