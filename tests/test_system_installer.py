"""Tests for SystemInstaller.

This module contains comprehensive tests for the SystemInstaller class,
including unit tests with mocked system calls and integration tests with
dummy packages.
"""

import unittest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from wobble.decorators import regression_test, integration_test

from hatch.installers.system_installer import SystemInstaller
from hatch.installers.installer_base import InstallationError
from hatch.installers.installation_context import (
    InstallationContext,
    InstallationResult,
    InstallationStatus,
)


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


class TestSystemInstaller(unittest.TestCase):
    """Test suite for SystemInstaller using unittest."""

    def setUp(self):
        self.installer = SystemInstaller()
        self.mock_context = DummyContext(
            env_path=Path("/test/env"),
            env_name="test_env",
            simulation_mode=False,
            extra_config={},
        )

    @regression_test
    def test_installer_type(self):
        self.assertEqual(self.installer.installer_type, "system")

    @regression_test
    def test_supported_schemes(self):
        self.assertEqual(self.installer.supported_schemes, ["apt"])

    @regression_test
    def test_can_install_valid_dependency(self):
        dependency = {
            "type": "system",
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        with (
            patch.object(self.installer, "_is_platform_supported", return_value=True),
            patch.object(self.installer, "_is_apt_available", return_value=True),
        ):
            self.assertTrue(self.installer.can_install(dependency))

    @regression_test
    def test_can_install_wrong_type(self):
        dependency = {
            "type": "python",
            "name": "requests",
            "version_constraint": ">=2.0.0",
        }

        self.assertFalse(self.installer.can_install(dependency))

    @regression_test
    def test_can_install_unsupported_platform(self):
        dependency = {
            "type": "system",
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        with patch.object(self.installer, "_is_platform_supported", return_value=False):
            self.assertFalse(self.installer.can_install(dependency))

    @regression_test
    def test_can_install_apt_not_available(self):
        dependency = {
            "type": "system",
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        with (
            patch.object(self.installer, "_is_platform_supported", return_value=True),
            patch.object(self.installer, "_is_apt_available", return_value=False),
        ):
            self.assertFalse(self.installer.can_install(dependency))

    @regression_test
    def test_validate_dependency_valid(self):
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        self.assertTrue(self.installer.validate_dependency(dependency))

    @regression_test
    def test_validate_dependency_missing_name(self):
        dependency = {"version_constraint": ">=7.0.0", "package_manager": "apt"}

        self.assertFalse(self.installer.validate_dependency(dependency))

    @regression_test
    def test_validate_dependency_missing_version_constraint(self):
        dependency = {"name": "curl", "package_manager": "apt"}

        self.assertFalse(self.installer.validate_dependency(dependency))

    @regression_test
    def test_validate_dependency_invalid_package_manager(self):
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "yum",
        }

        self.assertFalse(self.installer.validate_dependency(dependency))

    @regression_test
    def test_validate_dependency_invalid_version_constraint(self):
        dependency = {
            "name": "curl",
            "version_constraint": "invalid_version",
            "package_manager": "apt",
        }

        self.assertFalse(self.installer.validate_dependency(dependency))

    @regression_test
    @patch("platform.system")
    @patch("pathlib.Path.exists")
    def test_is_platform_supported_debian(self, mock_exists, mock_system):
        """Test platform support detection for Debian."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = True

        self.assertTrue(self.installer._is_platform_supported())
        mock_exists.assert_called_with()

    @regression_test
    @patch("platform.system")
    @patch("pathlib.Path.exists")
    @patch("builtins.open")
    def test_is_platform_supported_ubuntu(self, mock_open, mock_exists, mock_system):
        """Test platform support detection for Ubuntu."""
        mock_system.return_value = "Linux"
        mock_exists.return_value = False

        # Mock os-release file content
        mock_file = MagicMock()
        mock_file.read.return_value = 'NAME="Ubuntu"\nVERSION="20.04"'
        mock_open.return_value.__enter__.return_value = mock_file

        self.assertTrue(self.installer._is_platform_supported())

    @regression_test
    @patch("platform.system")
    @patch("pathlib.Path.exists")
    def test_is_platform_supported_unsupported(self, mock_exists, mock_system):
        """Test platform support detection for unsupported systems."""
        mock_system.return_value = "Windows"
        mock_exists.return_value = False

        self.assertFalse(self.installer._is_platform_supported())

    @regression_test
    @patch("shutil.which")
    def test_is_apt_available_true(self, mock_which):
        """Test apt availability detection when apt is available."""
        mock_which.return_value = "/usr/bin/apt"

        self.assertTrue(self.installer._is_apt_available())
        mock_which.assert_called_once_with("apt")

    @regression_test
    @patch("shutil.which")
    def test_is_apt_available_false(self, mock_which):
        """Test apt availability detection when apt is not available."""
        mock_which.return_value = None

        self.assertFalse(self.installer._is_apt_available())

    @regression_test
    def test_build_apt_command_basic(self):
        """Test building basic apt install command."""
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        command = self.installer._build_apt_command(dependency, self.mock_context)
        self.assertEqual(command, ["sudo", "apt", "install", "curl"])

    @regression_test
    def test_build_apt_command_exact_version(self):
        """Test building apt command with exact version constraint."""
        dependency = {
            "name": "curl",
            "version_constraint": "==7.68.0",
            "package_manager": "apt",
        }

        command = self.installer._build_apt_command(dependency, self.mock_context)
        self.assertEqual(command, ["sudo", "apt", "install", "curl=7.68.0"])

    @regression_test
    def test_build_apt_command_automated(self):
        """Test building apt command in automated mode."""
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        self.mock_context.extra_config = {"automated": True}
        command = self.installer._build_apt_command(dependency, self.mock_context)
        self.assertEqual(command, ["sudo", "apt", "install", "-y", "curl"])

    @regression_test
    @unittest.skipIf(
        sys.platform.startswith("win"), "System dependency test skipped on Windows"
    )
    @patch("subprocess.run")
    def test_verify_installation_success(self, mock_run):
        """Test successful installation verification."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["apt-cache", "policy", "curl"],
            returncode=0,
            stdout="curl:\n  Installed: 7.68.0-1ubuntu2.7\n  Candidate: 7.68.0-1ubuntu2.7\n  Version table:\n *** 7.68.0-1ubuntu2.7 500\n        500 http://archive.ubuntu.com/ubuntu focal-updates/main amd64 Packages\n        100 /var/lib/dpkg/status",
            stderr="",
        )

        version = self.installer._verify_installation("curl")
        self.assertTrue(
            isinstance(version, str) and len(version) > 0,
            f"Expected a non-empty version string, got: {version}",
        )

    @regression_test
    @patch("subprocess.run")
    def test_verify_installation_failure(self, mock_run):
        """Test installation verification when package not found."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["dpkg-query"])

        version = self.installer._verify_installation("nonexistent")
        self.assertIsNone(version)

    @regression_test
    def test_parse_apt_error_permission_denied(self):
        """Test parsing permission denied error."""
        error = subprocess.CalledProcessError(
            1,
            ["apt", "install", "curl"],
            stderr="E: Could not open lock file - permission denied",
        )
        wrapped_error = InstallationError(
            str(error.stderr),
            dependency_name="curl",
            error_code="APT_INSTALL_FAILED",
            cause=error,
        )
        message = self.installer._parse_apt_error(wrapped_error)
        self.assertIn("permission denied", message.lower())
        self.assertIn("sudo", message.lower())

    @regression_test
    def test_parse_apt_error_package_not_found(self):
        """Test parsing package not found error."""
        error = subprocess.CalledProcessError(
            100,
            ["apt", "install", "nonexistent"],
            stderr="E: Unable to locate package nonexistent",
        )
        wrapped_error = InstallationError(
            str(error.stderr),
            dependency_name="nonexistent",
            error_code="APT_INSTALL_FAILED",
            cause=error,
        )
        message = self.installer._parse_apt_error(wrapped_error)
        self.assertIn("package not found", message.lower())
        self.assertIn("apt update", message.lower())

    @regression_test
    def test_parse_apt_error_generic(self):
        """Test parsing generic apt error."""
        error = subprocess.CalledProcessError(
            1, ["apt", "install", "curl"], stderr="Some unknown error occurred"
        )
        wrapped_error = InstallationError(
            str(error.stderr),
            dependency_name="curl",
            error_code="APT_INSTALL_FAILED",
            cause=error,
        )
        message = self.installer._parse_apt_error(wrapped_error)
        self.assertIn("apt command failed", message.lower())
        self.assertIn("unknown error", message.lower())

    @regression_test
    @patch.object(SystemInstaller, "validate_dependency")
    @patch.object(SystemInstaller, "_build_apt_command")
    @patch.object(SystemInstaller, "_run_apt_subprocess")
    @patch.object(SystemInstaller, "_verify_installation")
    def test_install_success(
        self, mock_verify, mock_execute, mock_build, mock_validate
    ):
        """Test successful installation."""
        # Setup mocks
        mock_validate.return_value = True
        mock_build.return_value = ["apt", "install", "curl"]
        mock_execute.return_value = 0
        mock_verify.return_value = "7.68.0"

        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        # Test with progress callback
        progress_calls = []

        def progress_callback(operation, progress, message):
            progress_calls.append((operation, progress, message))

        result = self.installer.install(
            dependency, self.mock_context, progress_callback
        )

        # Verify result
        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertEqual(result.installed_version, "7.68.0")
        self.assertEqual(result.metadata["package_manager"], "apt")

        # Verify progress was reported
        self.assertEqual(len(progress_calls), 4)
        self.assertEqual(progress_calls[0][1], 0.0)  # Start
        self.assertEqual(progress_calls[-1][1], 100.0)  # Complete

    @regression_test
    @patch.object(SystemInstaller, "validate_dependency")
    def test_install_invalid_dependency(self, mock_validate):
        """Test installation with invalid dependency."""
        mock_validate.return_value = False

        dependency = {"name": "curl", "version_constraint": "invalid"}

        with self.assertRaises(InstallationError) as exc_info:
            self.installer.install(dependency, self.mock_context)

        self.assertEqual(exc_info.exception.error_code, "INVALID_DEPENDENCY")
        self.assertIn("Invalid dependency", str(exc_info.exception))

    @regression_test
    @patch.object(SystemInstaller, "validate_dependency")
    @patch.object(SystemInstaller, "_build_apt_command")
    @patch.object(SystemInstaller, "_run_apt_subprocess")
    def test_install_apt_failure(self, mock_execute, mock_build, mock_validate):
        """Test installation failure due to apt command error."""
        mock_validate.return_value = True
        mock_build.return_value = ["apt", "install", "curl"]
        # Simulate failure on the first call (apt-get update)
        mock_execute.side_effect = [1, 0]

        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        with self.assertRaises(InstallationError) as exc_info:
            self.installer.install(dependency, self.mock_context)

        # Accept either update or install failure
        self.assertEqual(exc_info.exception.error_code, "APT_UPDATE_FAILED")
        self.assertEqual(exc_info.exception.dependency_name, "curl")

        # Now simulate update success but install failure
        mock_execute.side_effect = [0, 1]
        with self.assertRaises(InstallationError) as exc_info2:
            self.installer.install(dependency, self.mock_context)
        self.assertEqual(exc_info2.exception.error_code, "APT_INSTALL_FAILED")
        self.assertEqual(exc_info2.exception.dependency_name, "curl")

    @regression_test
    @patch.object(SystemInstaller, "validate_dependency")
    @patch.object(SystemInstaller, "_simulate_installation")
    def test_install_simulation_mode(self, mock_simulate, mock_validate):
        """Test installation in simulation mode."""
        mock_validate.return_value = True
        mock_simulate.return_value = InstallationResult(
            dependency_name="curl",
            status=InstallationStatus.COMPLETED,
            metadata={"simulation": True},
        )

        self.mock_context.simulation_mode = True
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        result = self.installer.install(dependency, self.mock_context)

        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertTrue(result.metadata["simulation"])
        mock_simulate.assert_called_once()

    @regression_test
    @unittest.skipIf(
        sys.platform.startswith("win"), "System dependency test skipped on Windows"
    )
    @patch.object(SystemInstaller, "_run_apt_subprocess")
    def test_simulate_installation_success(self, mock_run):
        """Test successful installation simulation."""
        mock_run.return_value = 0

        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        result = self.installer._simulate_installation(dependency, self.mock_context)

        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertTrue(result.metadata["simulation"])

    @regression_test
    @patch.object(SystemInstaller, "_run_apt_subprocess")
    def test_simulate_installation_failure(self, mock_run):
        """Test installation simulation failure."""
        mock_run.return_value = 1
        mock_run.side_effect = InstallationError(
            "Simulation failed",
            dependency_name="nonexistent",
            error_code="APT_SIMULATION_FAILED",
        )

        dependency = {
            "name": "nonexistent",
            "version_constraint": ">=1.0.0",
            "package_manager": "apt",
        }

        with self.assertRaises(InstallationError) as exc_info:
            self.installer._simulate_installation(dependency, self.mock_context)

        self.assertEqual(exc_info.exception.dependency_name, "nonexistent")
        self.assertEqual(exc_info.exception.error_code, "APT_SIMULATION_FAILED")

    @regression_test
    @patch.object(SystemInstaller, "_run_apt_subprocess", return_value=0)
    def test_uninstall_success(self, mock_execute):
        """Test successful uninstall."""

        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        result = self.installer.uninstall(dependency, self.mock_context)

        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertEqual(result.metadata["operation"], "uninstall")

    @regression_test
    @patch.object(SystemInstaller, "_run_apt_subprocess", return_value=0)
    def test_uninstall_automated(self, mock_execute):
        """Test uninstall in automated mode."""

        self.mock_context.extra_config = {"automated": True}
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        result = self.installer.uninstall(dependency, self.mock_context)

        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        # Verify -y flag is in the command (final command is in the metadata)
        self.assertIn("-y", result.metadata.get("command_executed", []))

    @regression_test
    @patch.object(SystemInstaller, "_simulate_uninstall")
    def test_uninstall_simulation_mode(self, mock_simulate):
        """Test uninstall in simulation mode."""
        mock_simulate.return_value = InstallationResult(
            dependency_name="curl",
            status=InstallationStatus.COMPLETED,
            metadata={"operation": "uninstall", "simulation": True},
        )

        self.mock_context.simulation_mode = True
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        result = self.installer.uninstall(dependency, self.mock_context)

        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertTrue(result.metadata["simulation"])
        mock_simulate.assert_called_once()


class TestSystemInstallerIntegration(unittest.TestCase):
    """Integration tests for SystemInstaller using actual system dependencies."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.installer = SystemInstaller()
        self.test_context = InstallationContext(
            environment_path=Path("/tmp/test_env"),
            environment_name="integration_test",
            simulation_mode=True,  # Always use simulation for integration tests
            extra_config={"automated": True},
        )

    @integration_test(scope="system")
    def test_validate_real_system_dependency(self):
        """Test validation with real system dependency from dummy package."""
        # This mimics the dependency from system_dep_pkg
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        self.assertTrue(self.installer.validate_dependency(dependency))

    @integration_test(scope="system")
    @patch.object(SystemInstaller, "_is_platform_supported")
    @patch.object(SystemInstaller, "_is_apt_available")
    def test_can_install_real_dependency(
        self, mock_apt_available, mock_platform_supported
    ):
        """Test can_install with real system dependency."""
        mock_platform_supported.return_value = True
        mock_apt_available.return_value = True

        dependency = {
            "type": "system",
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        self.assertTrue(self.installer.can_install(dependency))

    @integration_test(scope="system")
    @unittest.skipIf(
        sys.platform.startswith("win"), "System dependency test skipped on Windows"
    )
    def test_simulate_curl_installation(self):
        """Test simulating installation of curl package."""
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        # Mock subprocess for simulation
        with patch.object(self.installer, "_run_apt_subprocess") as mock_run:
            mock_run.return_value = 0

            result = self.installer._simulate_installation(
                dependency, self.test_context
            )

            self.assertEqual(result.dependency_name, "curl")
            self.assertEqual(result.status, InstallationStatus.COMPLETED)
            self.assertTrue(result.metadata["simulation"])

    @integration_test(scope="system")
    def test_get_installation_info(self):
        """Test getting installation info for system dependency."""
        dependency = {
            "type": "system",
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        with patch.object(self.installer, "can_install", return_value=True):
            info = self.installer.get_installation_info(dependency, self.test_context)

            self.assertEqual(info["installer_type"], "system")
            self.assertEqual(info["dependency_name"], "curl")
            self.assertTrue(info["supported"])

    @integration_test(scope="system")
    @patch.object(SystemInstaller, "_run_apt_subprocess", return_value=0)
    def test_install_real_dependency(self, mock_run):
        """Test installing a system dependency (mocked subprocess)."""
        dependency = {
            "name": "sl",
            "version_constraint": ">=5.02",
            "package_manager": "apt",
        }

        result = self.installer.install(dependency, self.test_context)

        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertTrue(result.metadata["automated"])
        mock_run.assert_called()

    @integration_test(scope="system")
    @patch.object(SystemInstaller, "_run_apt_subprocess", return_value=0)
    def test_install_integration_with_real_subprocess(self, mock_run):
        """Test install method with mocked _run_apt_subprocess execution.

        This test ensures the install flow works correctly in simulation mode
        with subprocess calls mocked.
        """
        dependency = {
            "name": "curl",
            "version_constraint": ">=7.0.0",
            "package_manager": "apt",
        }

        # Create a test context that uses simulation mode
        test_context = InstallationContext(
            environment_path=Path("/tmp/test_env"),
            environment_name="integration_test",
            simulation_mode=True,
            extra_config={"automated": True},
        )

        result = self.installer.install(dependency, test_context)

        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertTrue(result.metadata["simulation"])
        self.assertEqual(result.metadata["package_manager"], "apt")
        self.assertTrue(result.metadata["automated"])
        mock_run.assert_called()

    @integration_test(scope="system")
    @patch("subprocess.Popen")
    def test_run_apt_subprocess_direct_integration(self, mock_popen):
        """Test _run_apt_subprocess directly with mocked subprocess.

        This test verifies that _run_apt_subprocess correctly handles
        subprocess calls and returns the expected return codes.
        """
        # Mock the Popen process
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "")
        mock_process.wait.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Test with apt-cache policy (read-only command)
        cmd = ["apt-cache", "policy", "curl"]
        returncode = self.installer._run_apt_subprocess(cmd)
        self.assertEqual(returncode, 0)

        # Test with apt-get dry-run (safe simulation command)
        cmd = ["apt-get", "install", "--dry-run", "-y", "curl"]
        returncode = self.installer._run_apt_subprocess(cmd)
        self.assertEqual(returncode, 0)

        # Test with invalid package (apt-cache policy doesn't fail)
        cmd = ["apt-cache", "policy", "nonexistent-package-12345"]
        returncode = self.installer._run_apt_subprocess(cmd)
        self.assertEqual(returncode, 0)

    @integration_test(scope="system")
    @patch.object(SystemInstaller, "_run_apt_subprocess", return_value=0)
    def test_install_with_version_constraint_integration(self, mock_run):
        """Test install method with version constraints (mocked subprocess)."""
        # Test with exact version constraint
        dependency = {
            "name": "curl",
            "version_constraint": "==7.68.0",
            "package_manager": "apt",
        }

        test_context = InstallationContext(
            environment_path=Path("/tmp/test_env"),
            environment_name="integration_test",
            simulation_mode=True,
            extra_config={"automated": True},
        )

        result = self.installer.install(dependency, test_context)

        self.assertEqual(result.dependency_name, "curl")
        self.assertEqual(result.status, InstallationStatus.COMPLETED)
        self.assertTrue(result.metadata["simulation"])
        # Check that the command includes the version constraint
        self.assertIn("curl", result.metadata["command_simulated"])
        mock_run.assert_called()

    @integration_test(scope="system")
    @patch("subprocess.Popen")
    def test_error_handling_in_run_apt_subprocess(self, mock_popen):
        """Test error handling in _run_apt_subprocess with invalid commands."""
        # Simulate FileNotFoundError for a nonexistent command
        mock_popen.side_effect = FileNotFoundError(
            "[Errno 2] No such file or directory: 'nonexistent-command-12345'"
        )

        cmd = ["nonexistent-command-12345"]

        with self.assertRaises(InstallationError) as exc_info:
            self.installer._run_apt_subprocess(cmd)

        self.assertEqual(exc_info.exception.error_code, "APT_SUBPROCESS_ERROR")
        self.assertIn(
            "Unexpected error running apt command", exc_info.exception.message
        )
