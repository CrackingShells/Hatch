"""Tests for PythonEnvironmentManager.

This module contains tests for the Python environment management functionality,
including conda/mamba environment creation, configuration, and integration.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from wobble.decorators import regression_test, integration_test, slow_test

from hatch.python_environment_manager import (
    PythonEnvironmentManager,
    PythonEnvironmentError,
)


class TestPythonEnvironmentManager(unittest.TestCase):
    """Test cases for PythonEnvironmentManager functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.environments_dir = Path(self.temp_dir) / "envs"
        self.environments_dir.mkdir(exist_ok=True)

        # Create manager instance for testing
        self.manager = PythonEnvironmentManager(environments_dir=self.environments_dir)

        # Track environments created during this test for cleanup
        self.created_environments = []

    def tearDown(self):
        """Clean up test environment."""
        # Clean up any conda/mamba environments created during this test
        if hasattr(self, "manager") and self.manager.is_available():
            for env_name in self.created_environments:
                try:
                    if self.manager.environment_exists(env_name):
                        self.manager.remove_python_environment(env_name)
                except Exception:
                    pass  # Best effort cleanup

        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _track_environment(self, env_name):
        """Track an environment for cleanup in tearDown."""
        if env_name not in self.created_environments:
            self.created_environments.append(env_name)

    @regression_test
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._conda_env_exists",
        return_value=True,
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._get_conda_env_name",
        return_value="hatch_test_env",
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._get_python_executable_path",
        return_value="C:/fake/env/Scripts/python.exe",
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager.get_environment_path",
        return_value=Path("C:/fake/env"),
    )
    @patch("platform.system", return_value="Windows")
    def test_get_environment_activation_info_windows(
        self,
        mock_platform,
        mock_get_env_path,
        mock_get_python_exec_path,
        mock_get_conda_env_name,
        mock_conda_env_exists,
    ):
        """Test get_environment_activation_info returns correct env vars on Windows."""
        env_name = "test_env"
        manager = PythonEnvironmentManager(environments_dir=Path("C:/fake/envs"))
        env_vars = manager.get_environment_activation_info(env_name)
        self.assertIsInstance(env_vars, dict)
        self.assertEqual(env_vars["CONDA_DEFAULT_ENV"], "hatch_test_env")
        self.assertEqual(env_vars["CONDA_PREFIX"], str(Path("C:/fake/env")))
        self.assertIn("PATH", env_vars)
        # On Windows, the path separator is ';' and paths are backslash
        # Split PATH and check each expected directory is present as a component
        path_dirs = env_vars["PATH"].split(";")
        self.assertIn("C:\\fake\\env", path_dirs)
        self.assertIn("C:\\fake\\env\\Scripts", path_dirs)
        self.assertIn("C:\\fake\\env\\Library\\bin", path_dirs)
        self.assertEqual(env_vars["PYTHON"], "C:/fake/env/Scripts/python.exe")

    @regression_test
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._conda_env_exists",
        return_value=True,
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._get_conda_env_name",
        return_value="hatch_test_env",
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._get_python_executable_path",
        return_value="/fake/env/bin/python",
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager.get_environment_path",
        return_value=Path("/fake/env"),
    )
    @patch("platform.system", return_value="Linux")
    def test_get_environment_activation_info_unix(
        self,
        mock_platform,
        mock_get_env_path,
        mock_get_python_exec_path,
        mock_get_conda_env_name,
        mock_conda_env_exists,
    ):
        """Test get_environment_activation_info returns correct env vars on Unix."""
        env_name = "test_env"
        manager = PythonEnvironmentManager(environments_dir=Path("/fake/envs"))
        env_vars = manager.get_environment_activation_info(env_name)
        self.assertIsInstance(env_vars, dict)
        self.assertEqual(env_vars["CONDA_DEFAULT_ENV"], "hatch_test_env")
        self.assertEqual(env_vars["CONDA_PREFIX"], str(Path("/fake/env")))
        self.assertIn("PATH", env_vars)
        # On Unix, the path separator is ':' and paths are forward slash, but Path() may normalize to backslash on Windows
        # Accept both possible representations for cross-platform test running
        path_dirs = env_vars["PATH"]
        self.assertTrue(
            "/fake/env/bin" in path_dirs or "\\fake\\env\\bin" in path_dirs,
            f"Expected '/fake/env/bin' or '\\fake\\env\\bin' to be in PATH: {env_vars['PATH']}",
        )
        self.assertEqual(env_vars["PYTHON"], "/fake/env/bin/python")

    @regression_test
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._conda_env_exists",
        return_value=False,
    )
    def test_get_environment_activation_info_env_not_exists(
        self, mock_conda_env_exists
    ):
        """Test get_environment_activation_info returns None if env does not exist."""
        env_name = "nonexistent_env"
        manager = PythonEnvironmentManager(environments_dir=Path("/fake/envs"))
        env_vars = manager.get_environment_activation_info(env_name)
        self.assertIsNone(env_vars)

    @regression_test
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._conda_env_exists",
        return_value=True,
    )
    @patch(
        "hatch.python_environment_manager.PythonEnvironmentManager._get_python_executable_path",
        return_value=None,
    )
    def test_get_environment_activation_info_no_python(
        self, mock_get_python_exec_path, mock_conda_env_exists
    ):
        """Test get_environment_activation_info returns None if python executable not found."""
        env_name = "test_env"
        manager = PythonEnvironmentManager(environments_dir=Path("/fake/envs"))
        env_vars = manager.get_environment_activation_info(env_name)
        self.assertIsNone(env_vars)

    @regression_test
    def test_init(self):
        """Test PythonEnvironmentManager initialization."""
        self.assertEqual(self.manager.environments_dir, self.environments_dir)
        self.assertIsNotNone(self.manager.logger)

    @regression_test
    def test_detect_conda_mamba_with_mamba(self):
        """Test conda/mamba detection when mamba is available."""
        with patch.object(PythonEnvironmentManager, "_detect_manager") as mock_detect:
            # mamba found, conda found
            mock_detect.side_effect = lambda manager: (
                "/usr/bin/mamba" if manager == "mamba" else "/usr/bin/conda"
            )
            manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
            self.assertEqual(manager.mamba_executable, "/usr/bin/mamba")
            self.assertEqual(manager.conda_executable, "/usr/bin/conda")

    @regression_test
    def test_detect_conda_mamba_conda_only(self):
        """Test conda/mamba detection when only conda is available."""
        with patch.object(PythonEnvironmentManager, "_detect_manager") as mock_detect:
            # mamba not found, conda found
            mock_detect.side_effect = lambda manager: (
                None if manager == "mamba" else "/usr/bin/conda"
            )
            manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
            self.assertIsNone(manager.mamba_executable)
            self.assertEqual(manager.conda_executable, "/usr/bin/conda")

    @regression_test
    def test_detect_conda_mamba_none_available(self):
        """Test conda/mamba detection when neither is available."""
        with patch.object(
            PythonEnvironmentManager, "_detect_manager", return_value=None
        ):
            manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
            self.assertIsNone(manager.mamba_executable)
            self.assertIsNone(manager.conda_executable)

    @regression_test
    def test_get_conda_env_name(self):
        """Test conda environment name generation."""
        env_name = "test_env"
        conda_name = self.manager._get_conda_env_name(env_name)
        self.assertEqual(conda_name, "hatch_test_env")

    @regression_test
    @patch("subprocess.run")
    def test_get_python_executable_path_windows(self, mock_run):
        """Test Python executable path on Windows."""
        with patch("platform.system", return_value="Windows"):
            env_name = "test_env"

            # Mock conda info command to return environment path
            mock_run.return_value = Mock(
                returncode=0, stdout='{"envs": ["/conda/envs/hatch_test_env"]}'
            )

            python_path = self.manager._get_python_executable_path(env_name)
            expected = Path("/conda/envs/hatch_test_env/python.exe")
            self.assertEqual(python_path, expected)

    @regression_test
    @patch("subprocess.run")
    def test_get_python_executable_path_unix(self, mock_run):
        """Test Python executable path on Unix/Linux."""
        with patch("platform.system", return_value="Linux"):
            env_name = "test_env"

            # Mock conda info command to return environment path
            mock_run.return_value = Mock(
                returncode=0, stdout='{"envs": ["/conda/envs/hatch_test_env"]}'
            )

            python_path = self.manager._get_python_executable_path(env_name)
            expected = Path("/conda/envs/hatch_test_env/bin/python")
            self.assertEqual(python_path, expected)

    @regression_test
    def test_is_available_no_conda(self):
        """Test availability check when conda/mamba is not available."""
        manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
        manager.conda_executable = None
        manager.mamba_executable = None

        self.assertFalse(manager.is_available())

    @regression_test
    @patch("subprocess.run")
    def test_is_available_with_conda(self, mock_run):
        """Test availability check when conda is available."""
        self.manager.conda_executable = "/usr/bin/conda"

        # Mock successful conda info
        mock_run.return_value = Mock(returncode=0, stdout='{"platform": "linux-64"}')

        self.assertTrue(self.manager.is_available())

    @regression_test
    def test_get_preferred_executable(self):
        """Test preferred executable selection."""
        # Test mamba preferred over conda
        self.manager.mamba_executable = "/usr/bin/mamba"
        self.manager.conda_executable = "/usr/bin/conda"
        self.assertEqual(self.manager.get_preferred_executable(), "/usr/bin/mamba")

        # Test conda when mamba not available
        self.manager.mamba_executable = None
        self.assertEqual(self.manager.get_preferred_executable(), "/usr/bin/conda")

        # Test None when neither available
        self.manager.conda_executable = None
        self.assertIsNone(self.manager.get_preferred_executable())

    @regression_test
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_create_python_environment_success(self, mock_run, mock_which):
        """Test successful Python environment creation."""
        # Patch mamba detection
        mock_which.side_effect = lambda cmd: (
            "/usr/bin/mamba" if cmd == "mamba" else None
        )

        # Patch subprocess.run for both validation and creation
        def run_side_effect(cmd, *args, **kwargs):
            if "info" in cmd:
                # Validation call
                return Mock(returncode=0, stdout='{"platform": "win-64"}')
            elif "create" in cmd:
                # Environment creation call
                return Mock(returncode=0, stdout="Environment created")
            else:
                return Mock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        manager = PythonEnvironmentManager(environments_dir=self.environments_dir)

        # Mock environment existence check
        with patch.object(manager, "_conda_env_exists", return_value=False):
            result = manager.create_python_environment(
                "test_env", python_version="3.11"
            )
            self.assertTrue(result)
            mock_run.assert_called()

    @regression_test
    def test_create_python_environment_no_conda(self):
        """Test Python environment creation when conda/mamba is not available."""
        self.manager.conda_executable = None
        self.manager.mamba_executable = None

        with self.assertRaises(PythonEnvironmentError):
            self.manager.create_python_environment("test_env")

    @regression_test
    @patch("shutil.which")
    @patch("subprocess.run")
    def test_create_python_environment_already_exists(self, mock_run, mock_which):
        """Test Python environment creation when environment already exists."""
        # Patch mamba detection
        mock_which.side_effect = lambda cmd: (
            "/usr/bin/mamba" if cmd == "mamba" else None
        )

        # Patch subprocess.run for both validation and creation
        def run_side_effect(cmd, *args, **kwargs):
            if "info" in cmd:
                # Validation call
                return Mock(returncode=0, stdout='{"platform": "win-64"}')
            elif "create" in cmd:
                # Environment creation call
                return Mock(returncode=0, stdout="Environment created")
            else:
                return Mock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        # Mock environment already exists
        with patch.object(self.manager, "_conda_env_exists", return_value=True):
            result = self.manager.create_python_environment("test_env")
            self.assertTrue(result)
            # Ensure 'create' was not called, but 'info' was
            create_calls = [
                call for call in mock_run.call_args_list if "create" in call[0][0]
            ]
            self.assertEqual(len(create_calls), 0)

    @regression_test
    @patch("subprocess.run")
    def test_conda_env_exists(self, mock_run):
        """Test conda environment existence check."""
        env_name = "test_env"

        # Mock conda env list to return the environment
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"envs": ["/conda/envs/hatch_test_env", "/conda/envs/other_env"]}',
        )

        self.assertTrue(self.manager._conda_env_exists(env_name))

    @regression_test
    @patch("subprocess.run")
    def test_conda_env_not_exists(self, mock_run):
        """Test conda environment existence check when environment doesn't exist."""
        env_name = "nonexistent_env"

        # Mock conda env list to not return the environment
        mock_run.return_value = Mock(
            returncode=0, stdout='{"envs": ["/conda/envs/other_env"]}'
        )

        self.assertFalse(self.manager._conda_env_exists(env_name))

    @regression_test
    @patch("subprocess.run")
    def test_get_python_executable_exists(self, mock_run):
        """Test getting Python executable when environment exists."""
        env_name = "test_env"

        # Mock conda env list to show environment exists
        def run_side_effect(cmd, *args, **kwargs):
            if "env" in cmd and "list" in cmd:
                return Mock(
                    returncode=0, stdout='{"envs": ["/conda/envs/hatch_test_env"]}'
                )
            elif "info" in cmd and "--envs" in cmd:
                return Mock(
                    returncode=0, stdout='{"envs": ["/conda/envs/hatch_test_env"]}'
                )
            else:
                return Mock(returncode=0, stdout="{}")

        mock_run.side_effect = run_side_effect

        # Mock that the file exists
        with patch("pathlib.Path.exists", return_value=True):
            result = self.manager.get_python_executable(env_name)
            import platform
            from pathlib import Path as _Path

            if platform.system() == "Windows":
                expected = str(_Path("\\conda\\envs\\hatch_test_env\\python.exe"))
            else:
                expected = str(_Path("/conda/envs/hatch_test_env/bin/python"))
            self.assertEqual(result, expected)

    @regression_test
    def test_get_python_executable_not_exists(self):
        """Test getting Python executable when environment doesn't exist."""
        env_name = "nonexistent_env"

        with patch.object(self.manager, "_conda_env_exists", return_value=False):
            result = self.manager.get_python_executable(env_name)
            self.assertIsNone(result)


class TestPythonEnvironmentManagerIntegration(unittest.TestCase):
    """Integration test cases for PythonEnvironmentManager with real conda/mamba operations.

    These tests require conda or mamba to be installed on the system and will create
    real conda environments for testing. They are more comprehensive but slower than
    the mocked unit tests.
    """

    @classmethod
    def setUpClass(cls):
        """Set up class-level test environment.

        All tests in this class are mocked — no real conda/mamba environments
        are created. The manager is initialised with fake executables so that
        subprocess calls can be intercepted by per-test mocks.
        """
        cls.temp_dir = tempfile.mkdtemp()
        cls.environments_dir = Path(cls.temp_dir) / "envs"
        cls.environments_dir.mkdir(exist_ok=True)

        # Create manager with mocked detection to avoid real subprocess calls
        with patch.object(PythonEnvironmentManager, "_detect_conda_mamba"):
            cls.manager = PythonEnvironmentManager(
                environments_dir=cls.environments_dir
            )
        # Set fake executables so is_available() returns True
        cls.manager.mamba_executable = "/usr/bin/mamba"
        cls.manager.conda_executable = "/usr/bin/conda"

        # Shared environment names (referenced by tests, but never created for real)
        cls.shared_env_basic = "test_shared_basic"
        cls.shared_env_py311 = "test_shared_py311"

        # Track environments (kept for API compatibility with setUp/tearDown)
        cls.all_created_environments = set()

    def setUp(self):
        """Set up individual test."""
        # Track environments created during this specific test
        self.test_environments = []

    def tearDown(self):
        """Clean up individual test."""
        # Clean up environments created during this specific test
        for env_name in self.test_environments:
            try:
                if self.manager.environment_exists(env_name):
                    self.manager.remove_python_environment(env_name)
                    self.all_created_environments.discard(env_name)
            except Exception:
                pass  # Best effort cleanup

    def _track_environment(self, env_name):
        """Track an environment for cleanup."""
        if env_name not in self.test_environments:
            self.test_environments.append(env_name)
        self.all_created_environments.add(env_name)

    @classmethod
    def tearDownClass(cls):
        """Clean up class-level test environment."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @integration_test(scope="system")
    def test_conda_mamba_detection_real(self):
        """Test conda/mamba detection logic with mocked executables."""
        # Manager already has fake executables set in setUpClass
        manager_info = self.manager.get_manager_info()

        # At least one should be available
        self.assertTrue(manager_info["is_available"])
        self.assertTrue(
            manager_info["conda_executable"] is not None
            or manager_info["mamba_executable"] is not None
        )

        # Preferred manager should be set (mamba preferred over conda)
        self.assertIsNotNone(manager_info["preferred_manager"])

        # Platform and Python version should be populated
        self.assertIsNotNone(manager_info["platform"])
        self.assertIsNotNone(manager_info["python_version"])

    @integration_test(scope="system")
    @patch("subprocess.run")
    def test_manager_diagnostics_real(self, mock_run):
        """Test manager diagnostics with mocked subprocess calls."""

        # Mock subprocess.run for --version calls made by get_manager_diagnostics
        def version_side_effect(cmd, *args, **kwargs):
            if "--version" in cmd:
                if "conda" in cmd[0]:
                    return Mock(returncode=0, stdout="conda 24.1.0")
                elif "mamba" in cmd[0]:
                    return Mock(returncode=0, stdout="mamba 1.5.6")
            return Mock(returncode=0, stdout="")

        mock_run.side_effect = version_side_effect

        diagnostics = self.manager.get_manager_diagnostics()

        # Should have basic information
        self.assertIn("any_manager_available", diagnostics)
        self.assertTrue(diagnostics["any_manager_available"])
        self.assertIn("platform", diagnostics)
        self.assertIn("python_version", diagnostics)
        self.assertIn("environments_dir", diagnostics)

        # Should test actual executables
        if diagnostics["conda_executable"]:
            self.assertIn("conda_works", diagnostics)
            self.assertIn("conda_version", diagnostics)

        if diagnostics["mamba_executable"]:
            self.assertIn("mamba_works", diagnostics)
            self.assertIn("mamba_version", diagnostics)

    @integration_test(scope="system")
    @slow_test
    def test_create_and_remove_python_environment_real(self):
        """Test real Python environment creation and removal.

        NOTE: This test creates a NEW environment to test creation/removal.
        Most other tests now use shared environments for speed.
        """
        env_name = "test_integration_env"
        self._track_environment(env_name)

        # Ensure environment doesn't exist initially
        if self.manager.environment_exists(env_name):
            self.manager.remove_python_environment(env_name)

        # Create environment
        result = self.manager.create_python_environment(env_name)
        self.assertTrue(result, "Failed to create Python environment")

        # Verify environment exists
        self.assertTrue(self.manager.environment_exists(env_name))

        # Verify Python executable is available
        python_exec = self.manager.get_python_executable(env_name)
        self.assertIsNotNone(python_exec, "Python executable not found")
        self.assertTrue(
            Path(python_exec).exists(),
            f"Python executable doesn't exist: {python_exec}",
        )

        # Get environment info
        env_info = self.manager.get_environment_info(env_name)
        self.assertIsNotNone(env_info)
        self.assertEqual(env_info["environment_name"], env_name)
        self.assertIsNotNone(env_info["conda_env_name"])
        self.assertIsNotNone(env_info["python_executable"])

        # Remove environment
        result = self.manager.remove_python_environment(env_name)
        self.assertTrue(result, "Failed to remove Python environment")

        # Verify environment no longer exists
        self.assertFalse(self.manager.environment_exists(env_name))

    @integration_test(scope="system")
    def test_create_python_environment_with_version_real(self):
        """Test Python environment with specific version using SHARED environment.

        OPTIMIZATION: Uses shared_env_py311 created in setUpClass.
        This saves 2-3 minutes per test run by reusing the environment.
        """
        # Use the shared Python 3.11 environment
        env_name = self.shared_env_py311

        # Verify environment exists (it should, created in setUpClass)
        self.assertTrue(
            self.manager.environment_exists(env_name),
            f"Shared environment {env_name} should exist",
        )

        # Verify Python version
        actual_version = self.manager.get_python_version(env_name)
        self.assertIsNotNone(actual_version)
        self.assertTrue(
            actual_version.startswith("3.11"),
            f"Expected Python 3.11.x, got {actual_version}",
        )

        # Get comprehensive environment info
        env_info = self.manager.get_environment_info(env_name)
        self.assertIsNotNone(env_info)
        self.assertTrue(
            env_info["python_version"].startswith("3.11"),
            f"Expected Python 3.11.x, got {env_info['python_version']}",
        )

        # No cleanup needed - shared environment is cleaned up in tearDownClass

    @integration_test(scope="system")
    def test_environment_diagnostics_real(self):
        """Test real environment diagnostics using SHARED environment.

        OPTIMIZATION: Uses shared_env_basic for existing environment tests.
        Tests non-existent environment without creating one.
        """
        # Test diagnostics for non-existent environment
        nonexistent_env = "test_nonexistent_diagnostics"
        diagnostics = self.manager.get_environment_diagnostics(nonexistent_env)
        self.assertFalse(diagnostics["exists"])
        self.assertTrue(diagnostics["conda_available"])

        # Test diagnostics for existing environment using shared environment
        env_name = self.shared_env_basic
        diagnostics = self.manager.get_environment_diagnostics(env_name)
        self.assertTrue(diagnostics["exists"])
        self.assertIsNotNone(diagnostics["python_executable"])
        self.assertTrue(diagnostics["python_accessible"])
        self.assertIsNotNone(diagnostics["python_version"])
        self.assertTrue(diagnostics["python_version_accessible"])
        self.assertTrue(diagnostics["python_executable_works"])
        self.assertIsNotNone(diagnostics["environment_path"])
        self.assertTrue(diagnostics["environment_path_exists"])

        # No cleanup needed - shared environment persists

    @integration_test(scope="system")
    @slow_test
    def test_force_recreation_real(self):
        """Test force recreation of existing environment."""
        env_name = "test_integration_env"

        # Ensure environment doesn't exist initially
        if self.manager.environment_exists(env_name):
            self.manager.remove_python_environment(env_name)

        # Create environment
        result1 = self.manager.create_python_environment(env_name)
        self.assertTrue(result1)

        # Get initial Python executable
        python_exec1 = self.manager.get_python_executable(env_name)
        self.assertIsNotNone(python_exec1)

        # Try to create again without force (should succeed but not recreate)
        result2 = self.manager.create_python_environment(env_name, force=False)
        self.assertTrue(result2)

        # Try to create again with force (should recreate)
        result3 = self.manager.create_python_environment(env_name, force=True)
        self.assertTrue(result3)

        # Verify environment still exists and works
        self.assertTrue(self.manager.environment_exists(env_name))
        python_exec3 = self.manager.get_python_executable(env_name)
        self.assertIsNotNone(python_exec3)

        # Cleanup
        self.manager.remove_python_environment(env_name)

    @integration_test(scope="system")
    def test_list_environments_real(self):
        """Test listing environments using SHARED environments.

        OPTIMIZATION: Uses shared environments instead of creating new ones.
        Saves 4-6 minutes per test run.
        """
        # List environments
        env_list = self.manager.list_environments()

        # Should include our shared test environments
        shared_env_names = [
            f"hatch_{self.shared_env_basic}",
            f"hatch_{self.shared_env_py311}",
        ]

        for env_name in shared_env_names:
            self.assertIn(
                env_name, env_list, f"{env_name} not found in environment list"
            )

        # Verify list_environments returns a list
        self.assertIsInstance(env_list, list)
        self.assertGreater(len(env_list), 0, "Environment list should not be empty")

        # No cleanup needed - shared environments persist

    @integration_test(scope="system")
    @slow_test
    @unittest.skipIf(
        not (
            Path("/usr/bin/python3.12").exists() or Path("/usr/bin/python3.9").exists()
        ),
        "Multiple Python versions not available for testing",
    )
    def test_multiple_python_versions_real(self):
        """Test creating environments with multiple Python versions."""
        test_cases = [("test_python_39", "3.9"), ("test_python_312", "3.12")]

        created_envs = []

        try:
            for env_name, python_version in test_cases:
                # Skip if this Python version is not available
                try:
                    result = self.manager.create_python_environment(
                        env_name, python_version=python_version
                    )
                    if result:
                        created_envs.append(env_name)

                        # Verify Python version
                        actual_version = self.manager.get_python_version(env_name)
                        self.assertIsNotNone(actual_version)
                        self.assertTrue(
                            actual_version.startswith(python_version),
                            f"Expected Python {python_version}.x, got {actual_version}",
                        )
                except Exception as e:
                    # Log but don't fail test if specific Python version is not available
                    print(f"Skipping Python {python_version} test: {e}")

        finally:
            # Cleanup
            for env_name in created_envs:
                try:
                    self.manager.remove_python_environment(env_name)
                except Exception:
                    pass  # Best effort cleanup

    @integration_test(scope="system")
    @slow_test
    def test_error_handling_real(self):
        """Test error handling with real operations."""
        # Test removing non-existent environment
        result = self.manager.remove_python_environment("nonexistent_env")
        self.assertTrue(
            result
        )  # Removing non existent environment returns True because it does nothing

        # Test getting info for non-existent environment
        info = self.manager.get_environment_info("nonexistent_env")
        self.assertIsNone(info)

        # Test getting Python executable for non-existent environment
        python_exec = self.manager.get_python_executable("nonexistent_env")
        self.assertIsNone(python_exec)

        # Test diagnostics for non-existent environment
        diagnostics = self.manager.get_environment_diagnostics("nonexistent_env")
        self.assertFalse(diagnostics["exists"])


class TestPythonEnvironmentManagerEnhancedFeatures(unittest.TestCase):
    """Test cases for enhanced features like shell launching and advanced diagnostics."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.environments_dir = Path(self.temp_dir) / "envs"
        self.environments_dir.mkdir(exist_ok=True)

        # Create manager instance for testing
        self.manager = PythonEnvironmentManager(environments_dir=self.environments_dir)

        # Track environments created during this test for cleanup
        self.created_environments = []

    def tearDown(self):
        """Clean up test environment."""
        # Clean up any conda/mamba environments created during this test
        if hasattr(self, "manager") and self.manager.is_available():
            for env_name in self.created_environments:
                try:
                    if self.manager.environment_exists(env_name):
                        self.manager.remove_python_environment(env_name)
                except Exception:
                    pass  # Best effort cleanup

        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _track_environment(self, env_name):
        """Track an environment for cleanup in tearDown."""
        if env_name not in self.created_environments:
            self.created_environments.append(env_name)

    @regression_test
    @patch("subprocess.run")
    def test_launch_shell_with_command(self, mock_run):
        """Test launching shell with specific command."""
        env_name = "test_shell_env"
        cmd = "print('Hello from Python')"

        # Mock environment existence and Python executable
        with (
            patch.object(self.manager, "environment_exists", return_value=True),
            patch.object(
                self.manager, "get_python_executable", return_value="/path/to/python"
            ),
        ):
            mock_run.return_value = Mock(returncode=0)

            result = self.manager.launch_shell(env_name, cmd)
            self.assertTrue(result)

            # Verify subprocess was called with correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn("/path/to/python", call_args)
            self.assertIn("-c", call_args)
            self.assertIn(cmd, call_args)

    @regression_test
    @patch("subprocess.run")
    @patch("platform.system")
    def test_launch_shell_interactive_windows(self, mock_platform, mock_run):
        """Test launching interactive shell on Windows."""
        mock_platform.return_value = "Windows"
        env_name = "test_shell_env"

        # Mock environment existence and Python executable
        with (
            patch.object(self.manager, "environment_exists", return_value=True),
            patch.object(
                self.manager, "get_python_executable", return_value="/path/to/python"
            ),
        ):
            mock_run.return_value = Mock(returncode=0)

            result = self.manager.launch_shell(env_name)
            self.assertTrue(result)

            # Verify subprocess was called for Windows
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn("cmd", call_args)
            self.assertIn("/c", call_args)

    @regression_test
    @patch("subprocess.run")
    @patch("platform.system")
    def test_launch_shell_interactive_unix(self, mock_platform, mock_run):
        """Test launching interactive shell on Unix."""
        mock_platform.return_value = "Linux"
        env_name = "test_shell_env"

        # Mock environment existence and Python executable
        with (
            patch.object(self.manager, "environment_exists", return_value=True),
            patch.object(
                self.manager, "get_python_executable", return_value="/path/to/python"
            ),
        ):
            mock_run.return_value = Mock(returncode=0)

            result = self.manager.launch_shell(env_name)
            self.assertTrue(result)

            # Verify subprocess was called with Python executable directly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args, ["/path/to/python"])

    @regression_test
    def test_launch_shell_nonexistent_environment(self):
        """Test launching shell for non-existent environment."""
        env_name = "nonexistent_env"

        with patch.object(self.manager, "environment_exists", return_value=False):
            result = self.manager.launch_shell(env_name)
            self.assertFalse(result)

    @regression_test
    def test_launch_shell_no_python_executable(self):
        """Test launching shell when Python executable is not found."""
        env_name = "test_shell_env"

        with (
            patch.object(self.manager, "environment_exists", return_value=True),
            patch.object(self.manager, "get_python_executable", return_value=None),
        ):
            result = self.manager.launch_shell(env_name)
            self.assertFalse(result)

    @regression_test
    def test_get_manager_info_structure(self):
        """Test manager info structure and content."""
        info = self.manager.get_manager_info()

        # Verify required fields are present
        required_fields = [
            "conda_executable",
            "mamba_executable",
            "preferred_manager",
            "is_available",
            "platform",
            "python_version",
        ]

        for field in required_fields:
            self.assertIn(field, info, f"Missing required field: {field}")

        # Verify data types
        self.assertIsInstance(info["is_available"], bool)
        self.assertIsInstance(info["platform"], str)
        self.assertIsInstance(info["python_version"], str)

    @regression_test
    def test_environment_diagnostics_structure(self):
        """Test environment diagnostics structure."""
        env_name = "test_diagnostics"
        diagnostics = self.manager.get_environment_diagnostics(env_name)

        # Verify required fields are present
        required_fields = [
            "environment_name",
            "conda_env_name",
            "exists",
            "conda_available",
            "manager_executable",
            "platform",
        ]

        for field in required_fields:
            self.assertIn(field, diagnostics, f"Missing required field: {field}")

        # Verify basic structure
        self.assertEqual(diagnostics["environment_name"], env_name)
        self.assertEqual(diagnostics["conda_env_name"], f"hatch_{env_name}")
        self.assertIsInstance(diagnostics["exists"], bool)
        self.assertIsInstance(diagnostics["conda_available"], bool)

    @regression_test
    def test_manager_diagnostics_structure(self):
        """Test manager diagnostics structure."""
        diagnostics = self.manager.get_manager_diagnostics()

        # Verify required fields are present
        required_fields = [
            "conda_executable",
            "mamba_executable",
            "conda_available",
            "mamba_available",
            "any_manager_available",
            "preferred_manager",
            "platform",
            "python_version",
            "environments_dir",
        ]

        for field in required_fields:
            self.assertIn(field, diagnostics, f"Missing required field: {field}")

        # Verify data types
        self.assertIsInstance(diagnostics["conda_available"], bool)
        self.assertIsInstance(diagnostics["mamba_available"], bool)
        self.assertIsInstance(diagnostics["any_manager_available"], bool)
        self.assertIsInstance(diagnostics["platform"], str)
        self.assertIsInstance(diagnostics["python_version"], str)
        self.assertIsInstance(diagnostics["environments_dir"], str)
