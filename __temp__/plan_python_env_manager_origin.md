# Revised Implementation Plan: Python Environment Management with Mamba

## Overview
**Objective:**  
Enable each Hatch environment to manage its own isolated Python environment using **mamba/conda**, ensuring that Python dependencies for MCP servers/packages are installed in the correct, environment-specific Python interpreter, leveraging mamba's ability to automatically install any Python version.

**Key constraints:**  
- Use **mamba** (or conda as fallback) for Python environment creation and management
- Python environments created as named conda environments: `hatch_<env_name>`
- Support `--no-python` flag to skip Python environment creation
- Support `--python-version` flag to specify Python version (mamba will install it automatically)
- Streamlined CLI with positional environment names (no `--env` flags)
- Tests must integrate with `run_environment_tests.py`
- **Requirement:** Users must have Miniforge/Miniconda and mamba installed
- Cross-platform support (Windows, macOS, Linux)
- Clear documentation of mamba dependency

---

## Phase 1: Mamba Integration and Environment Metadata

**Goal:**  
Replace venv-based Python environment creation with mamba-based conda environments and update metadata structure.

### Actions:

1. **Action 1.1:** Update environment metadata structure for mamba environments
   - **Preconditions:** Existing environment management code and metadata structure in `environments.json`.
   - **Details:** Modify the environment data structure to include a `python_env` field optimized for conda/mamba environments.
   - **Context:**  
     - Files: `environment_manager.py`, `environments.json`
     - Symbols: `_initialize_environments_file`, `create_environment`, environment data structures
   - **Postconditions:** Environment metadata supports mamba-based Python environment configuration:
     ```json
     "python_env": {
       "enabled": true,
       "conda_env_name": "hatch_myenv",
       "python_executable": "/path/to/conda/envs/hatch_myenv/bin/python",
       "created_at": "2025-06-29T10:30:00",
       "version": "3.11.8",
       "requested_version": "3.11",
       "manager": "mamba"
     }
     ```
   - **Validation:**  
     - **Development tests:** Create environments and verify metadata structure persists correctly.
     - **Verification method:** Inspect `environments.json` for new conda-specific fields.

2. **Action 1.2:** Add mamba/conda detection and validation
   - **Preconditions:** Updated metadata structure supports conda environment configuration.
   - **Details:** Add methods to detect if mamba/conda is available on the system and validate installation.
   - **Context:**  
     - Files: `environment_manager.py`
     - Symbols: New `_detect_conda_manager`, `_validate_conda_installation` methods
   - **Postconditions:** 
     - System can detect and prefer mamba over conda
     - Clear error messages when mamba/conda is not available
     - Fallback detection logic (mamba → conda → error)
   - **Validation:**  
     - **Development tests:** Test detection with and without mamba/conda installed.
     - **Verification method:** Check detection results and error messages.

3. **Action 1.3:** Implement mamba-based Python environment creation
   - **Preconditions:** Mamba detection works and environment metadata structure is updated.
   - **Details:** Replace `_create_python_environment` to use mamba for creating conda environments with specified Python versions.
   - **Context:**  
     - Files: `environment_manager.py`
     - Symbols: Replace `_create_python_environment`, new `_create_conda_environment` method
     - Other context: `subprocess` for mamba/conda commands, conda environment naming conventions
   - **Postconditions:** 
     - Python environments are created as named conda environments
     - Mamba automatically installs requested Python versions
     - Environment metadata contains conda-specific information
   - **Validation:**  
     - **Development tests:** Create environments with different Python versions.
     - **Verification method:** Check conda environment list and Python version in created environments.

### Phase Completion Criteria:
- Environment metadata supports mamba/conda environment configuration
- Mamba/conda detection and validation works reliably
- Python environments are created using mamba with automatic Python version installation
- **Regression tests:** Basic environment creation flows work with new backend

---

## Phase 2: Environment Lifecycle Management with Mamba

**Goal:**  
Update environment operations (activation, validation, removal) to work with conda environments.

### Actions:

1. **Action 2.1:** Update environment activation and Python executable resolution
   - **Preconditions:** Mamba environments can be created and metadata contains conda environment names.
   - **Details:** Modify `set_current_environment` to resolve Python executable from conda environment and configure installation context.
   - **Context:**  
     - Files: `environment_manager.py`, `installation_context.py`
     - Symbols: `set_current_environment`, `set_config`, conda environment path resolution
   - **Postconditions:** When switching environments, the installation context uses the conda environment's Python executable.
   - **Validation:**  
     - **Development tests:** Switch environments and verify correct conda Python executable is configured.
     - **Verification method:** Check context configuration points to conda environment Python.

2. **Action 2.2:** Update environment validation for conda environments
   - **Preconditions:** Conda environments can be created and managed.
   - **Details:** Modify `_validate_python_environment` to check conda environment existence and health using `conda info`.
   - **Context:**  
     - Files: `environment_manager.py`
     - Symbols: `_validate_python_environment`, conda environment validation commands
   - **Postconditions:** 
     - Environment validation checks conda environment status
     - Broken or missing conda environments are detected
     - Validation uses `conda list` or `conda info` for health checks
   - **Validation:**  
     - **Development tests:** Validate environments in various states (healthy, missing, corrupted).
     - **Verification method:** Check validation results match actual conda environment state.

3. **Action 2.3:** Update environment removal to clean up conda environments
   - **Preconditions:** Conda environments are created and tracked in metadata.
   - **Details:** Modify `remove_environment` and `remove_python_environment` to properly remove conda environments using `mamba env remove`.
   - **Context:**  
     - Files: `environment_manager.py`
     - Symbols: `remove_environment`, `remove_python_environment`, conda environment removal commands
   - **Postconditions:** 
     - Removing Hatch environments also removes associated conda environments
     - Conda environment cleanup is atomic and safe
   - **Validation:**  
     - **Development tests:** Remove environments and verify conda environments are cleaned up.
     - **Verification method:** Check `conda env list` after environment removal.

### Phase Completion Criteria:
- Environment switching configures conda environment Python executable correctly
- Environment validation works with conda environments
- Environment removal properly cleans up conda environments
- **Regression tests:** Environment lifecycle operations work with conda backend

---

## Phase 3: CLI Integration and User Experience

**Goal:**  
Update CLI commands to support mamba-based Python environment management with clear user feedback.

### Actions:

1. **Action 3.1:** Update CLI commands with mamba-specific options
   - **Preconditions:** Mamba-based environment management is implemented.
   - **Details:** Update CLI commands to reflect mamba usage and add mamba-specific options where appropriate.
   - **Context:**  
     - Files: `cli_hatch.py`, `environment_manager.py`
     - Symbols: CLI argument parsing, environment creation/management methods
   - **Postconditions:** CLI commands support:
     - `hatch env create <name> [--no-python] [--python-version <version>]`
     - `hatch env python-init <name> [--python-version <version>]`
     - `hatch env python-info <name>` (shows conda environment info)
     - `hatch env python-remove <name>`
     - `hatch env python-shell <name>` (activates conda environment)
   - **Validation:**  
     - **Development tests:** Execute CLI commands and verify mamba operations.
     - **Verification method:** Check conda environment creation and CLI output.

2. **Action 3.2:** Enhance environment listing with conda environment information
   - **Preconditions:** Conda environments are tracked and can be validated.
   - **Details:** Update `list_environments` and CLI display to show conda environment names, Python versions, and conda-specific status.
   - **Context:**  
     - Files: `environment_manager.py`, `cli_hatch.py`
     - Symbols: `list_environments`, CLI environment display logic
   - **Postconditions:** 
     - Environment listing shows conda environment names
     - Python version information includes mamba-installed versions
     - Clear indication of conda vs non-conda environments
   - **Validation:**  
     - **Development tests:** List environments and verify conda information display.
     - **Verification method:** Check CLI output format and conda environment details.

3. **Action 3.3:** Add conda environment diagnostics and troubleshooting
   - **Preconditions:** Mamba detection and environment management work.
   - **Details:** Add commands and features to help users troubleshoot conda/mamba installation and environment issues.
   - **Context:**  
     - Files: `environment_manager.py`, `cli_hatch.py`
     - Symbols: New diagnostic methods, CLI help and error messages
   - **Postconditions:** 
     - Clear error messages when mamba/conda is not found
     - Diagnostic command to check mamba/conda installation
     - Helpful suggestions for installing Miniforge/mamba
   - **Validation:**  
     - **Development tests:** Test error scenarios and diagnostic features.
     - **Verification method:** Check error messages and diagnostic output quality.

### Phase Completion Criteria:
- Complete CLI interface works with mamba-based environments
- Environment listing shows comprehensive conda environment information
- Clear diagnostics and error messages for mamba/conda issues
- **Regression tests:** CLI functionality works with new conda backend

---

## Phase 4: Testing and Documentation

**Goal:**  
Implement comprehensive tests and documentation for mamba-based Python environment management.

### Actions:

1. **Action 4.1:** Create mamba-specific development tests
   - **Preconditions:** Mamba-based environment management is fully implemented.
   - **Details:** Create `dev_test_env_mamba.py` with tests specific to conda/mamba functionality.
   - **Context:**  
     - Files: New `tests/dev_test_env_mamba.py`, existing test infrastructure
     - Symbols: Test classes for mamba detection, conda environment creation, lifecycle management
   - **Postconditions:** 
     - Tests verify mamba detection and fallback logic
     - Tests verify conda environment creation with version specification
     - Tests verify conda environment lifecycle management
   - **Validation:**  
     - **Development tests:** Run mamba tests in environments with/without mamba installed.
     - **Verification method:** All tests pass and cover mamba-specific functionality.

2. **Action 4.2:** Update regression tests for mamba compatibility
   - **Preconditions:** Development tests pass and core functionality is stable.
   - **Details:** Update existing regression tests to work with mamba backend and ensure backward compatibility.
   - **Context:**  
     - Files: regression_test_env_python.py, other existing test files
     - Symbols: Update test assumptions about Python environment backend
   - **Postconditions:** 
     - All existing tests pass with mamba backend
     - Backward compatibility is verified
     - Migration from venv to mamba is tested
   - **Validation:**  
     - **Regression tests:** Run full test suite to ensure no functionality breaks.
     - **Verification method:** All existing tests continue to pass.

3. **Action 4.3:** Create comprehensive documentation
   - **Preconditions:** Implementation and tests are complete.
   - **Details:** Document mamba requirement, installation instructions, and usage patterns.
   - **Context:**  
     - Files: README.md, documentation files
     - Other context: Installation guides for Miniforge, mamba usage examples
   - **Postconditions:** 
     - Clear installation instructions for Miniforge/mamba
     - Usage examples for Python environment management
     - Troubleshooting guide for common mamba issues
     - Migration guide from other Python environment tools
   - **Validation:**  
     - **Verification method:** Documentation review for completeness and clarity.

### Phase Completion Criteria:
- Comprehensive test coverage for mamba functionality
- All regression tests pass with mamba backend
- Complete documentation with installation and usage guides
- **Feature tests:** New mamba-based functionality is fully tested

---

## Updated Metadata Structure

**Environment Metadata with Mamba Environment:**
```json
{
  "name": "myenv",
  "description": "My Hatch environment",
  "created_at": "2025-06-29T10:00:00",
  "packages": [...],
  "python_env": {
    "enabled": true,
    "conda_env_name": "hatch_myenv",
    "python_executable": "/opt/miniconda3/envs/hatch_myenv/bin/python",
    "created_at": "2025-06-29T10:05:00",
    "version": "3.11.8",
    "requested_version": "3.11",
    "manager": "mamba"
  }
}
```

**Environment Metadata without Python Environment:**
```json
{
  "name": "myenv_no_python",
  "description": "Environment without Python isolation",
  "created_at": "2025-06-29T10:00:00",
  "packages": [...],
  "python_env": {
    "enabled": false
  }
}
```

---

## Updated CLI Commands

| Command | Description | Example Usage | Mamba Operation |
|---------|-------------|---------------|------------------|
| `hatch env create <name> [--no-python] [--python-version <ver>]` | Create environment with mamba-managed Python | `hatch env create myenv --python-version 3.11` | `mamba create -n hatch_myenv python=3.11` |
| `hatch env python-init <name> [--python-version <ver>]` | Initialize Python environment using mamba | `hatch env python-init myenv --python-version 3.10` | `mamba create -n hatch_myenv python=3.10` |
| `hatch env python-info <name>` | Show conda environment details | `hatch env python-info myenv` | `conda info --envs`, `conda list -n hatch_myenv` |
| `hatch env python-remove <name>` | Remove conda environment | `hatch env python-remove myenv` | `mamba env remove -n hatch_myenv` |
| `hatch env python-shell <name>` | Activate conda environment shell | `hatch env python-shell myenv` | `conda activate hatch_myenv` |
| `hatch env list` | List environments with conda info | `hatch env list` | `conda env list` integration |

---

## Key Implementation Changes

### Core Methods Update:
```python
def _detect_conda_manager(self) -> Optional[str]:
    """Detect available conda manager (mamba preferred over conda)."""
    
def _create_conda_environment(self, env_name: str, python_version: Optional[str] = None) -> Dict[str, Any]:
    """Create conda environment using mamba/conda."""
    
def _get_conda_python_executable(self, conda_env_name: str) -> str:
    """Get Python executable path from conda environment."""
    
def _validate_conda_environment(self, conda_env_name: str) -> bool:
    """Validate conda environment exists and is functional."""
```

---

## Benefits of Mamba Approach

1. **Automatic Python Installation:** Mamba installs any requested Python version automatically
2. **Cross-platform Consistency:** Same behavior on Windows, macOS, and Linux  
3. **Dependency Management:** Can handle both Python and non-Python dependencies
4. **Environment Isolation:** Superior isolation compared to venv
5. **Performance:** Mamba is significantly faster than conda for environment operations
6. **Reproducibility:** Environments can be exported/imported easily

---

This revised plan leverages mamba's strengths for robust, cross-platform Python environment management while maintaining the same user-facing API design.