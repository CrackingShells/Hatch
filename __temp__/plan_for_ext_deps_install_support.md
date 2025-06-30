
# Phase 1: Extend Validator and Integrate with Hatch

**Goal:**  
Ensure the validator provides a simple, install-ready list of Hatch package dependencies (including `resolved_version`), and refactor Hatch to use this output. Address and fix the API breakage caused by recent validator changes.

---

### Action 1.1: Extend the validator to output install-ready Hatch dependencies

- **Preconditions:**  
  - Existing validator logic for dependency validation and graph traversal.
  - Only Hatch dependencies are relevant for this step.

- **Details:**  
  - Add or extend a method in `HatchPackageValidator` (or a related utility) to return a list of Hatch package dependencies for a given package, in install order (topologically sorted, acyclic).
  - Each dependency object should include:
    - `name`
    - `version_constraint`
    - `resolved_version` (mandatory, to facilitate downstream installation)
  - Use or adapt logic from `version_utils.py` and `package_validator.py` to avoid duplicating dependency parsing or graph traversal.
  - Do **not** include external dependency types in this output; those will be handled by their respective managers.

- **Context**:
  - Files:
    - package_validator.py
    - dependency_graph.py
    - version_utils.py
    - validator.py
  - Symbols:
    - `HatchPackageValidator`
    - `DependencyGraph`
    - Any new method like `get_hatch_dependencies_in_install_order`

- **Postconditions:**  
  - Validator can output a simple, install-ready list of Hatch package dependencies (with `resolved_version`) for a given package.

- **Validation:**
  - **Development tests:** Integration tests using dummy packages to verify correct dependency order, content, and resolved versions.
  - **Verification method:** Compare output to expected install order for known test cases.

---

### Action 1.2: Refactor Hatch to delegate all dependency resolution to the validator and fix API breakage

- **Preconditions:**  
  - Validator provides a method for retrieving install-ready Hatch dependencies (with `resolved_version`).
  - Hatch currently has broken integration due to missing/changed attributes in the validator.

- **Details:**  
  - Refactor Hatch to use the new validator method for all Hatch dependency resolution.
  - Remove any direct access to `dependency_resolver` or other internals that no longer exist in `HatchPackageValidator`.
  - Update all relevant code paths in Hatch (especially in `environment_manager.py`) to use the new API.
  - Ensure that the new integration is robust to future validator changes by relying only on documented, stable APIs.
  - Add or update error handling to provide clear messages if the validator cannot resolve dependencies.

- **Context**:
  - Files:
    - environment_manager.py
    - package_loader.py
    - cli_hatch.py
    - package_validator.py
  - Symbols:
    - `HatchEnvironmentManager`
    - `HatchPackageValidator`
    - Any new/updated method for dependency resolution

- **Postconditions:**  
  - Hatch no longer relies on removed or internal attributes of the validator.
  - All dependency resolution for Hatch packages is delegated to the validator via a stable, public API.
  - The integration is robust and future-proof.

- **Validation:**
  - **Development tests:** Reuse or enhance `test_env_manip.py` to cover package installation, environment creation, and dependency resolution.
  - **Verification method:** Run Hatch end-to-end and confirm no AttributeError or similar integration failures.

---

### Phase 1 Completion Criteria

- Validator provides a simple, install-ready list of Hatch dependencies (with `resolved_version`).
- Hatch uses only the validator for Hatch dependency resolution, with no broken or deprecated API usage.
- All integration and regression tests pass for both validator and Hatch.

---

# Phase 2: Installer Interface, Concrete Installers, and Registry

**Goal:**  
Design a robust, extensible installer interface and registry, and implement installers for all supported types, each in its own file.

---

### Action 2.1: Carefully design the `DependencyInstaller` abstract base class

- **Preconditions:**  
  - Install-ready dependency objects are defined.

- **Details:**  
  - Create `base_installer.py` with `DependencyInstaller` ABC.
  - Define the interface:
    - `install(dependency, env_context, progress_callback=None)`
    - (Optional) `uninstall(dependency, env_context)`
  - Document all parameters and expected behaviors.

- **Context**:
  - Files:
    - `hatch/installers/base_installer.py`
  - Symbols:
    - `DependencyInstaller` (ABC)

- **Postconditions:**  
  - Interface is stable and well-documented.

- **Validation:**
  - **Development tests:** Static type checks, interface tests.
  - **Verification method:** Peer review of interface design.

---

### Action 2.2: Implement and test concrete installers, each in its own file

- **Preconditions:**  
  - Interface is defined.

- **Details:**  
  - Create one file per installer:
    - `hatch_installer.py` (uses `HatchPackageLoader` for file ops)
    - `python_installer.py` (pip logic)
    - `system_installer.py` (system package manager logic)
    - `docker_installer.py` (Docker logic)
  - Each installer implements the interface and handles its dependency type.
  - Use dummy packages from validator tests for realistic scenarios.

- **Context**:
  - Files:
    - `hatch/installers/hatch_installer.py`
    - `hatch/installers/python_installer.py`
    - `hatch/installers/system_installer.py`
    - `hatch/installers/docker_installer.py`
    - package_loader.py
  - Symbols:
    - `HatchInstaller`
    - `PythonInstaller`
    - `SystemInstaller`
    - `DockerInstaller`
    - `HatchPackageLoader`

- **Postconditions:**  
  - Each installer can handle its dependency type.

- **Validation:**
  - **Development tests:** Use dummy packages for install simulation.
  - **Verification method:** Check logs/output for correct installer invocation.

---

### Action 2.3: Implement the installer registry in its own file and test with dummy packages

- **Preconditions:**  
  - Installers are implemented.

- **Details:**  
  - Create `registry.py` for the installer registry.
  - Register each installer with the registry.
  - Test registry lookup and installation using dummy packages, letting the registry orchestrate the process.

- **Context**:
  - Files:
    - `hatch/installers/registry.py`
  - Symbols:
    - `InstallerRegistry`

- **Postconditions:**  
  - Registry correctly delegates to installers.

- **Validation:**
  - **Development tests:** Integration tests using dummy packages.
  - **Verification method:** Confirm correct installer is used for each dependency.

---

### Phase 2 Completion Criteria

- Stable, extensible installer interface in `base_installer.py`.
- All supported types have working installers, each in its own file.
- Registry delegates correctly, implemented in `registry.py`.
- All dummy package scenarios pass.


# Implementation Plan: Phase 3 – Orchestration, Environment Refactor, Parallelization, and Progress Reporting

## Overview
**Objective:**  
Modularize and modernize the installation orchestration, refactor environment management, enable safe parallelization, implement robust progress reporting using the observer pattern, and centralize user consent management.

**Key constraints:**  
- Maintain clear separation of concerns between environment management and installation orchestration.
- Ensure thread/process safety for parallel installs.
- Provide real-time, extensible progress reporting for UI/CLI.
- Centralize user consent at the orchestrator level to provide consistent UX across all dependency types.

---

## Phase 3.1: Refactor Environment Management and Delegate Installation

**Goal:**  
Move all installation orchestration logic out of `environment_manager.py` into a dedicated orchestrator class, and implement centralized user consent management.

### Actions

1. **Action 3.1.1:** Identify and extract all installation-related logic from `environment_manager.py`.
   - **Preconditions:** Installer registry and concrete installers are implemented.
   - **Details:**  
     - Move all code that resolves dependencies, checks that adding the pending_install package is not introducing a circular dependency in the environment, selects installers, and performs installation to a new orchestrator class (e.g., `DependencyInstallerOrchestrator`).
     - Keep only environment lifecycle and state management in `environment_manager.py`.
   - **Context**:
     - Files:  
       - `hatch/environment_manager.py`  
       - `hatch/package_loader.py`  
       - `hatch/installers/` (new directory for installers)  
       - `hatch/installers/registry.py` (installer registry)
     - Symbols:  
       - `HatchEnvironmentManager`  
       - `add_package_to_environment`  
       - `HatchPackageLoader`  
       - `DependencyInstallerOrchestrator` (to be created)
   - **Postconditions:** `environment_manager.py` delegates all installation to the orchestrator.
   - **Validation:**
     - **Development tests:** Integration tests for environment creation, deletion, and package installation.
     - **Verification method:** Code review for separation of concerns.

2. **Action 3.1.2:** Implement centralized user consent management in the orchestrator.
   - **Preconditions:** Orchestrator class is created and dependency aggregation is working.
   - **Details:**  
     - Aggregate all dependencies to be installed (across all types: hatch, python, system, docker).
     - Present a comprehensive summary to the user showing all pending installations.
     - Request a single yes/no confirmation before proceeding with any installations.
     - Support `--yes` flag or config option for automation scenarios (CI/CD).
     - Ensure all installers assume consent has been granted and do not prompt independently.
   - **Context**:
     - Files:  
       - `hatch/installers/dependency_installation_orchestrator.py`
       - CLI/UX layer files
     - Symbols:  
       - `DependencyInstallerOrchestrator.request_user_consent()`
       - `DependencyInstallerOrchestrator.aggregate_install_plan()`
   - **Postconditions:** All dependency installations are gated by a single, clear user consent prompt.
   - **Validation:**
     - **Development tests:** Mock user input scenarios (yes/no/automation).
     - **Verification method:** No installer proceeds without orchestrator-level approval.

3. **Action 3.1.3:** Update all environment-related APIs to use the orchestrator for installation.
   - **Preconditions:** Orchestrator class is implemented with consent management.
   - **Details:**  
     - Refactor methods like `add_package_to_environment` to call the orchestrator.
     - Ensure backward compatibility for public APIs.
     - Pass automation flags and configuration through to orchestrator.
   - **Context**:
     - Files:  
       - `hatch/environment_manager.py`  
       - `hatch/installers/dependency_installation_orchestrator.py`
     - Symbols:  
       - `HatchEnvironmentManager.add_package_to_environment`  
       - `DependencyInstallerOrchestrator.install_dependencies`
   - **Postconditions:** All install flows go through the orchestrator with centralized consent.
   - **Validation:**
     - **Development tests:** Regression and integration tests for all environment operations.

### Phase Completion Criteria
- `environment_manager.py` contains only environment lifecycle/state logic.
- All installation is delegated to the orchestrator with centralized user consent.
- No individual installer prompts for user consent.
- All tests for environment and install flows pass.

---

## Phase 3.2: Implement Orchestration Logic with Parallelization

**Goal:**  
Enable the orchestrator to install non-overlapping dependency types in parallel, with robust error handling and rollback.

### Actions

1. **Action 3.2.1:** Analyze dependency types for safe parallelization.
   - **Preconditions:** Installers are implemented and tested.
   - **Details:**  
     - Identify which dependency types (e.g., hatch, python, docker, system) can be installed in parallel without conflicts.
     - Document any constraints or exceptions.
   - **Context**:
     - Files:  
       - `hatch/installers/base_installer.py`  
       - `hatch/installers/hatch_installer.py`  
       - `hatch/installers/python_installer.py`  
       - `hatch/installers/system_installer.py`  
       - `hatch/installers/docker_installer.py`
     - Symbols:  
       - `DependencyInstaller`  
       - `HatchInstaller`  
       - `PythonInstaller`  
       - `SystemInstaller`  
       - `DockerInstaller`
   - **Postconditions:** Parallelization plan is documented.
   - **Validation:**
     - **Verification method:** Peer review of parallelization plan.

2. **Action 3.2.2:** Implement parallel installation in the orchestrator.
   - **Preconditions:** Parallelization plan is defined.
   - **Details:**  
     - Use threads, async tasks, or process pools to install independent dependencies in parallel.
     - Ensure thread/process safety and proper error propagation.
     - Provide a configuration option to enable/disable parallelization.
   - **Context**:
     - Files:  
       - `hatch/installers/dependency_installation_orchestrator.py`
     - Symbols:  
       - `DependencyInstallerOrchestrator.install_dependencies`
   - **Postconditions:** Orchestrator can install dependencies in parallel where safe.
   - **Validation:**
     - **Development tests:** Simulate parallel installs with dummy packages.
     - **Verification method:** Check for race conditions, correct install order, and error handling.

3. **Action 3.2.3:** Implement robust error handling and rollback.
   - **Preconditions:** Parallel installation logic is in place.
   - **Details:**  
     - Use the Command pattern to encapsulate install/uninstall actions.
     - On failure, roll back previously installed dependencies in reverse order.
   - **Context**:
     - Files:  
       - `hatch/installers/dependency_installation_orchestrator.py`
     - Symbols:  
       - `DependencyInstallerOrchestrator.rollback`
   - **Postconditions:** Partial installs are cleaned up on error.
   - **Validation:**
     - **Development tests:** Simulate failures and verify rollback.
     - **Verification method:** Check environment state after simulated errors.

### Phase Completion Criteria
- Orchestrator supports safe parallel installation.
- Rollback logic is robust and tested.
- All install scenarios (success, partial failure, rollback) are covered by tests.

---

## Phase 3.3: Implement Observer-Based Progress Reporting

**Goal:**  
Provide real-time, extensible progress reporting using the observer (publish-subscribe) pattern.

### Actions

1. **Action 3.3.1:** Define progress event and subscriber interfaces.
   - **Preconditions:** Orchestrator class is implemented.
   - **Details:**  
     - Create a `ProgressEvent` data class (fields: dependency, status, percent, message, etc.).
     - Define a `ProgressSubscriber` interface with an `update(event)` method.
   - **Context**:
     - Files:  
       - `hatch/installers/progress_events.py` (or similar)
     - Symbols:  
       - `ProgressEvent`  
       - `ProgressSubscriber`
   - **Postconditions:** Progress event and subscriber interfaces are available.
   - **Validation:**
     - **Development tests:** Unit tests for event and subscriber classes.

2. **Action 3.3.2:** Integrate observer pattern into the orchestrator.
   - **Preconditions:** Interfaces are defined.
   - **Details:**  
     - Orchestrator maintains a list of subscribers.
     - At each install step (start, progress, complete, error), orchestrator publishes a `ProgressEvent` to all subscribers.
   - **Context**:
     - Files:  
       - `hatch/installers/dependency_installation_orchestrator.py`  
       - `hatch/installers/progress_events.py`
     - Symbols:  
       - `DependencyInstallerOrchestrator.subscribe`  
       - `DependencyInstallerOrchestrator.notify`
   - **Postconditions:** Orchestrator notifies subscribers of progress in real time.
   - **Validation:**
     - **Development tests:** Simulate installs and verify progress events are sent.
     - **Verification method:** Mock subscribers receive correct updates.

3. **Action 3.3.3:** Implement a CLI/GUI subscriber for user feedback.
   - **Preconditions:** Observer pattern is integrated.
   - **Details:**  
     - Implement a subscriber that displays progress (percentage, current dependency, status) in the CLI or GUI.
     - Ensure the subscriber can be easily replaced or extended for different UIs.
   - **Context**:
     - Files:  
       - `hatch/cli/progress_subscriber.py` (or similar)
     - Symbols:  
       - `CLIProgressSubscriber` (example)
   - **Postconditions:** Users receive real-time feedback during installation.
   - **Validation:**
     - **Development tests:** Manual and automated tests for progress display.

### Phase Completion Criteria
- Observer pattern is fully integrated.
- Real-time progress updates are available to UI/CLI.
- Progress reporting is extensible and robust.

---

## Phase 3.4: Final Integration and Regression Testing

**Goal:**  
Ensure all new and refactored components work together seamlessly and maintain backward compatibility.

### Actions

1. **Action 3.4.1:** Integrate all components and update documentation.
   - **Preconditions:** All previous actions are complete.
   - **Details:**  
     - Ensure all APIs, orchestrator, installers, and progress reporting are integrated.
     - Update developer and user documentation to reflect new architecture.
   - **Context**:
     - Files:  
       - All files modified or created in previous actions
       - `README.md`, developer docs
     - Symbols:  
       - All public APIs and classes
   - **Postconditions:** Documentation is up to date.
   - **Validation:**
     - **Verification method:** Peer review of documentation.

2. **Action 3.4.2:** Run full regression and integration test suite.
   - **Preconditions:** All code is integrated.
   - **Details:**  
     - Run all existing and new tests (unit, integration, regression).
     - Address any failures or regressions.
   - **Context**:
     - Files:  
       - `tests/` (all relevant test files)
     - Symbols:  
       - All test cases and test runners
   - **Postconditions:** All tests pass.
   - **Validation:**
     - **Development tests:** Full test suite.

### Phase Completion Criteria
- All components are integrated and documented.
- All tests pass, ensuring stability and backward compatibility.