"""Unit tests for dependency installation orchestrator consent handling.

This module tests the user consent functionality in the dependency installation
orchestrator, focusing on TTY detection, environment variable support, and
error handling scenarios.
"""

import unittest
import os
from unittest.mock import patch, MagicMock
from hatch.installers.dependency_installation_orchestrator import (
    DependencyInstallerOrchestrator,
)
from hatch.package_loader import HatchPackageLoader
from hatch_validator.registry.registry_service import RegistryService
from wobble.decorators import regression_test
from test_data_utils import NonTTYTestDataLoader


class TestUserConsentHandling(unittest.TestCase):
    """Test user consent handling in dependency installation orchestrator."""

    def setUp(self):
        """Set up test environment with centralized test data."""
        # Create mock dependencies for orchestrator
        self.mock_package_loader = MagicMock(spec=HatchPackageLoader)
        self.mock_registry_data = {
            "registry_schema_version": "1.1.0",
            "repositories": [],
        }
        self.mock_registry_service = MagicMock(spec=RegistryService)

        # Create orchestrator with mocked dependencies
        self.orchestrator = DependencyInstallerOrchestrator(
            package_loader=self.mock_package_loader,
            registry_service=self.mock_registry_service,
            registry_data=self.mock_registry_data,
        )

        self.test_data = NonTTYTestDataLoader()
        self.mock_install_plan = self.test_data.get_installation_plan(
            "basic_python_plan"
        )
        self.logging_messages = self.test_data.get_logging_messages()

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", return_value="y")
    def test_tty_environment_user_approves(self, mock_input, mock_isatty):
        """Test user consent approval in TTY environment."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertTrue(result)
        mock_input.assert_called_once_with("\nProceed with installation? [y/N]: ")
        mock_isatty.assert_called_once()

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", return_value="yes")
    def test_tty_environment_user_approves_full_word(self, mock_input, mock_isatty):
        """Test user consent approval with 'yes' in TTY environment."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertTrue(result)
        mock_input.assert_called_once_with("\nProceed with installation? [y/N]: ")

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", return_value="n")
    def test_tty_environment_user_denies(self, mock_input, mock_isatty):
        """Test user consent denial in TTY environment."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertFalse(result)
        mock_input.assert_called_once_with("\nProceed with installation? [y/N]: ")

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", return_value="no")
    def test_tty_environment_user_denies_full_word(self, mock_input, mock_isatty):
        """Test user consent denial with 'no' in TTY environment."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertFalse(result)
        mock_input.assert_called_once_with("\nProceed with installation? [y/N]: ")

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", return_value="")
    def test_tty_environment_user_default_deny(self, mock_input, mock_isatty):
        """Test user consent default (empty) response in TTY environment."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertFalse(result)
        mock_input.assert_called_once_with("\nProceed with installation? [y/N]: ")

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", side_effect=["invalid", "y"])
    @patch("builtins.print")
    def test_tty_environment_invalid_then_valid_input(
        self, mock_print, mock_input, mock_isatty
    ):
        """Test handling of invalid input followed by valid input."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertTrue(result)
        self.assertEqual(mock_input.call_count, 2)
        mock_print.assert_called_once_with("Please enter 'y' for yes or 'n' for no.")

    @regression_test
    @patch("sys.stdin.isatty", return_value=False)
    def test_non_tty_environment_auto_approve(self, mock_isatty):
        """Test automatic approval in non-TTY environment."""
        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(self.mock_install_plan)

            self.assertTrue(result)
            mock_isatty.assert_called_once()
            mock_log.assert_called_with(self.logging_messages["auto_approve"])

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch.dict(os.environ, {"HATCH_AUTO_APPROVE": "1"})
    def test_environment_variable_numeric_true(self, mock_isatty):
        """Test HATCH_AUTO_APPROVE=1 triggers auto-approval."""
        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(self.mock_install_plan)

            self.assertTrue(result)
            mock_log.assert_called_with(self.logging_messages["auto_approve"])

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch.dict(os.environ, {"HATCH_AUTO_APPROVE": "true"})
    def test_environment_variable_string_true(self, mock_isatty):
        """Test HATCH_AUTO_APPROVE=true triggers auto-approval."""
        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(self.mock_install_plan)

            self.assertTrue(result)
            mock_log.assert_called_with(self.logging_messages["auto_approve"])

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch.dict(os.environ, {"HATCH_AUTO_APPROVE": "YES"})
    def test_environment_variable_case_insensitive(self, mock_isatty):
        """Test HATCH_AUTO_APPROVE is case-insensitive."""
        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(self.mock_install_plan)

            self.assertTrue(result)
            mock_log.assert_called_with(self.logging_messages["auto_approve"])

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch.dict(os.environ, {"HATCH_AUTO_APPROVE": "invalid"})
    @patch("builtins.input", return_value="y")
    def test_environment_variable_invalid_value(self, mock_input, mock_isatty):
        """Test invalid HATCH_AUTO_APPROVE value falls back to TTY behavior."""
        result = self.orchestrator._request_user_consent(self.mock_install_plan)

        self.assertTrue(result)
        mock_input.assert_called_once()

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", side_effect=EOFError())
    def test_eof_error_handling(self, mock_input, mock_isatty):
        """Test EOFError handling in interactive mode."""
        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(self.mock_install_plan)

            self.assertFalse(result)
            mock_log.assert_called_with(self.logging_messages["user_cancelled"])

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_keyboard_interrupt_handling(self, mock_input, mock_isatty):
        """Test KeyboardInterrupt handling in interactive mode."""
        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(self.mock_install_plan)

            self.assertFalse(result)
            mock_log.assert_called_with(self.logging_messages["user_cancelled"])


class TestEnvironmentVariableScenarios(unittest.TestCase):
    """Test comprehensive environment variable scenarios using centralized test data."""

    def setUp(self):
        """Set up test environment with centralized test data."""
        # Create mock dependencies for orchestrator
        self.mock_package_loader = MagicMock(spec=HatchPackageLoader)
        self.mock_registry_data = {
            "registry_schema_version": "1.1.0",
            "repositories": [],
        }
        self.mock_registry_service = MagicMock(spec=RegistryService)

        # Create orchestrator with mocked dependencies
        self.orchestrator = DependencyInstallerOrchestrator(
            package_loader=self.mock_package_loader,
            registry_service=self.mock_registry_service,
            registry_data=self.mock_registry_data,
        )

        self.test_data = NonTTYTestDataLoader()
        self.mock_install_plan = self.test_data.get_installation_plan(
            "basic_python_plan"
        )
        self.env_scenarios = self.test_data.get_environment_variable_scenarios()
        self.logging_messages = self.test_data.get_logging_messages()

    @regression_test
    @patch("sys.stdin.isatty", return_value=True)
    @patch("builtins.input", return_value="n")  # Mock input for fallback cases to deny
    def test_all_environment_variable_scenarios(self, mock_input, mock_isatty):
        """Test all environment variable scenarios from centralized test data."""
        for scenario in self.env_scenarios:
            with self.subTest(scenario=scenario["name"]):
                with patch.dict(os.environ, {"HATCH_AUTO_APPROVE": scenario["value"]}):
                    with patch.object(self.orchestrator.logger, "info") as mock_log:
                        result = self.orchestrator._request_user_consent(
                            self.mock_install_plan
                        )

                        self.assertEqual(
                            result,
                            scenario["expected"],
                            f"Failed for scenario: {scenario['name']} with value: {scenario['value']}",
                        )

                        if scenario["expected"]:
                            mock_log.assert_called_with(
                                self.logging_messages["auto_approve"]
                            )


class TestInstallationPlanVariations(unittest.TestCase):
    """Test consent handling with different installation plan variations."""

    def setUp(self):
        """Set up test environment with centralized test data."""
        # Create mock dependencies for orchestrator
        self.mock_package_loader = MagicMock(spec=HatchPackageLoader)
        self.mock_registry_data = {
            "registry_schema_version": "1.1.0",
            "repositories": [],
        }
        self.mock_registry_service = MagicMock(spec=RegistryService)

        # Create orchestrator with mocked dependencies
        self.orchestrator = DependencyInstallerOrchestrator(
            package_loader=self.mock_package_loader,
            registry_service=self.mock_registry_service,
            registry_data=self.mock_registry_data,
        )

        self.test_data = NonTTYTestDataLoader()

    @regression_test
    @patch("sys.stdin.isatty", return_value=False)
    def test_non_tty_with_empty_plan(self, mock_isatty):
        """Test non-TTY behavior with empty installation plan."""
        empty_plan = self.test_data.get_installation_plan("empty_plan")

        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(empty_plan)

            self.assertTrue(result)
            mock_log.assert_called_with(
                self.test_data.get_logging_messages()["auto_approve"]
            )

    @regression_test
    @patch("sys.stdin.isatty", return_value=False)
    def test_non_tty_with_complex_plan(self, mock_isatty):
        """Test non-TTY behavior with complex installation plan."""
        complex_plan = self.test_data.get_installation_plan("complex_plan")

        with patch.object(self.orchestrator.logger, "info") as mock_log:
            result = self.orchestrator._request_user_consent(complex_plan)

            self.assertTrue(result)
            mock_log.assert_called_with(
                self.test_data.get_logging_messages()["auto_approve"]
            )


if __name__ == "__main__":
    unittest.main()
