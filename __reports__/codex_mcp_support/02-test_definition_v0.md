# Codex MCP Host Support - Test Definition Report

## Overview

This report defines the test suite for Codex MCP host configuration support. Tests follow established patterns from Kiro integration while addressing Codex-specific requirements (TOML format, unique fields).

**Test-to-Code Ratio Analysis**:
- 1 new feature (Codex host support) → Target: 8-12 tests
- 1 backup system enhancement → Target: 2-4 tests
- **Total Target**: 10-16 tests

## Test Categories

| Category | Count | Purpose |
|----------|-------|---------|
| Strategy Tests | 8 | Core `CodexHostStrategy` functionality |
| Backup Integration Tests | 4 | TOML backup/restore operations |
| Model Validation Tests | 3 | `MCPServerConfigCodex` field validation |
| **Total** | **15** | Within target range |

## Test File Structure

```
tests/
├── regression/
│   ├── test_mcp_codex_host_strategy.py    # Strategy tests
│   ├── test_mcp_codex_backup_integration.py # Backup tests
│   └── test_mcp_codex_model_validation.py  # Model tests
└── test_data/
    └── codex/
        ├── valid_config.toml              # Sample valid config
        ├── stdio_server.toml              # STDIO server config
        └── http_server.toml               # HTTP server config
```

---

## Group 1: Strategy Tests

**File**: `tests/regression/test_mcp_codex_host_strategy.py`

### Test 1.1: Config Path Resolution
**Purpose**: Verify Codex configuration path is correctly resolved.

```python
@regression_test
def test_codex_config_path_resolution(self):
    """Test Codex configuration path resolution."""
    # Expected: ~/.codex/config.toml
    # Verify: Path ends with '.codex/config.toml'
    # Verify: File extension is .toml (not .json)
```

**Validates**: `CodexHostStrategy.get_config_path()`

### Test 1.2: Config Key
**Purpose**: Verify Codex uses correct configuration key.

```python
@regression_test
def test_codex_config_key(self):
    """Test Codex configuration key."""
    # Expected: "mcp_servers" (underscore, not camelCase)
    # Verify: Different from other hosts' "mcpServers"
```

**Validates**: `CodexHostStrategy.get_config_key()`

### Test 1.3: Server Config Validation - STDIO
**Purpose**: Verify STDIO server configuration validation.

```python
@regression_test
def test_codex_server_config_validation_stdio(self):
    """Test Codex STDIO server configuration validation."""
    # Input: MCPServerConfig with command="npx", args=["-y", "package"]
    # Expected: validate_server_config() returns True
```

**Validates**: `CodexHostStrategy.validate_server_config()` for local servers

### Test 1.4: Server Config Validation - HTTP
**Purpose**: Verify HTTP server configuration validation.

```python
@regression_test
def test_codex_server_config_validation_http(self):
    """Test Codex HTTP server configuration validation."""
    # Input: MCPServerConfig with url="https://api.example.com/mcp"
    # Expected: validate_server_config() returns True
```

**Validates**: `CodexHostStrategy.validate_server_config()` for remote servers

### Test 1.5: Host Availability Detection
**Purpose**: Verify Codex host detection based on directory existence.

```python
@regression_test
def test_codex_host_availability_detection(self):
    """Test Codex host availability detection."""
    # Mock: ~/.codex directory exists → True
    # Mock: ~/.codex directory doesn't exist → False
```

**Validates**: `CodexHostStrategy.is_host_available()`

### Test 1.6: Read Configuration - Success
**Purpose**: Verify successful TOML configuration reading.

```python
@regression_test
def test_codex_read_configuration_success(self):
    """Test successful Codex TOML configuration reading."""
    # Mock: Valid TOML file with [mcp_servers.context7] section
    # Verify: Returns HostConfiguration with correct servers
    # Verify: Nested [mcp_servers.name.env] parsed correctly
```

**Validates**: `CodexHostStrategy.read_configuration()` with valid TOML

### Test 1.7: Read Configuration - File Not Exists
**Purpose**: Verify graceful handling when config file doesn't exist.

```python
@regression_test
def test_codex_read_configuration_file_not_exists(self):
    """Test Codex configuration reading when file doesn't exist."""
    # Mock: config.toml doesn't exist
    # Expected: Returns empty HostConfiguration (no error)
```

**Validates**: `CodexHostStrategy.read_configuration()` graceful fallback

### Test 1.8: Write Configuration - Preserves Features Section
**Purpose**: Verify [features] section is preserved during write.

```python
@regression_test
def test_codex_write_configuration_preserves_features(self):
    """Test that write_configuration preserves [features] section."""
    # Setup: Existing config with [features].rmcp_client = true
    # Action: Write new server configuration
    # Verify: [features] section preserved in output
    # Verify: New server added to [mcp_servers]
```

**Validates**: `CodexHostStrategy.write_configuration()` preserves non-MCP settings

---

## Group 2: Backup Integration Tests

**File**: `tests/regression/test_mcp_codex_backup_integration.py`

### Test 2.1: Write Creates Backup by Default
**Purpose**: Verify backup is created when writing to existing file.

```python
@regression_test
def test_write_configuration_creates_backup_by_default(self):
    """Test that write_configuration creates backup by default when file exists."""
    # Setup: Existing config.toml with server configuration
    # Action: Write new configuration with no_backup=False
    # Verify: Backup file created in ~/.hatch/mcp_host_config_backups/codex/
    # Verify: Backup contains original TOML content
```

**Validates**: Backup integration in `write_configuration()`

### Test 2.2: Write Skips Backup When Requested
**Purpose**: Verify backup is skipped when no_backup=True.

```python
@regression_test
def test_write_configuration_skips_backup_when_requested(self):
    """Test that write_configuration skips backup when no_backup=True."""
    # Setup: Existing config.toml
    # Action: Write new configuration with no_backup=True
    # Verify: No backup file created
    # Verify: Configuration still written successfully
```

**Validates**: `no_backup` parameter handling

### Test 2.3: No Backup for New File
**Purpose**: Verify no backup created when file doesn't exist.

```python
@regression_test
def test_write_configuration_no_backup_for_new_file(self):
    """Test that no backup is created when writing to a new file."""
    # Setup: config.toml doesn't exist
    # Action: Write configuration with no_backup=False
    # Verify: No backup created (nothing to backup)
    # Verify: New file created successfully
```

**Validates**: Backup logic for new files

### Test 2.4: Codex Hostname Supported in Backup System
**Purpose**: Verify 'codex' is a valid hostname for backup operations.

```python
@regression_test
def test_codex_hostname_supported_in_backup_system(self):
    """Test that 'codex' hostname is supported by the backup system."""
    # Action: Create backup with hostname="codex"
    # Verify: Backup succeeds (no validation error)
    # Verify: Backup filename follows pattern: mcp.json.codex.{timestamp}
```

**Validates**: `BackupInfo.validate_hostname()` includes 'codex'

---

## Group 3: Model Validation Tests

**File**: `tests/regression/test_mcp_codex_model_validation.py`

### Test 3.1: Codex-Specific Fields Accepted
**Purpose**: Verify Codex-specific fields are valid in model.

```python
@regression_test
def test_codex_specific_fields_accepted(self):
    """Test that Codex-specific fields are accepted in MCPServerConfigCodex."""
    # Input: Model with startup_timeout_sec, tool_timeout_sec, enabled_tools
    # Expected: Model validates successfully
    # Verify: All Codex-specific fields accessible
```

**Validates**: `MCPServerConfigCodex` field definitions

### Test 3.2: From Omni Conversion
**Purpose**: Verify conversion from Omni model to Codex model.

```python
@regression_test
def test_codex_from_omni_conversion(self):
    """Test MCPServerConfigCodex.from_omni() conversion."""
    # Input: MCPServerConfigOmni with Codex-specific fields
    # Action: MCPServerConfigCodex.from_omni(omni)
    # Verify: All Codex fields transferred correctly
    # Verify: Non-Codex fields excluded
```

**Validates**: `MCPServerConfigCodex.from_omni()` method

### Test 3.3: HOST_MODEL_REGISTRY Contains Codex
**Purpose**: Verify Codex model is registered in HOST_MODEL_REGISTRY.

```python
@regression_test
def test_host_model_registry_contains_codex(self):
    """Test that HOST_MODEL_REGISTRY contains Codex model."""
    # Verify: MCPHostType.CODEX in HOST_MODEL_REGISTRY
    # Verify: Maps to MCPServerConfigCodex class
```

**Validates**: `HOST_MODEL_REGISTRY` registration

---

## Test Data Requirements

### Sample TOML Files

**`tests/test_data/codex/valid_config.toml`**:
```toml
[features]
rmcp_client = true

[mcp_servers.context7]
command = "npx"
args = ["-y", "@upstash/context7-mcp"]
startup_timeout_sec = 10
tool_timeout_sec = 60
enabled = true

[mcp_servers.context7.env]
MY_VAR = "value"
```

**`tests/test_data/codex/http_server.toml`**:
```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
bearer_token_env_var = "FIGMA_OAUTH_TOKEN"
http_headers = { "X-Figma-Region" = "us-east-1" }
```

---

## Self-Review Checklist Applied

| Test | Implementation Focus | Unique Value | Not Testing Stdlib |
|------|---------------------|--------------|-------------------|
| 1.1 | Path resolution | ✅ Codex-specific path | ✅ |
| 1.2 | Config key | ✅ Underscore vs camelCase | ✅ |
| 1.3 | STDIO validation | ✅ Our validation logic | ✅ |
| 1.4 | HTTP validation | ✅ Our validation logic | ✅ |
| 1.5 | Host detection | ✅ Our detection logic | ✅ |
| 1.6 | TOML read | ✅ Our TOML parsing | ✅ |
| 1.7 | Missing file | ✅ Our error handling | ✅ |
| 1.8 | Features preservation | ✅ Our preservation logic | ✅ |
| 2.1 | Backup creation | ✅ Our backup integration | ✅ |
| 2.2 | Backup skip | ✅ Our no_backup param | ✅ |
| 2.3 | New file backup | ✅ Our backup logic | ✅ |
| 2.4 | Hostname validation | ✅ Our hostname list | ✅ |
| 3.1 | Model fields | ✅ Our field definitions | ✅ |
| 3.2 | Omni conversion | ✅ Our conversion method | ✅ |
| 3.3 | Registry entry | ✅ Our registry config | ✅ |

**All tests pass self-review criteria.**

---

## Tests NOT Included (Rationale)

| Potential Test | Reason Excluded |
|----------------|-----------------|
| TOML parsing correctness | Trust `tomllib` stdlib (Python 3.11+) |
| TOML writing correctness | Trust `tomli-w` library |
| Pydantic field validation | Trust Pydantic framework |
| Path.exists() behavior | Trust Python stdlib |
| JSON serialization | Trust Python stdlib |
| AtomicFileOperations.atomic_copy() | Already tested in existing backup tests |

---

## Success Criteria

1. ✅ All 15 tests pass
2. ✅ No tests duplicate existing coverage
3. ✅ Tests focus on Codex-specific implementation
4. ✅ TOML format handling validated
5. ✅ Backup integration verified
6. ✅ Model registration confirmed

---

**Report Date**: December 15, 2025  
**Test Count**: 15 tests  
**Target Range**: 10-16 tests ✅