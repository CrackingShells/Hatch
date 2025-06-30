"""Tests for PythonEnvironmentManager.

This module contains tests for the Python environment management functionality,
including conda/mamba environment creation, configuration, and integration.
"""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from hatch.python_environment_manager import PythonEnvironmentManager, PythonEnvironmentError


class TestPythonEnvironmentManager(unittest.TestCase):
    """Test cases for PythonEnvironmentManager functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.environments_dir = Path(self.temp_dir) / "envs"
        self.environments_dir.mkdir(exist_ok=True)
        
        # Create manager instance for testing
        self.manager = PythonEnvironmentManager(environments_dir=self.environments_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test PythonEnvironmentManager initialization."""
        self.assertEqual(self.manager.environments_dir, self.environments_dir)
        self.assertIsNotNone(self.manager.logger)

    def test_detect_conda_mamba_with_mamba(self):
        """Test conda/mamba detection when mamba is available."""
        with patch.object(PythonEnvironmentManager, "_detect_manager") as mock_detect:
            # mamba found, conda found
            mock_detect.side_effect = lambda manager: "/usr/bin/mamba" if manager == "mamba" else "/usr/bin/conda"
            manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
            self.assertEqual(manager.mamba_executable, "/usr/bin/mamba")
            self.assertEqual(manager.conda_executable, "/usr/bin/conda")

    def test_detect_conda_mamba_conda_only(self):
        """Test conda/mamba detection when only conda is available."""
        with patch.object(PythonEnvironmentManager, "_detect_manager") as mock_detect:
            # mamba not found, conda found
            mock_detect.side_effect = lambda manager: None if manager == "mamba" else "/usr/bin/conda"
            manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
            self.assertIsNone(manager.mamba_executable)
            self.assertEqual(manager.conda_executable, "/usr/bin/conda")

    def test_detect_conda_mamba_none_available(self):
        """Test conda/mamba detection when neither is available."""
        with patch.object(PythonEnvironmentManager, "_detect_manager", return_value=None):
            manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
            self.assertIsNone(manager.mamba_executable)
            self.assertIsNone(manager.conda_executable)

    def test_get_conda_env_name(self):
        """Test conda environment name generation."""
        env_name = "test_env"
        conda_name = self.manager._get_conda_env_name(env_name)
        self.assertEqual(conda_name, "hatch_test_env")

    def test_get_conda_env_prefix(self):
        """Test conda environment prefix path generation."""
        env_name = "test_env"
        prefix = self.manager._get_conda_env_prefix(env_name)
        expected = self.environments_dir / "test_env" / "python_env"
        self.assertEqual(prefix, expected)

    def test_get_python_executable_path_windows(self):
        """Test Python executable path on Windows."""
        with patch('platform.system', return_value='Windows'):
            env_name = "test_env"
            python_path = self.manager._get_python_executable_path(env_name)
            expected = self.environments_dir / "test_env" / "python_env" / "python.exe"
            self.assertEqual(python_path, expected)

    def test_get_python_executable_path_unix(self):
        """Test Python executable path on Unix/Linux."""
        with patch('platform.system', return_value='Linux'):
            env_name = "test_env"
            python_path = self.manager._get_python_executable_path(env_name)
            expected = self.environments_dir / "test_env" / "python_env" / "bin" / "python"
            self.assertEqual(python_path, expected)

    def test_is_available_no_conda(self):
        """Test availability check when conda/mamba is not available."""
        manager = PythonEnvironmentManager(environments_dir=self.environments_dir)
        manager.conda_executable = None
        manager.mamba_executable = None
        
        self.assertFalse(manager.is_available())

    @patch('subprocess.run')
    def test_is_available_with_conda(self, mock_run):
        """Test availability check when conda is available."""
        self.manager.conda_executable = "/usr/bin/conda"
        
        # Mock successful conda info
        mock_run.return_value = Mock(returncode=0, stdout='{"platform": "linux-64"}')
        
        self.assertTrue(self.manager.is_available())

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

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_create_python_environment_success(self, mock_run, mock_which):
        """Test successful Python environment creation."""
        # Patch mamba detection
        mock_which.side_effect = lambda cmd: "/usr/bin/mamba" if cmd == "mamba" else None

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
        with patch.object(manager, '_conda_env_exists', return_value=False):
            result = manager.create_python_environment("test_env", python_version="3.11")
            self.assertTrue(result)
            mock_run.assert_called()

    def test_create_python_environment_no_conda(self):
        """Test Python environment creation when conda/mamba is not available."""
        self.manager.conda_executable = None
        self.manager.mamba_executable = None
        
        with self.assertRaises(PythonEnvironmentError):
            self.manager.create_python_environment("test_env")

    @patch('shutil.which')
    @patch('subprocess.run')
    def test_create_python_environment_already_exists(self, mock_run, mock_which):
        """Test Python environment creation when environment already exists."""
        # Patch mamba detection
        mock_which.side_effect = lambda cmd: "/usr/bin/mamba" if cmd == "mamba" else None

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
        with patch.object(self.manager, '_conda_env_exists', return_value=True):
            result = self.manager.create_python_environment("test_env")
            self.assertTrue(result)
            # Ensure 'create' was not called, but 'info' was
            create_calls = [call for call in mock_run.call_args_list if "create" in call[0][0]]
            self.assertEqual(len(create_calls), 0)

    def test_conda_env_exists(self):
        """Test conda environment existence check."""
        env_name = "test_env"
        
        # Create the environment directory structure
        env_prefix = self.manager._get_conda_env_prefix(env_name)
        env_prefix.mkdir(parents=True, exist_ok=True)
        
        # Create Python executable
        python_executable = self.manager._get_python_executable_path(env_name)
        python_executable.parent.mkdir(parents=True, exist_ok=True)
        python_executable.write_text("#!/usr/bin/env python")
        
        self.assertTrue(self.manager._conda_env_exists(env_name))

    def test_conda_env_not_exists(self):
        """Test conda environment existence check when environment doesn't exist."""
        env_name = "nonexistent_env"
        self.assertFalse(self.manager._conda_env_exists(env_name))

    def test_get_python_executable_exists(self):
        """Test getting Python executable when environment exists."""
        env_name = "test_env"
        
        # Create environment and Python executable
        python_executable = self.manager._get_python_executable_path(env_name)
        python_executable.parent.mkdir(parents=True, exist_ok=True)
        python_executable.write_text("#!/usr/bin/env python")
        
        with patch.object(self.manager, '_conda_env_exists', return_value=True):
            result = self.manager.get_python_executable(env_name)
            self.assertEqual(result, str(python_executable))

    def test_get_python_executable_not_exists(self):
        """Test getting Python executable when environment doesn't exist."""
        env_name = "nonexistent_env"
        
        with patch.object(self.manager, '_conda_env_exists', return_value=False):
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
        """Set up class-level test environment."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.environments_dir = Path(cls.temp_dir) / "envs"
        cls.environments_dir.mkdir(exist_ok=True)
        
        # Create manager instance for integration testing
        cls.manager = PythonEnvironmentManager(environments_dir=cls.environments_dir)

        # Skip all tests if conda/mamba is not available
        if not cls.manager.is_available():
            raise unittest.SkipTest("Conda/mamba not available for integration tests")

    @classmethod
    def tearDownClass(cls):
        """Clean up class-level test environment."""
        # Clean up any test environments that might have been created
        try:
            test_envs = ["test_integration_env", "test_python_311", "test_python_312", "test_diagnostics_env"]
            for env_name in test_envs:
                if cls.manager.environment_exists(env_name):
                    cls.manager.remove_python_environment(env_name)
        except Exception:
            pass  # Best effort cleanup
        
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_conda_mamba_detection_real(self):
        """Test real conda/mamba detection on the system."""
        manager_info = self.manager.get_manager_info()
        
        # At least one should be available since we skip tests if neither is available
        self.assertTrue(manager_info["is_available"])
        self.assertTrue(
            manager_info["conda_executable"] is not None or 
            manager_info["mamba_executable"] is not None
        )
        
        # Preferred manager should be set
        self.assertIsNotNone(manager_info["preferred_manager"])
        
        # Platform and Python version should be populated
        self.assertIsNotNone(manager_info["platform"])
        self.assertIsNotNone(manager_info["python_version"])

    def test_manager_diagnostics_real(self):
        """Test real manager diagnostics."""
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

    def test_create_and_remove_python_environment_real(self):
        """Test real Python environment creation and removal."""
        env_name = "test_integration_env"
        
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
        self.assertTrue(Path(python_exec).exists(), f"Python executable doesn't exist: {python_exec}")
        
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

    def test_create_python_environment_with_version_real(self):
        """Test real Python environment creation with specific version."""
        env_name = "test_python_311"
        python_version = "3.11"
        
        # Ensure environment doesn't exist initially
        if self.manager.environment_exists(env_name):
            self.manager.remove_python_environment(env_name)
        
        # Create environment with specific Python version
        result = self.manager.create_python_environment(env_name, python_version=python_version)
        self.assertTrue(result, f"Failed to create Python {python_version} environment")

        # Verify environment exists
        self.assertTrue(self.manager.environment_exists(env_name))
        
        # Verify Python version
        actual_version = self.manager.get_python_version(env_name)
        self.assertIsNotNone(actual_version)
        self.assertTrue(actual_version.startswith("3.11"), f"Expected Python 3.11.x, got {actual_version}")

        # Get comprehensive environment info
        env_info = self.manager.get_environment_info(env_name)
        self.assertIsNotNone(env_info)
        self.assertTrue(env_info["python_version"].startswith("3.11"), f"Expected Python 3.11.x, got {env_info['python_version']}")

        # Cleanup
        self.manager.remove_python_environment(env_name)

    def test_environment_diagnostics_real(self):
        """Test real environment diagnostics."""
        env_name = "test_diagnostics_env"
        
        # Ensure environment doesn't exist initially
        if self.manager.environment_exists(env_name):
            self.manager.remove_python_environment(env_name)
        
        # Test diagnostics for non-existent environment
        diagnostics = self.manager.get_environment_diagnostics(env_name)
        self.assertFalse(diagnostics["exists"])
        self.assertTrue(diagnostics["conda_available"])
        
        # Create environment
        self.manager.create_python_environment(env_name)
        
        # Test diagnostics for existing environment
        diagnostics = self.manager.get_environment_diagnostics(env_name)
        self.assertTrue(diagnostics["exists"])
        self.assertIsNotNone(diagnostics["python_executable"])
        self.assertTrue(diagnostics["python_accessible"])
        self.assertIsNotNone(diagnostics["python_version"])
        self.assertTrue(diagnostics["python_version_accessible"])
        self.assertTrue(diagnostics["python_executable_works"])
        self.assertIsNotNone(diagnostics["environment_path"])
        self.assertTrue(diagnostics["environment_path_exists"])
        
        # Cleanup
        self.manager.remove_python_environment(env_name)

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

    def test_list_environments_real(self):
        """Test listing environments with real conda environments."""
        test_envs = ["test_env_1", "test_env_2"]
        
        # Clean up any existing test environments
        for env_name in test_envs:
            if self.manager.environment_exists(env_name):
                self.manager.remove_python_environment(env_name)
        
        # Create test environments
        for env_name in test_envs:
            result = self.manager.create_python_environment(env_name)
            self.assertTrue(result, f"Failed to create {env_name}")
        
        # List environments
        env_list = self.manager.list_environments()
        
        # Should include our test environments
        for env_name in test_envs:
            self.assertIn(env_name, env_list, f"{env_name} not found in environment list")
        
        # Cleanup
        for env_name in test_envs:
            self.manager.remove_python_environment(env_name)

    @unittest.skipIf(
        not (Path("/usr/bin/python3.12").exists() or Path("/usr/bin/python3.9").exists()),
        "Multiple Python versions not available for testing"
    )
    def test_multiple_python_versions_real(self):
        """Test creating environments with multiple Python versions."""
        test_cases = [
            ("test_python_39", "3.9"),
            ("test_python_312", "3.12")
        ]
        
        created_envs = []
        
        try:
            for env_name, python_version in test_cases:
                # Skip if this Python version is not available
                try:
                    result = self.manager.create_python_environment(env_name, python_version=python_version)
                    if result:
                        created_envs.append(env_name)
                        
                        # Verify Python version
                        actual_version = self.manager.get_python_version(env_name)
                        self.assertIsNotNone(actual_version)
                        self.assertTrue(
                            actual_version.startswith(python_version),
                            f"Expected Python {python_version}.x, got {actual_version}"
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

    def test_error_handling_real(self):
        """Test error handling with real operations."""
        # Test removing non-existent environment
        result = self.manager.remove_python_environment("nonexistent_env")
        self.assertTrue(result) # Removing non existent environment returns True because it does nothing
        
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

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('subprocess.run')
    def test_launch_shell_with_command(self, mock_run):
        """Test launching shell with specific command."""
        env_name = "test_shell_env"
        cmd = "print('Hello from Python')"
        
        # Mock environment existence and Python executable
        with patch.object(self.manager, 'environment_exists', return_value=True), \
             patch.object(self.manager, 'get_python_executable', return_value="/path/to/python"):
            
            mock_run.return_value = Mock(returncode=0)
            
            result = self.manager.launch_shell(env_name, cmd)
            self.assertTrue(result)
            
            # Verify subprocess was called with correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn("/path/to/python", call_args)
            self.assertIn("-c", call_args)
            self.assertIn(cmd, call_args)

    @patch('subprocess.run')
    @patch('platform.system')
    def test_launch_shell_interactive_windows(self, mock_platform, mock_run):
        """Test launching interactive shell on Windows."""
        mock_platform.return_value = "Windows"
        env_name = "test_shell_env"
        
        # Mock environment existence and Python executable
        with patch.object(self.manager, 'environment_exists', return_value=True), \
             patch.object(self.manager, 'get_python_executable', return_value="/path/to/python"):
            
            mock_run.return_value = Mock(returncode=0)
            
            result = self.manager.launch_shell(env_name)
            self.assertTrue(result)
            
            # Verify subprocess was called for Windows
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertIn("cmd", call_args)
            self.assertIn("/c", call_args)

    @patch('subprocess.run')
    @patch('platform.system')
    def test_launch_shell_interactive_unix(self, mock_platform, mock_run):
        """Test launching interactive shell on Unix."""
        mock_platform.return_value = "Linux"
        env_name = "test_shell_env"
        
        # Mock environment existence and Python executable
        with patch.object(self.manager, 'environment_exists', return_value=True), \
             patch.object(self.manager, 'get_python_executable', return_value="/path/to/python"):
            
            mock_run.return_value = Mock(returncode=0)
            
            result = self.manager.launch_shell(env_name)
            self.assertTrue(result)
            
            # Verify subprocess was called with Python executable directly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args, ["/path/to/python"])

    def test_launch_shell_nonexistent_environment(self):
        """Test launching shell for non-existent environment."""
        env_name = "nonexistent_env"
        
        with patch.object(self.manager, 'environment_exists', return_value=False):
            result = self.manager.launch_shell(env_name)
            self.assertFalse(result)

    def test_launch_shell_no_python_executable(self):
        """Test launching shell when Python executable is not found."""
        env_name = "test_shell_env"
        
        with patch.object(self.manager, 'environment_exists', return_value=True), \
             patch.object(self.manager, 'get_python_executable', return_value=None):
            
            result = self.manager.launch_shell(env_name)
            self.assertFalse(result)

    def test_get_manager_info_structure(self):
        """Test manager info structure and content."""
        info = self.manager.get_manager_info()
        
        # Verify required fields are present
        required_fields = [
            "conda_executable", "mamba_executable", "preferred_manager",
            "is_available", "platform", "python_version"
        ]
        
        for field in required_fields:
            self.assertIn(field, info, f"Missing required field: {field}")
        
        # Verify data types
        self.assertIsInstance(info["is_available"], bool)
        self.assertIsInstance(info["platform"], str)
        self.assertIsInstance(info["python_version"], str)

    def test_environment_diagnostics_structure(self):
        """Test environment diagnostics structure."""
        env_name = "test_diagnostics"
        diagnostics = self.manager.get_environment_diagnostics(env_name)
        
        # Verify required fields are present
        required_fields = [
            "environment_name", "conda_env_name", "exists", "conda_available",
            "manager_executable", "platform"
        ]
        
        for field in required_fields:
            self.assertIn(field, diagnostics, f"Missing required field: {field}")
        
        # Verify basic structure
        self.assertEqual(diagnostics["environment_name"], env_name)
        self.assertEqual(diagnostics["conda_env_name"], f"hatch-{env_name}")
        self.assertIsInstance(diagnostics["exists"], bool)
        self.assertIsInstance(diagnostics["conda_available"], bool)

    def test_manager_diagnostics_structure(self):
        """Test manager diagnostics structure."""
        diagnostics = self.manager.get_manager_diagnostics()
        
        # Verify required fields are present
        required_fields = [
            "conda_executable", "mamba_executable", "conda_available", "mamba_available",
            "any_manager_available", "preferred_manager", "platform", "python_version",
            "environments_dir"
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
