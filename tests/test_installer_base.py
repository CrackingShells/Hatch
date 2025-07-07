import sys
import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
from typing import Dict, Any, List

# Add parent directory to path for direct testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.installers.installer_base import (
    DependencyInstaller,
    InstallationError
)

from hatch.installers.installation_context import (
    InstallationContext, 
    InstallationResult,
    InstallationStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hatch.installer_interface_tests")


class MockInstaller(DependencyInstaller):
    """Mock installer for testing the base interface."""
    
    @property
    def installer_type(self) -> str:
        return "mock"
    
    @property
    def supported_schemes(self) -> List[str]:
        return ["test", "mock"]
    
    def can_install(self, dependency: Dict[str, Any]) -> bool:
        return dependency.get("type") == "mock"
    
    def install(self, dependency: Dict[str, Any], context: InstallationContext,
                progress_callback=None) -> InstallationResult:
        return InstallationResult(
            dependency_name=dependency["name"],
            status=InstallationStatus.COMPLETED,
            installed_path=context.environment_path / dependency["name"],
            installed_version=dependency["resolved_version"]
        )


class BaseInstallerTests(unittest.TestCase):
    """Tests for the DependencyInstaller base class interface."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test environments
        self.temp_dir = tempfile.mkdtemp()
        self.env_path = Path(self.temp_dir) / "test_env"
        self.env_path.mkdir(parents=True, exist_ok=True)
        
        # Create a mock installer instance for testing
        self.installer = MockInstaller()
        
        # Create test context
        self.context = InstallationContext(
            environment_path=self.env_path,
            environment_name="test_env"
        )
        
        logger.info(f"Set up test environment at {self.temp_dir}")
    
    def tearDown(self):
        """Clean up test environment after each test."""
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up test environment at {self.temp_dir}")
    
    def test_installation_context_creation(self):
        """Test that InstallationContext can be created with required fields."""
        context = InstallationContext(
            environment_path=Path("/test/env"),
            environment_name="test_env"
        )
        self.assertEqual(context.environment_path, Path("/test/env"), f"Expected environment_path=/test/env, got {context.environment_path}")
        self.assertEqual(context.environment_name, "test_env", f"Expected environment_name='test_env', got {context.environment_name}")
        self.assertTrue(context.parallel_enabled, f"Expected parallel_enabled=True, got {context.parallel_enabled}")  # Default value
        self.assertEqual(context.get_config("nonexistent", "default"), "default", f"Expected default config fallback, got {context.get_config('nonexistent', 'default')}")
        logger.info("InstallationContext creation test passed")
    
    def test_installation_context_with_config(self):
        """Test InstallationContext with extra configuration."""
        context = InstallationContext(
            environment_path=Path("/test/env"),
            environment_name="test_env",
            extra_config={"custom_setting": "value"}
        )
        self.assertEqual(context.get_config("custom_setting"), "value", f"Expected custom_setting='value', got {context.get_config('custom_setting')}")
        self.assertEqual(context.get_config("missing_key", "fallback"), "fallback", f"Expected fallback for missing_key, got {context.get_config('missing_key', 'fallback')}")
        logger.info("InstallationContext with config test passed")
    
    def test_installation_result_creation(self):
        """Test that InstallationResult can be created."""
        result = InstallationResult(
            dependency_name="test_package",
            status=InstallationStatus.COMPLETED,
            installed_path=Path("/env/test_package"),
            installed_version="1.0.0"
        )
        self.assertEqual(result.dependency_name, "test_package", f"Expected dependency_name='test_package', got {result.dependency_name}")
        self.assertEqual(result.status, InstallationStatus.COMPLETED, f"Expected status=COMPLETED, got {result.status}")
        self.assertEqual(result.installed_path, Path("/env/test_package"), f"Expected installed_path=/env/test_package, got {result.installed_path}")
        self.assertEqual(result.installed_version, "1.0.0", f"Expected installed_version='1.0.0', got {result.installed_version}")
        logger.info("InstallationResult creation test passed")
    
    def test_installation_error(self):
        """Test InstallationError creation and attributes."""
        error = InstallationError(
            message="Installation failed",
            dependency_name="test_package",
            error_code="DOWNLOAD_FAILED"
        )
        self.assertEqual(error.message, "Installation failed", f"Expected error message 'Installation failed', got '{error.message}'")
        self.assertEqual(error.dependency_name, "test_package", f"Expected dependency_name='test_package', got {error.dependency_name}")
        self.assertEqual(error.error_code, "DOWNLOAD_FAILED", f"Expected error_code='DOWNLOAD_FAILED', got {error.error_code}")
        logger.info("InstallationError test passed")
    
    def test_mock_installer_interface(self):
        """Test that MockInstaller implements the interface correctly."""
        # Test properties
        self.assertEqual(self.installer.installer_type, "mock", f"Expected installer_type='mock', got {self.installer.installer_type}")
        self.assertEqual(self.installer.supported_schemes, ["test", "mock"], f"Expected supported_schemes=['test', 'mock'], got {self.installer.supported_schemes}")
        # Test can_install
        mock_dep = {"type": "mock", "name": "test"}
        non_mock_dep = {"type": "other", "name": "test"}
        self.assertTrue(self.installer.can_install(mock_dep), f"Expected can_install to be True for {mock_dep}")
        self.assertFalse(self.installer.can_install(non_mock_dep), f"Expected can_install to be False for {non_mock_dep}")
        logger.info("MockInstaller interface test passed")
    
    def test_mock_installer_install(self):
        """Test the install method of MockInstaller."""
        dependency = {
            "name": "test_package",
            "type": "mock",
            "version_constraint": ">=1.0.0",
            "resolved_version": "1.2.0"
        }
        result = self.installer.install(dependency, self.context)
        self.assertEqual(result.dependency_name, "test_package", f"Expected dependency_name='test_package', got {result.dependency_name}")
        self.assertEqual(result.status, InstallationStatus.COMPLETED, f"Expected status=COMPLETED, got {result.status}")
        self.assertEqual(result.installed_path, self.env_path / "test_package", f"Expected installed_path={self.env_path / 'test_package'}, got {result.installed_path}")
        self.assertEqual(result.installed_version, "1.2.0", f"Expected installed_version='1.2.0', got {result.installed_version}")
        logger.info("MockInstaller install test passed")
    
    def test_mock_installer_validation(self):
        """Test dependency validation."""
        valid_dep = {
            "name": "test",
            "version_constraint": ">=1.0.0",
            "resolved_version": "1.0.0"
        }
        invalid_dep = {
            "name": "test"
            # Missing required fields
        }
        self.assertTrue(self.installer.validate_dependency(valid_dep), f"Expected valid dependency to pass validation: {valid_dep}")
        self.assertFalse(self.installer.validate_dependency(invalid_dep), f"Expected invalid dependency to fail validation: {invalid_dep}")
        logger.info("MockInstaller validation test passed")
    
    def test_mock_installer_get_installation_info(self):
        """Test getting installation information."""
        dependency = {
            "name": "test_package",
            "type": "mock",
            "resolved_version": "1.0.0"
        }
        info = self.installer.get_installation_info(dependency, self.context)
        self.assertEqual(info["installer_type"], "mock", f"Expected installer_type='mock', got {info['installer_type']}")
        self.assertEqual(info["dependency_name"], "test_package", f"Expected dependency_name='test_package', got {info['dependency_name']}")
        self.assertEqual(info["resolved_version"], "1.0.0", f"Expected resolved_version='1.0.0', got {info['resolved_version']}")
        self.assertEqual(info["target_path"], str(self.env_path), f"Expected target_path={self.env_path}, got {info['target_path']}")
        self.assertTrue(info["supported"], f"Expected supported=True, got {info['supported']}")
        logger.info("MockInstaller get_installation_info test passed")
    
    def test_mock_installer_uninstall_not_implemented(self):
        """Test that uninstall raises NotImplementedError by default."""
        dependency = {"name": "test", "type": "mock"}
        with self.assertRaises(NotImplementedError, msg="Expected NotImplementedError for uninstall on MockInstaller"):
            self.installer.uninstall(dependency, self.context)
        logger.info("MockInstaller uninstall NotImplementedError test passed")
    
    def test_installation_status_enum(self):
        """Test InstallationStatus enum values."""
        self.assertEqual(InstallationStatus.PENDING.value, "pending", f"Expected PENDING='pending', got {InstallationStatus.PENDING.value}")
        self.assertEqual(InstallationStatus.IN_PROGRESS.value, "in_progress", f"Expected IN_PROGRESS='in_progress', got {InstallationStatus.IN_PROGRESS.value}")
        self.assertEqual(InstallationStatus.COMPLETED.value, "completed", f"Expected COMPLETED='completed', got {InstallationStatus.COMPLETED.value}")
        self.assertEqual(InstallationStatus.FAILED.value, "failed", f"Expected FAILED='failed', got {InstallationStatus.FAILED.value}")
        self.assertEqual(InstallationStatus.ROLLED_BACK.value, "rolled_back", f"Expected ROLLED_BACK='rolled_back', got {InstallationStatus.ROLLED_BACK.value}")
        logger.info("InstallationStatus enum test passed")
    
    def test_progress_callback_support(self):
        """Test that installer accepts progress callback."""
        dependency = {
            "name": "test_package",
            "type": "mock",
            "resolved_version": "1.0.0"
        }
        callback_called = []
        def progress_callback(progress: float, message: str = ""):
            callback_called.append((progress, message))
        # Install with callback - should not raise error
        result = self.installer.install(dependency, self.context, progress_callback)
        self.assertEqual(result.status, InstallationStatus.COMPLETED, f"Expected status=COMPLETED, got {result.status}")
        logger.info("Progress callback support test passed")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
