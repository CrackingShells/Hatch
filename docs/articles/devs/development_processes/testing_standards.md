# Testing Standards

This article is about:

- Testing requirements, patterns, and best practices for Hatch development
- Test organization and naming conventions
- Testing tools and infrastructure usage

## Overview

Hatch follows comprehensive testing standards to ensure code quality, prevent regressions, and validate new functionality. All contributors must understand and follow these testing standards when making changes to the codebase.

## Testing Philosophy

### Quality Assurance Goals

- **Prevent Regressions** - Ensure existing functionality continues to work
- **Validate New Features** - Confirm new functionality works as designed
- **Enable Refactoring** - Provide confidence when improving code structure
- **Document Behavior** - Tests serve as executable documentation

### Testing Principles

- **Test Early and Often** - Write tests as you develop, not after --> prefix with `dev_test_*.py`
- **Test at Multiple Levels** - Unit, integration, and end-to-end testing
- **Test Edge Cases** - Cover error conditions and boundary cases
- **Keep Tests Simple** - Each test should verify one specific behavior

## Test Organization

### Test Runner

All tests are executed via the central test runner: `run_tests.py` located in project roots. `run_tests.py` dispatches to the Python standard library `unittest` test discovery by default, and it provides flags for selecting test types (development/regression/feature) and verbosity.

Example usage:

```bash
# Run all tests (uses unittest discovery)
python run_tests.py

# Run specific test types
python run_tests.py --development
python run_tests.py --regression
python run_tests.py --feature

# Run tests matching pattern (if supported by run_tests.py)
python run_tests.py --pattern "*environment*"

# Run with verbose output
python run_tests.py --verbose
```

### Test File Naming Conventions

In this repository the common and established pattern is `test_*.py` files under the `tests/` folder (for example `tests/test_python_installer.py`).

Guidance:

- Primary pattern: `test_<module_or_feature>.py` (e.g. `test_python_installer.py`, `test_registry.py`).
- Tests are organized by topic and typically include `unittest.TestCase` subclasses and helper functions.
- If you need to create temporary developer-only tests you may prefix them with `dev_` (for example `dev_test_new_feature.py`) or place them in a `tests/dev/` directory, but prefer landing permanent tests as `test_*.py` so they are discoverable by default.

Examples you will find in the repository:

```txt
tests/
├── test_python_installer.py
├── test_registry.py
├── test_env_manip.py
└── test_python_environment_manager.py
```

### Test File Placement

Place test files in dedicated `tests/` directories at the project root:

```txt
Hatch/
├── tests/
│   ├── dev_test_environment_manager.py
│   ├── regression_test_package_installation.py
│   └── feature_test_python_env_integration.py
├── hatch/
└── run_tests.py
```

## Test Types and Lifecycle

### Test Types & Lifecycle

The codebase primarily uses `unittest` test files named `test_*.py`. Tests fall into three practical categories (development, regression, feature) but the repository's pattern is to keep the discoverable filename as `test_*.py`. Use directory layout or filename prefixes (for example `tests/dev/` or `dev_test_*.py`) to mark transient development tests.

Characteristics by category:

- Development tests: temporary, may be placed under `tests/dev/` or prefixed with `dev_`. Remove or convert before merging.
- Regression tests: permanent, cover previously fixed bugs and stable behavior. Keep these in `tests/` with a clear name and thorough assertions.
- Feature tests: permanent, cover new feature behavior and edge cases; these can become regression tests over time.

Key rule: make tests discoverable by `python -m unittest discover -s tests -p "test_*.py"` and use clear names and docstrings to describe purpose.

### Repository test patterns (what you'll see)

Practical patterns used across the existing `tests/` files — follow these so tests are consistent and maintainable:

- Test files are named `test_*.py` and live under `tests/`.
- Tests use `unittest.TestCase` subclasses and the standard assertion methods (`self.assertEqual`, `self.assertTrue`, `self.assertRaises`, etc.). When adding tests, prefer the `unittest` assertion methods for clearer error messages and consistency.
- Use `setUp`/`tearDown` for per-test setup/cleanup. For slower integration suites use `setUpClass`/`tearDownClass` to prepare/clean shared resources.
- Temporary filesystem resources are created with `tempfile` and cleaned with `shutil.rmtree` in `tearDown`.
- Use `unittest.mock.patch` frequently; decorators are used to patch functions or methods at import paths (e.g., `@patch('hatch.module.Class.method')`).
- Some tests modify `sys.path` at module top-level to import local packages for direct testing; prefer installing the package in editable mode during development, but keep `sys.path` inserts when necessary for simple test execution.
- Integration tests often guard against missing external tools and call `unittest.SkipTest` or raise SkipTest in `setUpClass` to avoid running on systems without required dependencies.
- Tests commonly include a `if __name__ == '__main__':` guard that calls `unittest.main()` (often with `verbosity=2`) so tests can be run directly.
- Use `unittest-xml-reporting` in CI to produce xUnit XML reports if required by the CI system; tests themselves don't need to change to support this.

When writing or updating tests, mirror these patterns so other contributors won't be surprised when cross-checking documentation and implementation.

## Testing Patterns and Best Practices

### Test Structure

Follow the Arrange-Act-Assert pattern. Prefer `unittest.TestCase` methods to keep examples consistent with the repository tests:

```python
import unittest

class TestPackageLoading(unittest.TestCase):
    def test_package_loading(self):
        # Arrange - Set up test data and conditions
        package_path = create_test_package()
        loader = HatchPackageLoader()

        # Act - Perform the action being tested
        metadata = loader.load_package(package_path)

        # Assert - Verify the expected outcome
        self.assertEqual(metadata.name, "test-package")
        self.assertEqual(metadata.version, "1.0.0")

```

### Mocking External Dependencies

Use mocks for external systems and dependencies (use `unittest.mock` which is part of the standard library):

```python
from unittest.mock import Mock, patch
import unittest

def test_registry_retrieval_with_network_error():
    """Test registry retrieval handles network errors gracefully."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.ConnectionError("Network error")

        retriever = RegistryRetriever()

        with unittest.TestCase().assertRaises(NetworkError):
            retriever.retrieve_package("test-package")
```

### Fixture Usage

In `unittest` use `setUp`/`tearDown` or class-level `setUpClass`/`tearDownClass` for shared fixtures.

```python
import unittest

class TestPackageInstallation(unittest.TestCase):
    def setUp(self):
        self.manager = HatchEnvironmentManager()
        self.env_name = "test-fixture-env"
        self.manager.create_environment(self.env_name)

    def tearDown(self):
        if self.manager.environment_exists(self.env_name):
            self.manager.remove_environment(self.env_name)

    def test_package_installation(self):
        self.assertTrue(self.manager.environment_exists(self.env_name))
        # further assertions here
```

## Testing Tools and Infrastructure

### Test Configuration

Unittest does not use a central ini file; configuration is handled by `run_tests.py` and by CI job configuration. Recommended conventions:

- Tests live under `tests/` and follow the file naming patterns described above (e.g. `dev_test_*.py`, `regression_test_*.py`, `feature_test_*.py`).
- Use `python -m unittest discover -s tests -p "*_test_*.py"` for discovery when running directly.
- Use `coverage` to collect coverage and enforce thresholds (examples below).

## Testing Specific Components

### Environment Management Testing

```python
import unittest

class TestEnvironmentIsolation(unittest.TestCase):
    def test_environment_isolation(self):
        """Test that environments are properly isolated."""
        manager = HatchEnvironmentManager()

        # Create two environments
        env1 = manager.create_environment("env1")
        env2 = manager.create_environment("env2")

        # Install different packages in each
        env1.install_package("package-a")
        env2.install_package("package-b")

        # Verify isolation
        self.assertIn("package-a", env1.list_packages())
        self.assertNotIn("package-a", env2.list_packages())

```

### Installer Testing

```python
import unittest

class TestInstallerErrorHandling(unittest.TestCase):
    def test_installer_error_handling(self):
        """Test installer handles errors gracefully."""
        installer = PythonInstaller()
        invalid_dependency = {"type": "python", "name": "nonexistent-package"}
        context = InstallationContext()

        result = installer.install_dependency(invalid_dependency, context)

        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message.lower())

```

### Registry Testing

```python
import unittest
from unittest.mock import patch

class TestRegistryCaching(unittest.TestCase):
    def test_registry_caching(self):
        """Test registry caching behavior."""
        retriever = RegistryRetriever()
        package_name = "test-package"

        # First retrieval should hit network
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"version": "1.0.0"}

            result1 = retriever.get_package_info(package_name)
            self.assertEqual(mock_get.call_count, 1)

        # Second retrieval should use cache
        with patch('requests.get') as mock_get:
            result2 = retriever.get_package_info(package_name)
            self.assertEqual(mock_get.call_count, 0)  # No network call
            self.assertEqual(result1, result2)

```

## Related Documentation

- [Development Environment Setup](./developer_onboarding.md) - Setting up testing environment
- [Contribution Guidelines](../contribution_guides/how_to_contribute.md) - Testing requirements for contributions
- [Implementation Guides](../implementation_guides/index.md) - Testing specific components
