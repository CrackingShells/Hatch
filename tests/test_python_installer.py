import subprocess
import unittest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest import mock

from hatch.installers.python_installer import PythonInstaller
from hatch.installers.installation_context import InstallationContext, InstallationStatus
from hatch.installers.installer_base import InstallationError

class DummyContext(InstallationContext):
    def __init__(self, env_path=None, env_name=None, simulation_mode=False, extra_config=None):
        self.simulation_mode = simulation_mode
        self.extra_config = extra_config or {}
        self.environment_path = env_path
        self.environment_name = env_name

    def get_config(self, key, default=None):
        return self.extra_config.get(key, default)

class TestPythonInstaller(unittest.TestCase):
    """Tests for the PythonInstaller class covering validation, installation, and error handling."""

    def setUp(self):
        """Set up a temporary directory and PythonInstaller instance for each test."""
        
        self.temp_dir = tempfile.mkdtemp()
        self.env_path = Path(self.temp_dir) / "test_env"

        # make the directory
        self.env_path.mkdir(parents=True, exist_ok=True)

        # assert the virtual environment was created successfully
        self.assertTrue(self.env_path.exists() and self.env_path.is_dir())
        
        self.installer = PythonInstaller()
        self.dummy_context = DummyContext(self.env_path, env_name="test_env", extra_config={
            "target_dir": str(self.env_path)
        })

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.temp_dir)

    def test_validate_dependency_valid(self):
        """Test validate_dependency returns True for valid dependency dict."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        self.assertTrue(self.installer.validate_dependency(dep))

    def test_validate_dependency_invalid_missing_fields(self):
        """Test validate_dependency returns False if required fields are missing."""
        dep = {"name": "requests"}
        self.assertFalse(self.installer.validate_dependency(dep))

    def test_validate_dependency_invalid_package_manager(self):
        """Test validate_dependency returns False for unsupported package manager."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0", "package_manager": "unknown"}
        self.assertFalse(self.installer.validate_dependency(dep))

    def test_can_install_python_type(self):
        """Test can_install returns True for type 'python'."""
        dep = {"type": self.installer.installer_type}
        self.assertTrue(self.installer.can_install(dep))

    def test_can_install_wrong_type(self):
        """Test can_install returns False for non-python type."""
        dep = {"type": "hatch"}
        self.assertFalse(self.installer.can_install(dep))

    @mock.patch("hatch.installers.python_installer.subprocess.Popen", side_effect=Exception("fail"))
    def test_run_pip_subprocess_exception(self, mock_popen):
        """Test _run_pip_subprocess raises InstallationError on exception."""
        cmd = [sys.executable, "-m", "pip", "--version"]
        with self.assertRaises(InstallationError):
            self.installer._run_pip_subprocess(cmd)

    def test_install_simulation_mode(self):
        """Test install returns COMPLETED immediately in simulation mode."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext(simulation_mode=True)
        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=(0, "", ""))
    def test_install_success(self, mock_run):
        """Test install returns COMPLETED on successful pip install."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext()
        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=(1, "", "error"))
    def test_install_failure(self, mock_run):
        """Test install raises InstallationError on pip failure."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"} # The content don't matter here given the mock
        context = DummyContext()
        with self.assertRaises(InstallationError):
            self.installer.install(dep, context)

    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=(0, "", ""))
    def test_uninstall_success(self, mock_run):
        """Test uninstall returns COMPLETED on successful pip uninstall."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext()
        result = self.installer.uninstall(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=(1, "", "error"))
    def test_uninstall_failure(self, mock_run):
        """Test uninstall raises InstallationError on pip uninstall failure."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext()
        with self.assertRaises(InstallationError):
            self.installer.uninstall(dep, context)

class TestPythonInstallerIntegration(unittest.TestCase):

    """Integration tests for PythonInstaller that perform actual package installations."""

    def setUp(self):
        """Set up a temporary directory and PythonInstaller instance for each test."""
        
        self.temp_dir = tempfile.mkdtemp()
        self.env_path = Path(self.temp_dir) / "test_env"
        
        # Use pip to create a virtual environment
        subprocess.check_call([sys.executable, "-m", "venv", str(self.env_path)])

        # assert the virtual environment was created successfully
        self.assertTrue(self.env_path.exists() and self.env_path.is_dir())

        # Get the Python executable in the virtual environment
        if sys.platform == "win32":
            self.python_executable = self.env_path / "Scripts" / "python.exe"
        else:
            self.python_executable = self.env_path / "bin" / "python"
        
        self.installer = PythonInstaller()
        self.dummy_context = DummyContext(self.env_path, env_name="test_env", extra_config={
            "python_executable": self.python_executable,
            "target_dir": str(self.env_path)
        })

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.temp_dir)

    def test_install_actual_package_success(self):
        """Test actual installation of a real Python package without mocking.
        
        Uses a lightweight package that's commonly available and installs quickly.
        This validates the entire installation pipeline including subprocess handling.
        """
        # Use a lightweight, commonly available package for testing
        dep = {
            "name": "wheel", 
            "version_constraint": "*",
            "type": "python"
        }
        
        # Create a virtual environment context to avoid polluting system packages
        context = DummyContext(
            env_path=self.env_path,
            env_name="test_env",
            extra_config={
                "python_executable": self.python_executable,
                "target_dir": str(self.env_path)
            }
        )
        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertIn("wheel", result.dependency_name)

    def test_install_package_with_version_constraint(self):
        """Test installation with specific version constraint.
        
        Validates that version constraints are properly passed to pip
        and that the installation succeeds with real package resolution.
        """
        dep = {
            "name": "setuptools",
            "version_constraint": ">=40.0.0",
            "type": "python"
        }
        
        context = DummyContext(
            env_path=self.env_path,
            env_name="test_env",
            extra_config={
            "python_executable": self.python_executable
        })

        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        # Verify the dependency was processed correctly
        self.assertIsNotNone(result.metadata)

    def test_install_package_with_extras(self):
        """Test installation of a package with extras specification.
        
        Tests the extras handling functionality with a real package installation.
        """
        dep = {
            "name": "requests",
            "version_constraint": "*",
            "type": "python",
            "extras": ["security"]  # pip[security] if available
        }
        
        context = DummyContext(
            env_path=self.env_path,
            env_name="test_env",
            extra_config={
            "python_executable": self.python_executable
        })
        
        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    def test_uninstall_actual_package(self):
        """Test actual uninstallation of a Python package.
        
        First installs a package, then uninstalls it to test the complete cycle.
        This validates both installation and uninstallation without mocking.
        """
        dep = {
            "name": "wheel",
            "version_constraint": "*", 
            "type": "python"
        }
        
        context = DummyContext(
            env_path=self.env_path,
            env_name="test_env",
            extra_config={
            "python_executable": self.python_executable
        })
        
        # First install the package
        install_result = self.installer.install(dep, context)
        self.assertEqual(install_result.status, InstallationStatus.COMPLETED)
        
        # Then uninstall it
        uninstall_result = self.installer.uninstall(dep, context)
        self.assertEqual(uninstall_result.status, InstallationStatus.COMPLETED)

    def test_install_nonexistent_package_failure(self):
        """Test that installation fails appropriately for non-existent packages.
        
        This validates error handling when pip encounters a package that doesn't exist,
        without using mocks to simulate the failure.
        """
        dep = {
            "name": "this-package-definitely-does-not-exist-12345",
            "version_constraint": "*",
            "type": "python"
        }
        
        context = DummyContext(
            env_path=self.env_path,
            env_name="test_env",
            extra_config={
            "python_executable": self.python_executable
        })
        
        with self.assertRaises(InstallationError) as cm:
            self.installer.install(dep, context)
        
        # Verify the error contains useful information
        error_msg = str(cm.exception)
        self.assertIn("this-package-definitely-does-not-exist-12345", error_msg)

    def test_get_installation_info_for_installed_package(self):
        """Test retrieval of installation info for an actually installed package.
        
        This tests the get_installation_info method with a real package
        that should be available in most Python environments.
        """
        dep = {
            "name": "pip",  # pip should be available in most environments
            "version_constraint": "*",
            "type": "python"
        }
        
        context = DummyContext(
            env_path=self.env_path,
            env_name="test_env",
            extra_config={
            "python_executable": self.python_executable
        })
        
        info = self.installer.get_installation_info(dep, context)
        self.assertIsInstance(info, dict)
        # Basic checks for expected info structure
        if info:  # Only check if info was returned (some implementations might return empty dict)
            self.assertIn("dependency_name", info)

if __name__ == "__main__":
    unittest.main()
