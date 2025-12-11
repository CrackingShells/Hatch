"""Integration tests for non-TTY handling across the full workflow.

This module tests the complete integration of non-TTY handling from CLI
through to the dependency installation orchestrator, ensuring the full
workflow operates correctly in both TTY and non-TTY environments.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from hatch.environment_manager import HatchEnvironmentManager
from wobble.decorators import integration_test, slow_test
from test_data_utils import NonTTYTestDataLoader, TestDataLoader


class TestNonTTYIntegration(unittest.TestCase):
    """Integration tests for non-TTY handling across the full workflow."""
    
    def setUp(self):
        """Set up integration test environment with centralized test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_manager = HatchEnvironmentManager(
            environments_dir=Path(self.temp_dir) / "envs",
            simulation_mode=True
        )
        self.test_data = NonTTYTestDataLoader()
        self.addCleanup(self._cleanup_temp_dir)
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @integration_test(scope="component")
    @slow_test
    @patch('sys.stdin.isatty', return_value=False)
    def test_cli_package_add_non_tty(self, mock_isatty):
        """Test package addition in non-TTY environment via CLI."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        # Test package addition without hanging
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        # Ensure the test package exists
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=False  # Test environment variable handling
        )
        
        self.assertTrue(result, "Package addition should succeed in non-TTY mode")
        mock_isatty.assert_called()
    
    @integration_test(scope="component")
    @slow_test
    @patch.dict(os.environ, {'HATCH_AUTO_APPROVE': '1'})
    def test_environment_variable_integration(self):
        """Test HATCH_AUTO_APPROVE environment variable integration."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        # Test with centralized test data
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        # Ensure the test package exists
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=False  # Environment variable should override
        )
        
        self.assertTrue(result, "Package addition should succeed with HATCH_AUTO_APPROVE")
    
    @integration_test(scope="component")
    @slow_test
    @patch('sys.stdin.isatty', return_value=False)
    def test_multiple_package_installation_non_tty(self, mock_isatty):
        """Test multiple package installation in non-TTY environment."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        test_loader = TestDataLoader()
        
        # Install first package
        base_pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        if base_pkg_path.exists():
            result1 = self.env_manager.add_package_to_environment(
                str(base_pkg_path),
                "test_env",
                auto_approve=False
            )
            self.assertTrue(result1, "First package installation should succeed")
        
        # Install second package
        utility_pkg_path = test_loader.packages_dir / "basic" / "utility_pkg"
        if utility_pkg_path.exists():
            result2 = self.env_manager.add_package_to_environment(
                str(utility_pkg_path),
                "test_env",
                auto_approve=False
            )
            self.assertTrue(result2, "Second package installation should succeed")
    
    @integration_test(scope="component")
    @slow_test
    @patch.dict(os.environ, {'HATCH_AUTO_APPROVE': 'true'})
    def test_environment_variable_case_insensitive_integration(self):
        """Test case-insensitive environment variable in full integration."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=False
        )
        
        self.assertTrue(result, "Package addition should succeed with case-insensitive env var")
    
    @integration_test(scope="component")
    @slow_test
    @patch('sys.stdin.isatty', return_value=True)
    @patch.dict(os.environ, {'HATCH_AUTO_APPROVE': 'invalid'})
    @patch('builtins.input', return_value='y')
    def test_invalid_environment_variable_fallback_integration(self, mock_input, mock_isatty):
        """Test fallback to interactive mode with invalid environment variable."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=False
        )
        
        self.assertTrue(result, "Package addition should succeed with user approval")
        # Verify that input was called (fallback to interactive mode)
        mock_input.assert_called()


class TestNonTTYErrorScenarios(unittest.TestCase):
    """Test error scenarios in non-TTY environments."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_manager = HatchEnvironmentManager(
            environments_dir=Path(self.temp_dir) / "envs",
            simulation_mode=True
        )
        self.test_data = NonTTYTestDataLoader()
        self.addCleanup(self._cleanup_temp_dir)
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @integration_test(scope="component")
    @slow_test
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_keyboard_interrupt_integration(self, mock_input, mock_isatty):
        """Test KeyboardInterrupt handling in full integration."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=False
        )
        
        # Should return False due to user cancellation
        self.assertFalse(result, "Package installation should be cancelled by user")
    
    @integration_test(scope="component")
    @slow_test
    @patch('sys.stdin.isatty', return_value=True)
    @patch('builtins.input', side_effect=EOFError())
    def test_eof_error_integration(self, mock_input, mock_isatty):
        """Test EOFError handling in full integration."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=False
        )
        
        # Should return False due to EOF error
        self.assertFalse(result, "Package installation should be cancelled due to EOF")


class TestEnvironmentVariableIntegrationScenarios(unittest.TestCase):
    """Test comprehensive environment variable scenarios in full integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_manager = HatchEnvironmentManager(
            environments_dir=Path(self.temp_dir) / "envs",
            simulation_mode=True
        )
        self.test_data = NonTTYTestDataLoader()
        self.addCleanup(self._cleanup_temp_dir)
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @integration_test(scope="component")
    @slow_test
    def test_all_valid_environment_variables_integration(self):
        """Test all valid environment variable values in integration."""
        # Create test environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        test_loader = TestDataLoader()
        pkg_path = test_loader.packages_dir / "basic" / "base_pkg"
        
        if not pkg_path.exists():
            self.skipTest(f"Test package not found: {pkg_path}")
        
        # Test all valid environment variable values
        valid_values = ["1", "true", "yes", "TRUE", "YES", "True"]
        
        for i, value in enumerate(valid_values):
            with self.subTest(env_value=value):
                env_name = f"test_env_{i}"
                self.env_manager.create_environment(env_name, f"Test environment {i}")
                
                with patch.dict(os.environ, {'HATCH_AUTO_APPROVE': value}):
                    result = self.env_manager.add_package_to_environment(
                        str(pkg_path),
                        env_name,
                        auto_approve=False
                    )
                    
                    self.assertTrue(result, f"Package installation should succeed with env var: {value}")


if __name__ == '__main__':
    unittest.main()
