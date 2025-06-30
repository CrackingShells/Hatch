I'll update the implementation plan to correctly reflect the existing design patterns and requirements you've outlined.

# Implementation Plan: Cross-Platform Python Environment Management with Mamba/Conda Support

## Overview
**Objective:** Design and implement robust, cross-platform Python environment management for the Hatch package manager, supporting per-environment Python isolation using mamba/conda, with environments installed under the Hatch environment directory.

**Key constraints:**
- Support `--no-python` and `--python-version` flags  
- Use streamlined CLI with positional arguments (no `--env`)
- Integrate with existing test runner run_environment_tests.py
- Encapsulate mamba/conda logic in dedicated `python_environment_manager.py`
- Install Python environments locally under each Hatch environment directory
- Environment naming: `hatch_<env_name>` in conda/mamba
- Cross-platform compatibility (Windows, Linux, macOS)
- Follow existing design patterns with python_installer.py and `registry.py`
- Integrate with `set_current_environment()` to automatically switch Python environments

## Phase 1: Foundation - Python Environment Manager Class
**Goal:** Create the dedicated `PythonEnvironmentManager` class to handle all mamba/conda operations.

### Actions:

1. **Action 1.1:** Create `PythonEnvironmentManager` class structure
   - **Preconditions:** Understanding of existing `HatchEnvironmentManager` interface and mamba/conda command patterns
   - **Details:** Create `hatch/python_environment_manager.py` with class definition, initialization, and core interface methods
   - **Context:**
     - Files: `hatch/python_environment_manager.py` (new), environment_manager.py
     - Directories: hatch
     - Symbols: `PythonEnvironmentManager`, `HatchEnvironmentManager`
     - Other context: Mamba/conda command-line interface patterns, cross-platform path handling
   - **Postconditions:** `PythonEnvironmentManager` class exists with proper initialization and logging setup
   - **Validation:**
     - **Development tests:** `dev_test_python_env_manager_creation.py` - verify class can be instantiated and basic properties are set
     - **Verification method:** Import and instantiate class without errors, verify logger is configured

2. **Action 1.2:** Implement conda/mamba environment detection and validation
   - **Preconditions:** `PythonEnvironmentManager` class structure exists
   - **Details:** Add methods to detect conda/mamba availability, validate installation, and check for environment conflicts
   - **Context:**
     - Files: `hatch/python_environment_manager.py`
     - Directories: hatch
     - Symbols: `PythonEnvironmentManager._detect_conda_mamba()`, `PythonEnvironmentManager._validate_conda_installation()`
     - Other context: Cross-platform executable detection patterns, conda/mamba command availability
   - **Postconditions:** Manager can detect and validate conda/mamba availability across platforms
   - **Validation:**
     - **Development tests:** `dev_test_conda_detection.py` - mock conda/mamba availability and verify detection logic
     - **Verification method:** Test on systems with and without conda/mamba, verify appropriate error handling

3. **Action 1.3:** Implement Python environment creation with local installation
   - **Preconditions:** Conda/mamba detection is working
   - **Details:** Add `create_python_environment()` method that creates conda environments locally under each Hatch environment directory
   - **Context:**
     - Files: `hatch/python_environment_manager.py`
     - Directories: hatch, `~/.hatch/envs/<env_name>/`
     - Symbols: `PythonEnvironmentManager.create_python_environment()`, `HatchEnvironmentManager.get_environment_path()`
     - Other context: Conda environment creation commands, local prefix handling, naming convention `hatch_<env_name>`
   - **Postconditions:** Can create Python environments locally within Hatch environment directories
   - **Validation:**
     - **Development tests:** `dev_test_python_env_creation.py` - verify environment creation with different Python versions
     - **Verification method:** Check that conda environment is created in expected local directory structure

### Phase Completion Criteria:
- `PythonEnvironmentManager` class exists and can be instantiated
- Conda/mamba detection works across platforms
- Python environment creation installs locally under Hatch environment directories
- **Regression tests:** `regression_test_existing_env_manager.py` - ensure existing environment functionality is preserved

## Phase 2: Core Environment Operations
**Goal:** Implement all core Python environment management operations with proper integration points.

### Actions:

1. **Action 2.1:** Implement environment lifecycle operations
   - **Preconditions:** Basic environment creation is working
   - **Details:** Add methods for environment removal, activation/deactivation, and info retrieval
   - **Context:**
     - Files: `hatch/python_environment_manager.py`
     - Directories: hatch
     - Symbols: `PythonEnvironmentManager.remove_python_environment()`, `PythonEnvironmentManager.get_python_environment_info()`, `PythonEnvironmentManager.get_python_executable()`
     - Other context: Conda environment lifecycle commands, path manipulation for Python executable discovery
   - **Postconditions:** Complete lifecycle management of Python environments with executable path discovery
   - **Validation:**
     - **Development tests:** `dev_test_python_env_lifecycle.py` - test create, info, executable discovery, remove cycle
     - **Verification method:** Verify environments can be created, queried, Python executable located, and cleanly removed

2. **Action 2.2:** Implement flag support and CLI integration points
   - **Preconditions:** Core environment operations work
   - **Details:** Add support for `--no-python` and `--python-version` flags, integrate with environment metadata tracking
   - **Context:**
     - Files: `hatch/python_environment_manager.py`, environment_manager.py
     - Directories: hatch
     - Symbols: `PythonEnvironmentManager.create_with_flags()`, `HatchEnvironmentManager._add_package_to_env_data()`
     - Other context: CLI argument parsing patterns, environment metadata structure
   - **Postconditions:** Full flag support integrated with environment metadata
   - **Validation:**
     - **Development tests:** `dev_test_flag_support.py` - test --no-python and --python-version flag handling
     - **Verification method:** Create environments with various flag combinations, verify metadata is stored correctly

3. **Action 2.3:** Implement Python executable resolution for InstallationContext
   - **Preconditions:** Flag support is working
   - **Details:** Add method to get the correct Python executable path for a given environment to be used with `set_config()`
   - **Context:**
     - Files: `hatch/python_environment_manager.py`, installation_context.py, python_installer.py
     - Directories: hatch, installers
     - Symbols: `PythonEnvironmentManager.get_python_executable()`, `InstallationContext.set_config()`, `python_installer.py:189-190`
     - Other context: Python executable path resolution in conda environments, InstallationContext configuration pattern
   - **Postconditions:** Python executable paths can be resolved and configured for use by `PythonInstaller`
   - **Validation:**
     - **Development tests:** `dev_test_python_executable_resolution.py` - test executable path resolution for different environments
     - **Verification method:** Create environments with different Python versions, verify correct executable paths are returned

### Phase Completion Criteria:
- Complete Python environment lifecycle operations work
- Flag support is implemented and integrated with metadata
- Python executable resolution works correctly for InstallationContext integration
- **Regression tests:** `regression_test_environment_isolation.py` - ensure environments remain isolated

## Phase 3: Integration with HatchEnvironmentManager
**Goal:** Integrate `PythonEnvironmentManager` with the existing environment management system and implement automatic Python environment switching.

### Actions:

1. **Action 3.1:** Refactor `HatchEnvironmentManager` to use `PythonEnvironmentManager`
   - **Preconditions:** `PythonEnvironmentManager` is fully functional
   - **Details:** Modify `HatchEnvironmentManager` to delegate Python environment operations to the new manager
   - **Context:**
     - Files: environment_manager.py, `hatch/python_environment_manager.py`
     - Directories: hatch
     - Symbols: `HatchEnvironmentManager.__init__()`, `HatchEnvironmentManager.create_environment()`, `PythonEnvironmentManager`
     - Other context: Dependency injection patterns, existing environment creation workflow
   - **Postconditions:** `HatchEnvironmentManager` uses `PythonEnvironmentManager` for Python environment operations
   - **Validation:**
     - **Development tests:** `dev_test_manager_integration.py` - verify delegation works correctly
     - **Verification method:** Create environments through existing interface, verify Python environments are created via new manager

2. **Action 3.2:** Implement automatic Python environment switching in `set_current_environment()`
   - **Preconditions:** Manager integration is working
   - **Details:** Modify `set_current_environment()` to automatically switch to the corresponding Python environment and configure the InstallationContext
   - **Context:**
     - Files: environment_manager.py, `hatch/python_environment_manager.py`, installation_context.py
     - Directories: hatch
     - Symbols: `HatchEnvironmentManager.set_current_environment()`, `PythonEnvironmentManager.get_python_executable()`, `InstallationContext.set_config()`
     - Other context: Environment switching workflow, InstallationContext configuration for PythonInstaller
   - **Postconditions:** Switching environments automatically configures the correct Python executable for package installation
   - **Validation:**
     - **Development tests:** `dev_test_environment_switching.py` - verify Python environment switching and context configuration
     - **Verification method:** Switch between environments, verify correct Python executable is configured in InstallationContext

3. **Action 3.3:** Update environment metadata to track Python environment details
   - **Preconditions:** Environment switching is working
   - **Details:** Extend environment metadata to include Python environment information, version, and local conda environment details
   - **Context:**
     - Files: environment_manager.py, `hatch/python_environment_manager.py`
     - Directories: hatch
     - Symbols: `HatchEnvironmentManager._add_package_to_env_data()`, `HatchEnvironmentManager._environments`, environment metadata schema
     - Other context: JSON schema for environment metadata, backward compatibility considerations
   - **Postconditions:** Environment metadata includes Python environment details and executable paths
   - **Validation:**
     - **Development tests:** `dev_test_metadata_tracking.py` - verify metadata is stored and retrieved correctly
     - **Verification method:** Create environments, check that metadata includes Python environment information

4. **Action 3.4:** Implement environment cleanup and error handling
   - **Preconditions:** Metadata tracking is working
   - **Details:** Add proper cleanup for Python environments during environment removal, implement comprehensive error handling
   - **Context:**
     - Files: environment_manager.py, `hatch/python_environment_manager.py`
     - Directories: hatch
     - Symbols: `HatchEnvironmentManager.remove_environment()`, `PythonEnvironmentManager.remove_python_environment()`, error handling patterns
     - Other context: Cross-platform cleanup procedures, conda environment removal
   - **Postconditions:** Complete cleanup and robust error handling for Python environments
   - **Validation:**
     - **Development tests:** `dev_test_cleanup_error_handling.py` - test cleanup and error scenarios
     - **Verification method:** Remove environments, verify all Python environment artifacts are cleaned up

### Phase Completion Criteria:
- `HatchEnvironmentManager` successfully delegates to `PythonEnvironmentManager`
- `set_current_environment()` automatically switches Python environments and configures InstallationContext
- Environment metadata properly tracks Python environment details
- Cleanup and error handling work correctly across all operations
- **Regression tests:** `regression_test_full_integration.py` - ensure all existing functionality works with new integration

## Phase 4: CLI Updates and Testing
**Goal:** Update CLI to support the new Python environment features and ensure comprehensive test coverage.

### Actions:

1. **Action 4.1:** Update CLI argument parsing for Python environment flags
   - **Preconditions:** Full integration is working
   - **Details:** Modify cli_hatch.py to support `--no-python` and `--python-version` flags with positional environment arguments
   - **Context:**
     - Files: cli_hatch.py, environment_manager.py
     - Directories: hatch
     - Symbols: `main()`, argparse configuration, environment command handlers
     - Other context: Existing CLI patterns, positional argument handling
   - **Postconditions:** CLI supports new Python environment flags with streamlined interface
   - **Validation:**
     - **Development tests:** `dev_test_cli_python_flags.py` - test CLI argument parsing for Python environment features
     - **Verification method:** Run CLI commands with various flag combinations, verify correct delegation to environment manager

2. **Action 4.2:** Create comprehensive test suite for `PythonEnvironmentManager`
   - **Preconditions:** CLI updates are complete
   - **Details:** Create `tests/test_python_environment_manager.py` with comprehensive coverage of all Python environment management features
   - **Context:**
     - Files: `tests/test_python_environment_manager.py` (new), run_environment_tests.py
     - Directories: tests
     - Symbols: `TestPythonEnvironmentManager`, run_environment_tests.py test discovery pattern
     - Other context: Existing test patterns from test_env_manip.py, test_python_installer.py
   - **Postconditions:** Comprehensive test coverage for `PythonEnvironmentManager` discoverable by test runner
   - **Validation:**
     - **Development tests:** `dev_test_test_discovery.py` - verify tests are discovered by run_environment_tests.py
     - **Verification method:** Run test suite, verify all Python environment manager functionality is tested

3. **Action 4.3:** Update integration tests and ensure test runner compatibility
   - **Preconditions:** New test suite exists
   - **Details:** Update existing integration tests, ensure run_environment_tests.py can discover and run all new tests
   - **Context:**
     - Files: run_environment_tests.py, test_env_manip.py, `tests/test_python_environment_manager.py`
     - Directories: tests
     - Symbols: test discovery patterns, `unittest.TestLoader`, existing test classes
     - Other context: Test naming conventions, integration with existing test infrastructure
   - **Postconditions:** All tests integrate with existing test runner and pass consistently
   - **Validation:**
     - **Development tests:** `dev_test_runner_integration.py` - verify test runner can execute all tests
     - **Verification method:** Run run_environment_tests.py with various flags, verify new tests are included and pass

### Phase Completion Criteria:
- CLI supports `--no-python` and `--python-version` flags with positional arguments
- Comprehensive test coverage for all Python environment management features
- All tests integrate with run_environment_tests.py and pass consistently
- **Feature tests:** `feature_test_python_env_management.py` - end-to-end testing of complete Python environment management workflow

## Testing Strategy

### About Test Files
All tests centralize around run_environment_tests.py which:
- Executes all tests in the codebase
- Has flags for different test types (e.g., `--python-env-only`, `--regression`, `--feature`)

Test files follow naming convention `<test_type>_test_<test_name>.py`:
- **Development tests:** `dev_test_<test_name>.py` - temporary tests for validation during implementation
- **Regression tests:** `regression_test_<test_name>.py` - permanent tests ensuring existing functionality isn't broken
- **Feature tests:** `feature_test_<test_name>.py` - permanent tests confirming new functionality works as expected

### Types of Tests
- **Development tests:** Temporary tests created to validate specific action postconditions, can be discarded after successful implementation
- **Regression tests:** Ensure existing `HatchEnvironmentManager` functionality continues to work unchanged, including that `PythonInstaller` receives correct Python executable via `InstallationContext.set_config()`
- **Feature tests:** Document and verify all new Python environment management capabilities work end-to-end, including automatic environment switching and correct Python executable configuration