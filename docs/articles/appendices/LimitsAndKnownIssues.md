# Limits and Known Issues

This appendix documents current limitations and known issues in Hatch v0.8.1, organized by impact severity and architectural domain.

## Critical Limitations (High Impact)

### System Package Version Constraint Simplification

**Issue**: Complex version constraints for system packages are reduced to "install latest" with only warning messages.

**Code Location**: `hatch/installers/system_installer.py:366-403` (`_build_apt_command`)

**Symptoms**:

- Version constraint `>=1.2.0` becomes "install latest"
- No validation that installed version satisfies original constraint
- Silent constraint violations in production environments

**Workaround**: Use exact version constraints (`==1.2.0`) for critical system dependencies

**Root Cause**: Simplified apt command building that only handles exact version matching.

### Concurrent Access Race Conditions

**Issue**: Plain file I/O operations without atomic writes or file locking can lead to corrupted state.

**Code Locations**:

- `hatch/environment_manager.py:172-179` (`_save_environments`)
- `hatch/environment_manager.py:220` (`set_current_environment`, `current_env` file write)
- `hatch/package_loader.py:139-145` (cache write in `download_package`)

**Symptoms**:

- Corrupted `environments.json` when multiple Hatch instances run
- Package cache corruption during concurrent downloads
- Lost environment configuration in multi-user scenarios

**Workaround**: Avoid running multiple Hatch operations simultaneously

**Root Cause**: Non-atomic file operations for critical state files.

## Significant Limitations (Medium Impact)

### Registry Fetch Fragility

**Issue**: Registry fetching has no retry logic for transient network failures.

**Code Location**: `hatch/registry_retriever.py:200-231` (`_fetch_remote_registry`)

**Symptoms**:

- A single transient network error causes the fetch to fail immediately with no retry
- Poor error messages during network connectivity issues
- Development workflow disruption during registry unavailability

**Workaround**: Use local packages (`hatch package add ./local-package`) when registry is unavailable

**Root Cause**: Network requests are single-attempt with no retry strategy or back-off logic.

### Package Integrity Verification Gap

**Issue**: Downloaded packages are not cryptographically verified for integrity.

**Code Location**: `hatch/package_loader.py:56-157` (`download_package`)

**Symptoms**:

- No detection of package tampering in hostile networks
- Corrupted downloads may be interpreted as valid packages
- No audit trail for package provenance

**Workaround**: Manually verify package sources and use trusted networks

**Root Cause**: Missing checksum validation and signature verification during package download.

### Cross-Platform Python Environment Detection

**Issue**: Hard-coded path assumptions limit Python environment detection for non-standard conda/mamba installations.

**Code Location**: `hatch/python_environment_manager.py:65-125` (`_detect_manager`)

**Symptoms**:

- Inconsistent behavior with custom conda/mamba installation locations
- Silent feature degradation when conda/mamba is not in a standard path
- User confusion about Python integration capabilities on non-standard setups

**Workaround**: Set the `CONDA_EXE` or `MAMBA_EXE` environment variable to point to your conda/mamba executable, or ensure it is in your system PATH

**Root Cause**: Hard-coded fallback paths cover only common installation locations (`~/miniconda3`, `~/anaconda3`, `/opt/conda`). `PATH` and `CONDA_EXE`/`MAMBA_EXE` environment variables are checked first but may not cover all installation scenarios.

### Error Recovery and Rollback Gaps

**Issue**: Limited transactional semantics during multi-dependency installation.

**Code Location**: `hatch/installers/dependency_installation_orchestrator.py:605-681` (`_execute_install_plan`)

**Symptoms**:

- Environments left in inconsistent states after failed installs
- Manual cleanup required for partial installation failures
- Difficult recovery from complex dependency conflicts

**Workaround**: Create environment snapshots before major installations; remove and recreate environments if corrupted

**Root Cause**: Sequential installation without comprehensive rollback mechanisms.

## Moderate Limitations (Development Impact)

### Limited Observability and Progress Reporting

**Issue**: Minimal structured logging and progress feedback during operations. Typically intermediate installation steps rely on the individual installer's (i.e. pip, apt, etc.), but orchestrator lacks end-to-end visibility.

**Code Locations**: Logging scattered across multiple modules

**Symptoms**:

- Difficult debugging of installation failures
- Poor user experience during long-running operations
- Limited integration with monitoring systems

**Workaround**: Increase logging verbosity and monitor log files

**Root Cause**: Progress callbacks exist but are sparsely implemented across the codebase.

### Template Generation Assumptions

**Issue**: Templates assume specific MCP server structure and dependencies.

**Code Location**: `hatch/template_generator.py` (particularly `generate_mcp_server_py:33`, `generate_hatch_mcp_server_entry_py:63`, `generate_metadata_json:87`)

**Symptoms**:

- Template lock-in for specific MCP server patterns
- Reduced flexibility for alternative MCP frameworks
- Potential incompatibility with future MCP specifications

**Workaround**: Manually modify generated templates for custom requirements

**Root Cause**: Hard-coded assumptions about entry points and MCP wrapper dependencies.

### Dependency Graph Resolution Edge Cases

**Issue**: Limited handling of circular dependencies and complex version constraints.

**Code Location**: `hatch/installers/dependency_installation_orchestrator.py:337-358` (`_get_install_ready_hatch_dependencies`)

**Symptoms**:

- Potential failures during dependency resolution for circular or deeply nested graphs
- Unclear error messages for complex dependency conflicts
- Unexpected behavior with deeply nested dependency trees

**Workaround**: Simplify dependency structures and avoid circular dependencies

**Root Cause**: Dependency graph resolution is delegated to `hatch_validator.utils.hatch_dependency_graph.HatchDependencyGraphBuilder`; edge case robustness depends on that external library.

## Minor Limitations (Quality of Life)

### Security Context Management

**Issue**: System package installation assumes `sudo` availability without proper validation.

**Code Location**: `hatch/installers/system_installer.py:382-403` (`_build_apt_command`, `install`)

**Symptoms**:

- Poor error messages when privilege escalation fails
- No pre-validation of system package manager availability

**Workaround**: Ensure proper sudo configuration and system package manager access

### Simulation and Dry-Run Gaps

**Issue**: Simulation mode infrastructure exists but is not yet wired through the orchestrator.

**Code Locations**:

- `hatch/installers/dependency_installation_orchestrator.py:635` (`simulation_mode=False`, marked "Future enhancement")
- `hatch/installers/system_installer.py:152` (simulation mode fully implemented at installer level)

**Symptoms**:

- No dry-run capability reachable through normal `hatch package add` flow
- `SystemInstaller` has full `apt-get --dry-run` support ready but not yet exposed
- Limited preview capabilities for complex installation plans

**Workaround**: Test installations in isolated environments first

**Root Cause**: Planned feature not yet implemented. `InstallationContext` supports `simulation_mode` and individual installers handle it, but the orchestrator does not yet accept or pass through a simulation flag.

### Cache Management Strategy

**Issue**: Basic TTL-based caching without intelligent invalidation or size limits.

**Code Locations**:

- `hatch/registry_retriever.py:37` (24-hour TTL constant)
- `hatch/package_loader.py` (presence-only caching, no TTL or size limits)

**Symptoms**:

- Fixed 24-hour TTL for registry data regardless of registry update frequency
- Package cache never expires — only invalidated by `force_download=True`
- No automatic cache cleanup for disk space management
- Force refresh only available at operation level

**Workaround**: Manually clear cache directory when needed:

```bash
rm -rf ~/.hatch/packages/*
```

### Documentation and Schema Evolution

**Issue**: Limited handling of package schema version transitions.

**Code Locations**: Template generation and package validation flows

**Symptoms**:

- Templates generate current schema version only
- No migration tools for package schema updates
- Version compatibility checking incomplete

**Workaround**: Manually update package metadata when schema versions change

## Impact Classification

| Severity | Automation | Reliability | Development |
|----------|------------|-------------|-------------|
| **Critical** | - | Concurrent access, System constraints | - |
| **Significant** | Registry fragility, Error recovery | Package integrity, Python detection | - |
| **Moderate** | - | - | Observability, Templates, Dependency resolution |
| **Minor** | Simulation gaps | Security context, Cache strategy | Schema evolution |

## Recommended Mitigation Strategies

### For Production Use

1. **Avoid concurrent operations** until race conditions are resolved
2. **Use exact version constraints** for system packages when possible
3. **Implement external monitoring** for installation operations
4. **Regularly backup environment configurations**

### For Development

1. **Test in isolated environments** before production deployment
2. **Monitor cache disk usage** and clean manually when needed
3. **Use local packages** when registry is unreliable
4. **Simplify dependency structures** to avoid resolution edge cases

### For Cross-Platform Deployment

1. **Ensure conda/mamba in PATH** on all target systems
2. **Test Python environment detection** on each platform
3. **Validate system package managers** before deployment
4. **Document platform-specific requirements**

## Future Improvements

The Hatch team is aware of these limitations and they are prioritized for future releases:

**Phase 1 (Stability)**: Address concurrent access and error recovery
**Phase 2 (Security)**: Implement package integrity verification and security context validation
**Phase 3 (Robustness)**: Improve cross-platform consistency and system package handling
**Phase 4 (Quality)**: Enhance observability, caching, and template flexibility

For the most current status of these issues, check the project's issue tracker and release notes.
