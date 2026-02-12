# Hatch Test Suite

## Overview

The Hatch test suite validates the package manager for the Cracking Shells ecosystem.
Tests are organized into a hierarchical directory structure following the
[CrackingShells Testing Standard](../cracking-shells-playbook/instructions/testing.instructions.md).

**Quick start:**

```bash
mamba activate forHatch-dev
python -m pytest tests/ --ignore=tests/test_cli_version.py
```

## Testing Strategy

### Mocking Approach

Tests use `unittest.mock` to isolate units from external dependencies:

- **Subprocess calls** (`subprocess.run`, `subprocess.Popen`) are mocked to avoid
  invoking real system commands (apt-get, pip, conda/mamba, docker).
- **File system operations** are mocked or use `tempfile` for isolation.
- **Network requests** (`requests.get`, `requests.post`) are mocked to avoid
  real HTTP calls to package registries.
- **Platform detection** (`sys.platform`, `shutil.which`) is mocked to test
  cross-platform behavior on any host OS.

### Mock Patching Rule

Always patch where a function is **used**, not where it is **defined**.
See the [testing standard](../cracking-shells-playbook/instructions/testing.instructions.md)
§4.4 for detailed guidance.

### Integration Tests

Integration tests in `tests/integration/` exercise real component interactions
with mocked external boundaries (file system, network, Docker daemon).
They use `@integration_test(scope=...)` decorators from Wobble.

## Shared Fixtures

### `setUpClass` Usage

Several test modules use `setUpClass` to create expensive shared resources once
per test class, avoiding redundant setup across individual tests:

| Module | Shared Resource |
|---|---|
| `test_python_installer.py` | Shared virtual environment for pip integration tests |
| `test_python_environment_manager.py` | Shared conda/mamba environment for manager integration tests |
| `test_hatch_installer.py` | Validates `Hatching-Dev` sibling directory exists |

### Test Data Utilities

`tests/test_data_utils.py` provides centralized data loading:

- **`TestDataLoader`** — loads configs, responses, and packages from `tests/test_data/`.
- **`NonTTYTestDataLoader`** — provides test scenarios for non-TTY environment testing.

### Static Test Packages

`tests/test_data/packages/` contains static Hatch packages organized by category:

- `basic/` — simple packages without dependencies
- `dependencies/` — packages with various dependency types (system, python, docker, mixed)
- `error_scenarios/` — packages that trigger error conditions (circular deps, invalid deps)
- `schema_versions/` — packages using different schema versions

## Test Categories

Tests follow the three-tier categorization from the CrackingShells Testing Standard:

### Regression Tests (`tests/regression/`)

Permanent tests that prevent breaking changes to existing functionality.
Decorated with `@regression_test`.

- `regression/cli/` — CLI output formatting, color logic, table formatting
- `regression/mcp/` — MCP field filtering, validation bug guards

### Integration Tests (`tests/integration/`)

Tests that validate component interactions and end-to-end workflows.
Decorated with `@integration_test(scope=...)`.

- `integration/cli/` — CLI reporter integration, MCP sync workflows
- `integration/mcp/` — Adapter serialization, cross-host sync, host configuration

### Unit Tests (`tests/unit/`)

Tests that validate individual components in isolation.

- `unit/mcp/` — Adapter protocol, adapter registry, config model validation

### Root-Level Tests (`tests/test_*.py`)

Legacy tests not yet migrated to the hierarchical structure.
These cover core functionality: installers, environment management,
package loading, registry, and non-TTY integration.

## Running Tests

```bash
# Run all tests (exclude known collection error)
python -m pytest tests/ --ignore=tests/test_cli_version.py

# Run by category
python -m pytest tests/regression/
python -m pytest tests/integration/
python -m pytest tests/unit/

# Run with timing info
python -m pytest tests/ --ignore=tests/test_cli_version.py --durations=30

# Run a specific test file
python -m pytest tests/test_env_manip.py -v
```

## Known Issues

| Test | Issue | Root Cause |
|---|---|---|
| `test_cli_version.py` | Collection error | `handle_mcp_show` import removed from `cli_mcp.py` |
| `test_hatch_installer.py` (4 tests) | Setup error | Missing `Hatching-Dev` sibling directory |
| `test_color_enum_total_count` | Assertion mismatch | Color enum count changed (15 vs expected 14) |
| `test_get_environment_activation_info_windows` | Path format | Windows path separator test on macOS |
| `test_handler_shows_prompt_before_confirmation` | Assertion | CLI behavior change |
| `test_mcp_show_invalid_subcommand_error` | Assertion | Error message format change |

All issues above are pre-existing and unrelated to the test refactoring.
