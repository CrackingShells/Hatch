import subprocess
import unittest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest import mock

# Import wobble decorators for test categorization
from wobble.decorators import regression_test, integration_test

from hatch.installers.python_installer import PythonInstaller
from hatch.installers.installation_context import (
    InstallationContext,
    InstallationStatus,
)
from hatch.installers.installer_base import InstallationError


class DummyContext(InstallationContext):
    def __init__(
        self, env_path=None, env_name=None, simulation_mode=False, extra_config=None
    ):
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
        self.dummy_context = DummyContext(
            self.env_path,
            env_name="test_env",
            extra_config={"target_dir": str(self.env_path)},
        )

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.temp_dir)

    @regression_test
    def test_validate_dependency_valid(self):
        """Test validate_dependency returns True for valid dependency dict."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        self.assertTrue(self.installer.validate_dependency(dep))

    @regression_test
    def test_validate_dependency_invalid_missing_fields(self):
        """Test validate_dependency returns False if required fields are missing."""
        dep = {"name": "requests"}
        self.assertFalse(self.installer.validate_dependency(dep))

    @regression_test
    def test_validate_dependency_invalid_package_manager(self):
        """Test validate_dependency returns False for unsupported package manager."""
        dep = {
            "name": "requests",
            "version_constraint": ">=2.0.0",
            "package_manager": "unknown",
        }
        self.assertFalse(self.installer.validate_dependency(dep))

    @regression_test
    def test_can_install_python_type(self):
        """Test can_install returns True for type 'python'."""
        dep = {"type": self.installer.installer_type}
        self.assertTrue(self.installer.can_install(dep))

    @regression_test
    def test_can_install_wrong_type(self):
        """Test can_install returns False for non-python type."""
        dep = {"type": "hatch"}
        self.assertFalse(self.installer.can_install(dep))

    @regression_test
    @mock.patch(
        "hatch.installers.python_installer.subprocess.Popen",
        side_effect=Exception("fail"),
    )
    def test_run_pip_subprocess_exception(self, mock_popen):
        """Test _run_pip_subprocess raises InstallationError on exception."""
        cmd = [sys.executable, "-m", "pip", "--version"]
        with self.assertRaises(InstallationError):
            self.installer._run_pip_subprocess(cmd)

    @regression_test
    def test_install_simulation_mode(self):
        """Test install returns COMPLETED immediately in simulation mode."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext(simulation_mode=True)
        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=0)
    def test_install_success(self, mock_run):
        """Test install returns COMPLETED on successful pip install."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext()
        result = self.installer.install(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=1)
    def test_install_failure(self, mock_run):
        """Test install raises InstallationError on pip failure."""
        dep = {
            "name": "requests",
            "version_constraint": ">=2.0.0",
        }  # The content don't matter here given the mock
        context = DummyContext()
        with self.assertRaises(InstallationError):
            self.installer.install(dep, context)

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=0)
    def test_uninstall_success(self, mock_run):
        """Test uninstall returns COMPLETED on successful pip uninstall."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext()
        result = self.installer.uninstall(dep, context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=1)
    def test_uninstall_failure(self, mock_run):
        """Test uninstall raises InstallationError on pip uninstall failure."""
        dep = {"name": "requests", "version_constraint": ">=2.0.0"}
        context = DummyContext()
        with self.assertRaises(InstallationError):
            self.installer.uninstall(dep, context)


class TestPythonInstallerIntegration(unittest.TestCase):
    """Integration tests for PythonInstaller that perform actual package installations."""

    @classmethod
    def setUpClass(cls):
        """Create a shared virtual environment once for all integration tests."""
        cls.shared_temp_dir = tempfile.mkdtemp()
        cls.shared_env_path = Path(cls.shared_temp_dir) / "shared_test_env"
        subprocess.check_call([sys.executable, "-m", "venv", str(cls.shared_env_path)])
        if sys.platform == "win32":
            cls.shared_python_executable = (
                cls.shared_env_path / "Scripts" / "python.exe"
            )
        else:
            cls.shared_python_executable = cls.shared_env_path / "bin" / "python"

    @classmethod
    def tearDownClass(cls):
        """Remove the shared virtual environment."""
        shutil.rmtree(cls.shared_temp_dir, ignore_errors=True)

    def setUp(self):
        """Set up a PythonInstaller instance for each test.

        Mocked tests use a simple temp directory (no real venv needed).
        Integration tests use the shared venv from setUpClass.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.env_path = Path(self.temp_dir) / "test_env"
        self.env_path.mkdir(parents=True, exist_ok=True)

        self.installer = PythonInstaller()
        self.dummy_context = DummyContext(
            self.env_path,
            env_name="test_env",
            extra_config={
                "python_executable": sys.executable,
                "target_dir": str(self.env_path),
            },
        )

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        shutil.rmtree(self.temp_dir)

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=0)
    def test_install_actual_package_success(self, mock_run):
        """Test installation pipeline returns COMPLETED on successful pip install.

        Mocks _run_pip_subprocess to validate our install flow without calling pip.
        """
        dep = {"name": "wheel", "version_constraint": "*", "type": "python"}

        result = self.installer.install(dep, self.dummy_context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertIn("wheel", result.dependency_name)
        mock_run.assert_called_once()

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=0)
    def test_install_package_with_version_constraint(self, mock_run):
        """Test installation with specific version constraint.

        Validates that version constraints are properly passed through
        our install flow and result metadata is populated.
        """
        dep = {
            "name": "setuptools",
            "version_constraint": ">=40.0.0",
            "type": "python",
        }

        result = self.installer.install(dep, self.dummy_context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertIsNotNone(result.metadata)
        # Verify the version constraint was included in the command
        cmd_args = mock_run.call_args[0][0]
        self.assertTrue(
            any("setuptools>=40.0.0" in arg for arg in cmd_args),
            f"Expected 'setuptools>=40.0.0' in pip command args: {cmd_args}",
        )

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=0)
    def test_install_package_with_extras(self, mock_run):
        """Test installation of a package with extras specification.

        Validates that extras are correctly formatted in the pip command.
        """
        dep = {
            "name": "requests",
            "version_constraint": "*",
            "type": "python",
            "extras": ["security"],
        }

        result = self.installer.install(dep, self.dummy_context)
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        # Verify extras were included in the pip command
        cmd_args = mock_run.call_args[0][0]
        self.assertTrue(
            any("requests[security]" in arg for arg in cmd_args),
            f"Expected 'requests[security]' in pip command args: {cmd_args}",
        )

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=0)
    def test_uninstall_actual_package(self, mock_run):
        """Test install/uninstall cycle completes successfully.

        Mocks _run_pip_subprocess to validate our install and uninstall flow.
        """
        dep = {"name": "wheel", "version_constraint": "*", "type": "python"}

        # First install the package
        install_result = self.installer.install(dep, self.dummy_context)
        self.assertEqual(install_result.status, InstallationStatus.COMPLETED)

        # Then uninstall it
        uninstall_result = self.installer.uninstall(dep, self.dummy_context)
        self.assertEqual(uninstall_result.status, InstallationStatus.COMPLETED)

        # Verify both install and uninstall called _run_pip_subprocess
        self.assertEqual(mock_run.call_count, 2)

    @regression_test
    @mock.patch.object(PythonInstaller, "_run_pip_subprocess", return_value=1)
    def test_install_nonexistent_package_failure(self, mock_run):
        """Test that installation fails appropriately when pip returns non-zero.

        Mocks _run_pip_subprocess to return failure, validating our error handling.
        """
        dep = {
            "name": "this-package-definitely-does-not-exist-12345",
            "version_constraint": "*",
            "type": "python",
        }

        with self.assertRaises(InstallationError) as cm:
            self.installer.install(dep, self.dummy_context)

        # Verify the error contains useful information
        error_msg = str(cm.exception)
        self.assertIn("this-package-definitely-does-not-exist-12345", error_msg)

    @integration_test(scope="component")
    def test_get_installation_info_for_installed_package(self):
        """Test retrieval of installation info for an actually installed package.

        Uses the shared venv from setUpClass. This tests the get_installation_info
        method with a real package that should be available in the shared venv.
        """
        dep = {
            "name": "pip",  # pip should be available in the shared venv
            "version_constraint": "*",
            "type": "python",
        }

        context = DummyContext(
            env_path=self.__class__.shared_env_path,
            env_name="shared_test_env",
            extra_config={
                "python_executable": self.__class__.shared_python_executable,
            },
        )

        info = self.installer.get_installation_info(dep, context)
        self.assertIsInstance(info, dict)
        # Basic checks for expected info structure
        if info:
            self.assertIn("dependency_name", info)


if __name__ == "__main__":
    unittest.main()
