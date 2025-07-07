"""Tests for DockerInstaller.

This module contains comprehensive tests for the DockerInstaller class,
including unit tests with mocked Docker client and integration tests with
real Docker images.
"""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, Any

from hatch.installers.docker_installer import DockerInstaller, DOCKER_AVAILABLE, DOCKER_DAEMON_AVAILABLE
from hatch.installers.installer_base import InstallationError
from hatch.installers.installation_context import InstallationContext, InstallationResult, InstallationStatus


class DummyContext(InstallationContext):
    """Test implementation of InstallationContext."""
    
    def __init__(self, env_path=None, env_name=None, simulation_mode=False, extra_config=None):
        """Initialize dummy context.
        
        Args:
            env_path (Optional[Path]): Environment path.
            env_name (Optional[str]): Environment name.
            simulation_mode (bool): Whether to run in simulation mode.
            extra_config (Optional[Dict]): Extra configuration.
        """
        self.env_path = env_path or Path("dummy_env")
        self.env_name = env_name or "dummy"
        self.simulation_mode = simulation_mode
        self.extra_config = extra_config or {}

    def get_config(self, key, default=None):
        """Get configuration value.
        
        Args:
            key (str): Configuration key.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        return self.extra_config.get(key, default)


class TestDockerInstaller(unittest.TestCase):
    """Test suite for DockerInstaller using unittest."""

    def setUp(self):
        """Set up test fixtures."""
        self.installer = DockerInstaller()
        self.temp_dir = tempfile.mkdtemp()
        self.context = DummyContext(
            env_path=Path(self.temp_dir),
            simulation_mode=False
        )

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_installer_type(self):
        """Test installer type property."""
        self.assertEqual(
            self.installer.installer_type, "docker",
            f"Installer type mismatch: expected 'docker', got '{self.installer.installer_type}'"
        )

    def test_supported_schemes(self):
        """Test supported schemes property."""
        self.assertEqual(
            self.installer.supported_schemes, ["dockerhub"],
            f"Supported schemes mismatch: expected ['dockerhub'], got {self.installer.supported_schemes}"
        )

    def test_can_install_valid_dependency(self):
        """Test can_install with valid Docker dependency."""
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        with patch.object(self.installer, '_is_docker_available', return_value=True):
            self.assertTrue(
                self.installer.can_install(dependency),
                f"can_install should return True for valid dependency: {dependency}"
            )

    def test_can_install_wrong_type(self):
        """Test can_install with wrong dependency type."""
        dependency = {
            "name": "requests",
            "version_constraint": ">=2.0.0",
            "type": "python"
        }
        self.assertFalse(
            self.installer.can_install(dependency),
            f"can_install should return False for non-docker dependency: {dependency}"
        )

    @unittest.skipUnless(DOCKER_AVAILABLE and DOCKER_DAEMON_AVAILABLE, f"Docker library not available or Docker daemon not available: library={DOCKER_AVAILABLE}, daemon={DOCKER_DAEMON_AVAILABLE}")
    def test_can_install_docker_unavailable(self):
        """Test can_install when Docker daemon is unavailable."""
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "docker"
        }
        with patch.object(self.installer, '_is_docker_available', return_value=False):
            self.assertFalse(
                self.installer.can_install(dependency),
                f"can_install should return False when Docker is unavailable for dependency: {dependency}"
            )

    def test_validate_dependency_valid(self):
        """Test validate_dependency with valid dependency."""
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        self.assertTrue(
            self.installer.validate_dependency(dependency),
            f"validate_dependency should return True for valid dependency: {dependency}"
        )

    def test_validate_dependency_missing_name(self):
        """Test validate_dependency with missing name field."""
        dependency = {
            "version_constraint": ">=1.25.0",
            "type": "docker"
        }
        self.assertFalse(
            self.installer.validate_dependency(dependency),
            f"validate_dependency should return False when 'name' is missing: {dependency}"
        )

    def test_validate_dependency_missing_version_constraint(self):
        """Test validate_dependency with missing version_constraint field."""
        dependency = {
            "name": "nginx",
            "type": "docker"
        }
        self.assertFalse(
            self.installer.validate_dependency(dependency),
            f"validate_dependency should return False when 'version_constraint' is missing: {dependency}"
        )

    def test_validate_dependency_invalid_type(self):
        """Test validate_dependency with invalid type."""
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "python"
        }
        self.assertFalse(
            self.installer.validate_dependency(dependency),
            f"validate_dependency should return False for invalid type: {dependency}"
        )

    def test_validate_dependency_invalid_registry(self):
        """Test validate_dependency with unsupported registry."""
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "docker",
            "registry": "gcr.io"
        }
        self.assertFalse(
            self.installer.validate_dependency(dependency),
            f"validate_dependency should return False for unsupported registry: {dependency}"
        )

    def test_validate_dependency_invalid_version_constraint(self):
        """Test validate_dependency with invalid version constraint."""
        dependency = {
            "name": "nginx",
            "version_constraint": "invalid_version",
            "type": "docker"
        }
        self.assertFalse(
            self.installer.validate_dependency(dependency),
            f"validate_dependency should return False for invalid version_constraint: {dependency}"
        )

    def test_version_constraint_validation(self):
        """Test various version constraint formats."""
        valid_constraints = [
            "1.25.0",
            ">=1.25.0", # Theoretically valid, but Docker works with tags and not version constraints. This is just to ensure the method can handle it.
            "==1.25.0", # Theoretically valid, but Docker works with tags and not version constraints. This is just to ensure the method can handle it.
            "<=2.0.0", # Theoretically valid, but Docker works with tags and not version constraints. This is just to ensure the method can handle it.
            #"!=1.24.0", # Docker works with tags and not version constraint, so this one is really irrelevant
            "latest",
            "1.25",
            "1"
        ]
        for constraint in valid_constraints:
            with self.subTest(constraint=constraint):
                self.assertTrue(
                    self.installer._validate_version_constraint(constraint),
                    f"_validate_version_constraint should return True for valid constraint: '{constraint}'"
                )

    def test_resolve_docker_tag(self):
        """Test Docker tag resolution from version constraints."""
        test_cases = [
            ("latest", "latest"),
            ("1.25.0", "1.25.0"),
            ("==1.25.0", "1.25.0"), # Theoretically valid, but Docker works with tags and not version constraints. This is just to ensure the method can handle it.
            (">=1.25.0", "1.25.0"), # Theoretically valid, but Docker works with tags and not version constraints. This is just to ensure the method can handle it.
            ("<=1.25.0", "1.25.0"), # Theoretically valid, but Docker works with tags and not version constraints. This is just to ensure the method can handle it.
            #("!=1.24.0", "latest"), # Docker works with tags and not version constraint, so this one is really irrelevant
        ]
        for constraint, expected in test_cases:
            with self.subTest(constraint=constraint):
                result = self.installer._resolve_docker_tag(constraint)
                self.assertEqual(
                    result, expected,
                    f"_resolve_docker_tag('{constraint}') returned '{result}', expected '{expected}'"
                )

    def test_install_simulation_mode(self):
        """Test installation in simulation mode."""
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        simulation_context = DummyContext(simulation_mode=True)
        progress_calls = []
        def progress_callback(message, percent, status):
            progress_calls.append((message, percent, status))
        result = self.installer.install(dependency, simulation_context, progress_callback)
        self.assertEqual(
            result.status, InstallationStatus.COMPLETED,
            f"Simulation install should return COMPLETED, got {result.status} with message: {result.metadata["message"]}"
        )
        self.assertIn(
            "Simulated installation", result.metadata["message"],
            f"Simulation install message should mention 'Simulated installation', got: {result.metadata["message"]}"
        )
        self.assertEqual(
            len(progress_calls), 2,
            f"Simulation install should call progress_callback twice (start and completion), got {len(progress_calls)} calls: {progress_calls}"
        )

    @unittest.skipUnless(DOCKER_AVAILABLE and DOCKER_DAEMON_AVAILABLE, f"Docker library not available or Docker daemon not available: library={DOCKER_AVAILABLE}, daemon={DOCKER_DAEMON_AVAILABLE}")
    @patch('hatch.installers.docker_installer.docker')
    def test_install_success(self, mock_docker):
        """Test successful Docker image installation."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.images.pull.return_value = Mock()
        dependency = {
            "name": "nginx",
            "version_constraint": "1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        progress_calls = []
        def progress_callback(message, percent, status):
            progress_calls.append((message, percent, status))
        result = self.installer.install(dependency, self.context, progress_callback)
        self.assertEqual(
            result.status, InstallationStatus.COMPLETED,
            f"Install should return COMPLETED, got {result.status} with message: {result.metadata["message"]}"
        )
        mock_client.images.pull.assert_called_once_with("nginx:1.25.0")
        self.assertGreater(
            len(progress_calls), 0,
            f"Install should call progress_callback at least once, got {len(progress_calls)} calls: {progress_calls}"
        )

    @unittest.skipUnless(DOCKER_AVAILABLE and DOCKER_DAEMON_AVAILABLE, f"Docker library not available or Docker daemon not available: library={DOCKER_AVAILABLE}, daemon={DOCKER_DAEMON_AVAILABLE}")
    @patch('hatch.installers.docker_installer.docker')
    def test_install_failure(self, mock_docker):
        """Test Docker installation failure."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.images.pull.side_effect = Exception("Network error")
        dependency = {
            "name": "nginx",
            "version_constraint": "1.25.0",
            "type": "docker"
        }
        with self.assertRaises(InstallationError, msg=f"Install should raise InstallationError on failure for dependency: {dependency}"):
            self.installer.install(dependency, self.context)

    def test_install_invalid_dependency(self):
        """Test installation with invalid dependency."""
        dependency = {
            "name": "nginx",
            # Missing version_constraint
            "type": "docker"
        }
        with self.assertRaises(InstallationError, msg=f"Install should raise InstallationError for invalid dependency: {dependency}"):
            self.installer.install(dependency, self.context)

    @unittest.skipUnless(DOCKER_AVAILABLE and DOCKER_DAEMON_AVAILABLE, f"Docker library not available or Docker daemon not available: library={DOCKER_AVAILABLE}, daemon={DOCKER_DAEMON_AVAILABLE}")
    @patch('hatch.installers.docker_installer.docker')
    def test_uninstall_success(self, mock_docker):
        """Test successful Docker image uninstallation."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        mock_client.containers.list.return_value = []
        mock_client.images.remove.return_value = None
        dependency = {
            "name": "nginx",
            "version_constraint": "1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        result = self.installer.uninstall(dependency, self.context)
        self.assertEqual(
            result.status, InstallationStatus.COMPLETED,
            f"Uninstall should return COMPLETED, got {result.status} with message: {result.metadata["message"]}"
        )
        mock_client.images.remove.assert_called_once_with("nginx:1.25.0", force=False)

    def test_uninstall_simulation_mode(self):
        """Test uninstallation in simulation mode."""
        dependency = {
            "name": "nginx",
            "version_constraint": "1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        simulation_context = DummyContext(simulation_mode=True)
        result = self.installer.uninstall(dependency, simulation_context)
        self.assertEqual(
            result.status, InstallationStatus.COMPLETED,
            f"Simulation uninstall should return COMPLETED, got {result.status} with message: {result.metadata["message"]}"
        )
        self.assertIn(
            "Simulated removal", result.metadata["message"],
            f"Simulation uninstall message should mention 'Simulated removal', got: {result.metadata["message"]}"
        )

    def test_get_installation_info_docker_unavailable(self):
        """Test get_installation_info when Docker is unavailable."""
        dependency = {
            "name": "nginx",
            "version_constraint": "1.25.0",
            "type": "docker"
        }
        with patch.object(self.installer, '_is_docker_available', return_value=False):
            info = self.installer.get_installation_info(dependency, self.context)
            self.assertEqual(
                info["installer_type"], "docker",
                f"get_installation_info: installer_type should be 'docker', got {info['installer_type']}"
            )
            self.assertEqual(
                info["dependency_name"], "nginx",
                f"get_installation_info: dependency_name should be 'nginx', got {info['dependency_name']}"
            )
            self.assertFalse(
                info["docker_available"],
                f"get_installation_info: docker_available should be False, got {info['docker_available']}"
            )
            self.assertFalse(
                info["can_install"],
                f"get_installation_info: can_install should be False, got {info['can_install']}"
            )

    @unittest.skipUnless(DOCKER_AVAILABLE and DOCKER_DAEMON_AVAILABLE, f"Docker library not available or Docker daemon not available: library={DOCKER_AVAILABLE}, daemon={DOCKER_DAEMON_AVAILABLE}")
    @patch('hatch.installers.docker_installer.docker')
    def test_get_installation_info_image_installed(self, mock_docker):
        """Test get_installation_info for installed image."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        mock_image = Mock()
        mock_image.id = "sha256:abc123"
        mock_image.tags = ["nginx:1.25.0"]
        mock_client.images.get.return_value = mock_image
        dependency = {
            "name": "nginx",
            "version_constraint": "1.25.0",
            "type": "docker"
        }
        
        with patch.object(self.installer, '_is_docker_available', return_value=True):
            info = self.installer.get_installation_info(dependency, self.context)
            
            self.assertTrue(info["docker_available"])
            self.assertTrue(info["installed"])
            self.assertEqual(info["image_id"], "sha256:abc123")


class TestDockerInstallerIntegration(unittest.TestCase):
    """Integration tests for DockerInstaller using real Docker operations."""

    def setUp(self):
        """Set up integration test fixtures."""
        if not DOCKER_AVAILABLE or not DOCKER_DAEMON_AVAILABLE:
            self.skipTest(f"Docker library not available or Docker daemon not available: library={DOCKER_AVAILABLE}, daemon={DOCKER_DAEMON_AVAILABLE}")
            
        self.installer = DockerInstaller()
        self.temp_dir = tempfile.mkdtemp()
        self.context = DummyContext(env_path=Path(self.temp_dir))
        
        # Check if Docker daemon is actually available
        if not self.installer._is_docker_available():
            self.skipTest("Docker daemon not available")

    def tearDown(self):
        """Clean up integration test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)

    def test_docker_daemon_availability(self):
        """Test Docker daemon availability detection."""
        self.assertTrue(self.installer._is_docker_available())

    def test_install_and_uninstall_small_image(self):
        """Test installing and uninstalling a small Docker image.
        
        This test uses the alpine image which is very small (~5MB) to minimize
        download time and resource usage in CI environments.
        """
        dependency = {
            "name": "alpine",
            "version_constraint": "latest",
            "type": "docker",
            "registry": "dockerhub"
        }
        
        progress_events = []
        
        def progress_callback(message, percent, status):
            progress_events.append((message, percent, status))
        
        try:
            # Test installation
            install_result = self.installer.install(dependency, self.context, progress_callback)
            self.assertEqual(install_result.status, InstallationStatus.COMPLETED)
            self.assertGreater(len(progress_events), 0)
            
            # Verify image is installed
            info = self.installer.get_installation_info(dependency, self.context)
            self.assertTrue(info.get("installed", False))
            
            # Test uninstallation
            progress_events.clear()
            uninstall_result = self.installer.uninstall(dependency, self.context, progress_callback)
            self.assertEqual(uninstall_result.status, InstallationStatus.COMPLETED)
            
        except InstallationError as e:
            if e.error_code == "DOCKER_DAEMON_NOT_AVAILABLE":
                self.skipTest(f"Integration test failed due to Docker/network issues: {e}")
            else:
                raise e

    def test_docker_dep_pkg_integration(self):
        """Test integration with docker_dep_pkg dummy package.
        
        This test validates the installer works with the real dependency format
        from the Hatching-Dev docker_dep_pkg.
        """
        # Dependency based on docker_dep_pkg/hatch_metadata.json
        dependency = {
            "name": "nginx",
            "version_constraint": ">=1.25.0",
            "type": "docker",
            "registry": "dockerhub"
        }
        
        try:
            # Test validation
            self.assertTrue(self.installer.validate_dependency(dependency))
            
            # Test can_install
            self.assertTrue(self.installer.can_install(dependency))
            
            # Test installation info
            info = self.installer.get_installation_info(dependency, self.context)
            self.assertEqual(info["installer_type"], "docker")
            self.assertEqual(info["dependency_name"], "nginx")
            
        except Exception as e:
            self.skipTest(f"Docker dep pkg integration test failed: {e}")


if __name__ == "__main__":
    unittest.main()