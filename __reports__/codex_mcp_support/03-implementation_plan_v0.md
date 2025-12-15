# Codex MCP Host Support - Implementation Plan

**Feature**: Codex MCP Host Configuration Support  
**Plan Date**: December 15, 2025  
**Status**: Ready for Implementation  
**Source**: Architecture Report v0 + Test Definition v0

---

## Overview

This plan defines the task-level implementation sequence for adding Codex MCP host support. Tasks are ordered by dependencies to enable efficient execution.

**Estimated Effort**: 10 tasks across 4 logical groups  
**Risk Level**: Low to Medium

---

## Task Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                    GROUP A: Foundation                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Task 1   │    │ Task 2   │    │ Task 3   │                  │
│  │ TOML Dep │    │ Enum     │    │ Backup   │                  │
│  └────┬─────┘    └────┬─────┘    │ Hostname │                  │
│       │               │          └────┬─────┘                  │
└───────┼───────────────┼───────────────┼────────────────────────┘
        │               │               │
        ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GROUP B: Data Models                         │
│       ┌──────────────────────────────────────┐                 │
│       │            Task 4                     │                 │
│       │    MCPServerConfigCodex Model         │                 │
│       └──────────────┬───────────────────────┘                 │
│                      │                                          │
│       ┌──────────────┼──────────────┐                          │
│       ▼              ▼              ▼                          │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐                       │
│  │ Task 5  │   │ Task 6  │   │ Task 7  │                       │
│  │ Omni    │   │Registry │   │ Exports │                       │
│  └────┬────┘   └────┬────┘   └────┬────┘                       │
└───────┼─────────────┼─────────────┼────────────────────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GROUP C: Backup Enhancement                  │
│                 ┌──────────┐                                    │
│                 │ Task 8   │                                    │
│                 │Serializer│                                    │
│                 │ Method   │                                    │
│                 └────┬─────┘                                    │
└──────────────────────┼──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GROUP D: Strategy & Tests                    │
│                 ┌──────────┐                                    │
│                 │ Task 9   │                                    │
│                 │ Codex    │                                    │
│                 │ Strategy │                                    │
│                 └────┬─────┘                                    │
│                      │                                          │
│                      ▼                                          │
│                 ┌──────────┐                                    │
│                 │ Task 10  │                                    │
│                 │  Tests   │                                    │
│                 └──────────┘                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Group A: Foundation (No Dependencies)

These tasks can be executed in parallel as they have no inter-dependencies.

### Task 1: Add TOML Dependency

**Goal**: Add `tomli-w` library for TOML writing capability  
**Pre-conditions**: None  
**File**: `pyproject.toml`

**Context**: Python 3.12+ (our requirement) includes built-in `tomllib` for reading TOML. We only need `tomli-w` for writing.

**Changes**:
```toml
dependencies = [
  # ... existing ...
  "tomli-w>=1.0.0",  # TOML writing (tomllib built-in for reading in Python 3.12+)
]
```

**Success Gates**:
- [ ] `tomli-w` added to dependencies list
- [ ] `pip install -e .` succeeds
- [ ] `import tomli_w` works in Python REPL
- [ ] `import tomllib` works (built-in)

---

### Task 2: Add MCPHostType.CODEX Enum

**Goal**: Register Codex as a supported host type  
**Pre-conditions**: None  
**File**: `hatch/mcp_host_config/models.py`

**Changes**:
```python
class MCPHostType(str, Enum):
    # ... existing ...
    CODEX = "codex"
```

**Success Gates**:
- [ ] `MCPHostType.CODEX` accessible
- [ ] `MCPHostType("codex")` returns `MCPHostType.CODEX`
- [ ] No import errors

---

### Task 3: Update Backup Hostname Validation

**Goal**: Allow 'codex' as valid hostname in backup system  
**Pre-conditions**: None  
**File**: `hatch/mcp_host_config/backup.py`

**Changes**:
```python
# In BackupInfo.validate_hostname()
supported_hosts = {
    'claude-desktop', 'claude-code', 'vscode', 
    'cursor', 'lmstudio', 'gemini', 'kiro', 'codex'  # Add 'codex'
}
```

**Success Gates**:
- [ ] `BackupInfo.validate_hostname('codex')` succeeds
- [ ] Existing hostnames still valid
- [ ] Invalid hostnames still rejected

---

## Group B: Data Models (Depends on Task 2)

### Task 4: Create MCPServerConfigCodex Model

**Goal**: Define Codex-specific configuration model with unique fields  
**Pre-conditions**: Task 2 (enum exists)  
**File**: `hatch/mcp_host_config/models.py`

**Changes**: Add new class after `MCPServerConfigKiro`:
```python
class MCPServerConfigCodex(MCPServerConfigBase):
    """Codex-specific MCP server configuration."""
    
    # Codex-specific fields
    env_vars: Optional[List[str]] = Field(None)
    cwd: Optional[str] = Field(None)
    startup_timeout_sec: Optional[int] = Field(None)
    tool_timeout_sec: Optional[int] = Field(None)
    enabled: Optional[bool] = Field(None)
    enabled_tools: Optional[List[str]] = Field(None)
    disabled_tools: Optional[List[str]] = Field(None)
    bearer_token_env_var: Optional[str] = Field(None)
    http_headers: Optional[Dict[str, str]] = Field(None)
    env_http_headers: Optional[Dict[str, str]] = Field(None)
    
    @classmethod
    def from_omni(cls, omni: 'MCPServerConfigOmni') -> 'MCPServerConfigCodex':
        supported_fields = set(cls.model_fields.keys())
        codex_data = omni.model_dump(include=supported_fields, exclude_unset=True)
        return cls.model_validate(codex_data)
```

**Success Gates**:
- [ ] Model instantiates with Codex-specific fields
- [ ] Inherits base fields (command, args, env, url)
- [ ] `from_omni()` method works correctly

---

### Task 5: Extend MCPServerConfigOmni

**Goal**: Add Codex fields to omni model for CLI integration  
**Pre-conditions**: Task 4 (know which fields to add)  
**File**: `hatch/mcp_host_config/models.py`

**Changes**: Add to `MCPServerConfigOmni` class:
```python
# Codex specific
env_vars: Optional[List[str]] = None
cwd: Optional[str] = None
startup_timeout_sec: Optional[int] = None
tool_timeout_sec: Optional[int] = None
enabled: Optional[bool] = None
enabled_tools: Optional[List[str]] = None
disabled_tools: Optional[List[str]] = None
bearer_token_env_var: Optional[str] = None
http_headers: Optional[Dict[str, str]] = None
env_http_headers: Optional[Dict[str, str]] = None
```

**Success Gates**:
- [ ] Omni model accepts Codex-specific fields
- [ ] Existing fields unaffected
- [ ] No validation errors

---

### Task 6: Update HOST_MODEL_REGISTRY

**Goal**: Register Codex model in host-to-model mapping  
**Pre-conditions**: Task 2 (enum), Task 4 (model)  
**File**: `hatch/mcp_host_config/models.py`

**Changes**:
```python
HOST_MODEL_REGISTRY: Dict[MCPHostType, type[MCPServerConfigBase]] = {
    # ... existing ...
    MCPHostType.CODEX: MCPServerConfigCodex,
}
```

**Success Gates**:
- [ ] `HOST_MODEL_REGISTRY[MCPHostType.CODEX]` returns `MCPServerConfigCodex`
- [ ] Existing mappings unchanged

---

### Task 7: Update Module Exports

**Goal**: Export new model from package  
**Pre-conditions**: Task 4 (model exists)  
**File**: `hatch/mcp_host_config/__init__.py`

**Changes**:
```python
from .models import (
    # ... existing ...
    MCPServerConfigCodex,  # Add this
)

__all__ = [
    # ... existing ...
    'MCPServerConfigCodex',  # Add this
]
```

**Success Gates**:
- [ ] `from hatch.mcp_host_config import MCPServerConfigCodex` works
- [ ] No import errors

---

## Group C: Backup Enhancement (Depends on Group A)

### Task 8: Add atomic_write_with_serializer Method

**Goal**: Enable format-agnostic atomic writes for TOML support  
**Pre-conditions**: Task 3 (backup system accessible)  
**File**: `hatch/mcp_host_config/backup.py`

**Changes**: Add new method to `AtomicFileOperations` class:
```python
from typing import Callable, TextIO, Any

def atomic_write_with_serializer(
    self, 
    file_path: Path, 
    data: Any,
    serializer: Callable[[Any, TextIO], None],
    backup_manager: "MCPHostConfigBackupManager", 
    hostname: str, 
    skip_backup: bool = False
) -> bool:
    """Atomic write with custom serializer."""
    # Backup logic (same as existing)
    backup_result = None
    if file_path.exists() and not skip_backup:
        backup_result = backup_manager.create_backup(file_path, hostname)
        if not backup_result.success:
            raise BackupError(f"Required backup failed: {backup_result.error_message}")
    
    temp_file = None
    try:
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
        with open(temp_file, 'w', encoding='utf-8') as f:
            serializer(data, f)  # Use custom serializer
        
        temp_file.replace(file_path)
        return True
        
    except Exception as e:
        if temp_file and temp_file.exists():
            temp_file.unlink()
        
        if backup_result and backup_result.backup_path:
            try:
                backup_manager.restore_backup(hostname, backup_result.backup_path.name)
            except Exception:
                pass
        
        raise BackupError(f"Atomic write failed: {str(e)}")
```

**Success Gates**:
- [ ] Method accepts custom serializer function
- [ ] Backup creation works with new method
- [ ] Atomic write behavior preserved
- [ ] Existing `atomic_write_with_backup()` unaffected

---

## Group D: Strategy & Tests (Depends on Groups B, C)

### Task 9: Implement CodexHostStrategy

**Goal**: Complete strategy implementation with TOML handling  
**Pre-conditions**: Tasks 1-8 complete  
**File**: `hatch/mcp_host_config/strategies.py`

**Changes**: Add new strategy class:
```python
import tomllib  # Python 3.12+ built-in
import tomli_w

@register_host_strategy(MCPHostType.CODEX)
class CodexHostStrategy(MCPHostStrategy):
    """Configuration strategy for Codex with TOML support."""
    
    def __init__(self):
        self._preserved_features = {}
    
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".codex" / "config.toml"
    
    def get_config_key(self) -> str:
        return "mcp_servers"  # Underscore, not camelCase
    
    def is_host_available(self) -> bool:
        codex_dir = Path.home() / ".codex"
        return codex_dir.exists()
    
    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        return server_config.command is not None or server_config.url is not None
    
    def read_configuration(self) -> HostConfiguration:
        # TOML reading implementation
        ...
    
    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        # TOML writing with backup integration
        ...
```

**Success Gates**:
- [ ] Strategy registered via decorator
- [ ] `MCPHostRegistry.get_strategy(MCPHostType.CODEX)` returns instance
- [ ] TOML read/write operations work
- [ ] `[features]` section preserved
- [ ] Backup integration functional

---

### Task 10: Implement Test Suite

**Goal**: Create comprehensive test coverage per test definition  
**Pre-conditions**: Task 9 (strategy to test)  
**Files**: 
- `tests/regression/test_mcp_codex_host_strategy.py`
- `tests/regression/test_mcp_codex_backup_integration.py`
- `tests/regression/test_mcp_codex_model_validation.py`
- `tests/test_data/codex/*.toml`

**Changes**: Implement 15 tests as defined in `02-test_definition_v0.md`

**Success Gates**:
- [ ] All 15 tests implemented
- [ ] All tests pass with `wobble --category regression`
- [ ] Test data files created
- [ ] No regressions in existing tests

---

### Task 11: Update Documentation

**Goal**: Document Codex support in developer guides  
**Pre-conditions**: Tasks 1-10 complete  
**Files**:
- `docs/articles/devs/architecture/mcp_host_configuration.md`
- `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md`

**Changes**:
1. Add Codex to supported hosts list in architecture doc
2. Add Codex to `MCPHostType` enum documentation
3. Update `BackupInfo.validate_hostname()` supported hosts list
4. Add Codex example to implementation guide (TOML format)
5. Document TOML-specific considerations (nested tables, feature preservation)

**Success Gates**:
- [ ] Architecture doc lists Codex as supported host
- [ ] Implementation guide includes Codex example
- [ ] TOML format differences documented
- [ ] All code examples accurate and tested

---

## Execution Order Summary

| Order | Task | Group | Dependencies | Risk |
|-------|------|-------|--------------|------|
| 1 | Task 1: TOML Dependency | A | None | Low |
| 2 | Task 2: Enum | A | None | Low |
| 3 | Task 3: Backup Hostname | A | None | Low |
| 4 | Task 4: Codex Model | B | Task 2 | Low |
| 5 | Task 5: Omni Extension | B | Task 4 | Low |
| 6 | Task 6: Registry | B | Task 2, 4 | Low |
| 7 | Task 7: Exports | B | Task 4 | Low |
| 8 | Task 8: Serializer Method | C | Task 3 | Medium |
| 9 | Task 9: Strategy | D | Tasks 1-8 | Medium |
| 10 | Task 10: Tests | D | Task 9 | Low |
| 11 | Task 11: Documentation | D | Tasks 1-10 | Low |

---

## Commit Strategy

Following org's git workflow with `[type](codex)` format:

1. **feat(codex): add tomli-w dependency for TOML support** (Task 1)
2. **feat(codex): add MCPHostType.CODEX enum value** (Task 2)
3. **feat(codex): add codex to backup hostname validation** (Task 3)
4. **feat(codex): add MCPServerConfigCodex model** (Tasks 4-7)
5. **feat(codex): add atomic_write_with_serializer method** (Task 8)
6. **feat(codex): implement CodexHostStrategy with TOML support** (Task 9)
7. **tests(codex): add Codex host strategy test suite** (Task 10)
8. **docs(codex): document Codex MCP host support** (Task 11)

---

## Validation Checkpoints

**After Group A**:
- [ ] Dependencies install correctly
- [ ] Enum accessible
- [ ] Backup accepts 'codex' hostname

**After Group B**:
- [ ] Model validates Codex-specific fields
- [ ] Registry lookup works
- [ ] Imports succeed

**After Group C**:
- [ ] Serializer method works with JSON (backward compat)
- [ ] Serializer method works with TOML

**After Group D (Tasks 9-10)**:
- [ ] All 15 tests pass
- [ ] No regressions in existing tests
- [ ] Manual verification with real `~/.codex/config.toml` (if available)

**After Task 11 (Documentation)**:
- [ ] Architecture doc updated with Codex
- [ ] Implementation guide includes Codex example
- [ ] All documentation links valid
- [ ] Code examples match implementation

---

**Plan Version**: v0  
**Status**: Ready for Implementation  
**Next Step**: Execute Task 1 (Add TOML Dependency)