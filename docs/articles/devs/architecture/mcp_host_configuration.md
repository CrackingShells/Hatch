# MCP Host Configuration Architecture

This article covers:

- Unified Adapter Architecture for MCP host configuration
- Adapter pattern for host-specific validation and serialization
- Unified data model (`MCPServerConfig`)
- Extension points for adding new host platforms
- Integration with backup and environment systems

## Overview

The MCP host configuration system manages Model Context Protocol server configurations across multiple host platforms (Claude Desktop, VS Code, Cursor, Gemini, Kiro, Codex, LM Studio). It uses the **Unified Adapter Architecture**: a single data model with host-specific adapters for validation and serialization.

> **Adding a new host?** See the [Implementation Guide](../implementation_guides/mcp_host_configuration_extension.md) for step-by-step instructions.

## Core Architecture

### Unified Adapter Pattern

The architecture separates concerns into three layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                               │
│   Creates MCPServerConfig with all user-provided fields         │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Adapter Layer                             │
│   Validates + serializes to host-specific format                │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│   │  Claude  │ │  VSCode  │ │  Gemini  │ │   Kiro   │   ...    │
│   │ Adapter  │ │ Adapter  │ │ Adapter  │ │ Adapter  │          │
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Strategy Layer                             │
│   Handles file I/O (read/write configuration files)             │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits:**

- Single unified data model accepts all fields
- Adapters declaratively define supported fields per host
- No inheritance hierarchies or model conversion methods
- Easy addition of new hosts (3 steps instead of 10)

### Unified Data Model

`MCPServerConfig` contains ALL possible fields from ALL hosts:

```python
class MCPServerConfig(BaseModel):
    """Unified model containing ALL possible fields."""
    model_config = ConfigDict(extra="allow")

    # Hatch metadata (never serialized)
    name: Optional[str] = None

    # Transport fields
    command: Optional[str] = None      # stdio transport
    url: Optional[str] = None          # sse transport
    httpUrl: Optional[str] = None      # http transport (Gemini)

    # Universal fields (all hosts)
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    type: Optional[Literal["stdio", "sse", "http"]] = None

    # Host-specific fields
    envFile: Optional[str] = None      # VSCode/Cursor
    disabled: Optional[bool] = None    # Kiro
    trust: Optional[bool] = None       # Gemini
    # ... additional fields per host
```

**Design principles:**

- `extra="allow"` for forward compatibility with unknown fields
- Adapters handle validation (not the model)
- `name` field is Hatch metadata (defined in `EXCLUDED_ALWAYS`):
  - Never serialized to host configuration files
  - Never reported in CLI field operations
  - Available as payload context within the unified model

## Key Components

### AdapterRegistry

Central registry mapping host names to adapter instances:

```python
from hatch.mcp_host_config.adapters import get_adapter, AdapterRegistry

# Get adapter for a specific host
adapter = get_adapter("claude-desktop")

# Or use registry directly
registry = AdapterRegistry()
adapter = registry.get_adapter("gemini")
supported = registry.get_supported_hosts()  # List all hosts
```

**Supported hosts:**

- `claude-desktop`, `claude-code`
- `vscode`, `cursor`, `lmstudio`
- `gemini`, `kiro`, `codex`

### BaseAdapter Protocol

All adapters implement this interface:

```python
class BaseAdapter(ABC):
    @property
    @abstractmethod
    def host_name(self) -> str:
        """Return host identifier (e.g., 'claude-desktop')."""
        ...

    @abstractmethod
    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields this host accepts."""
        ...

    @abstractmethod
    def validate(self, config: MCPServerConfig) -> None:
        """DEPRECATED (v0.9.0): Use validate_filtered() instead."""
        ...

    @abstractmethod
    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate ONLY fields that survived filtering."""
        ...

    def apply_transformations(self, filtered: Dict[str, Any]) -> Dict[str, Any]:
        """Apply host-specific field name/value transformations (default: no-op)."""
        return filtered

    @abstractmethod
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Convert config to host's expected format."""
        ...
```

**Serialization pattern (validate-after-filter):**

```
filter_fields(config) → validate_filtered(filtered) → apply_transformations(filtered) → return
```

This pattern ensures validation only checks fields the host actually supports,
preventing false rejections during cross-host sync operations.

### Field Constants

Field support is defined in `fields.py`:

```python
# Universal fields (all hosts)
UNIVERSAL_FIELDS = frozenset({"command", "args", "env", "url", "headers"})

# Host-specific field sets
CLAUDE_FIELDS = UNIVERSAL_FIELDS | frozenset({"type"})
VSCODE_FIELDS = CLAUDE_FIELDS | frozenset({"envFile", "inputs"})
GEMINI_FIELDS = UNIVERSAL_FIELDS | frozenset({"httpUrl", "timeout", "trust", ...})
KIRO_FIELDS = UNIVERSAL_FIELDS | frozenset({"disabled", "autoApprove", ...})

# Metadata fields (never serialized or reported)
EXCLUDED_ALWAYS = frozenset({"name"})
```

### Reporting System

The reporting system (`reporting.py`) provides user-friendly feedback for MCP configuration operations. It respects adapter exclusion semantics to ensure consistency between what's reported and what's actually written to host configuration files.

**Key components:**

- `FieldOperation`: Represents a single field-level change (UPDATED, UNCHANGED, or UNSUPPORTED)
- `ConversionReport`: Complete report for a configuration operation
- `generate_conversion_report()`: Analyzes configuration against target host's adapter
- `display_report()`: Displays formatted report to console

**Metadata field handling:**

Fields in `EXCLUDED_ALWAYS` (like `name`) are completely omitted from field operation reports:

```python
# Get excluded fields from adapter
excluded_fields = adapter.get_excluded_fields()

for field_name, new_value in set_fields.items():
    # Skip metadata fields - they should never appear in reports
    if field_name in excluded_fields:
        continue
    # ... process other fields
```

This ensures that:
- Internal metadata fields never appear as UPDATED, UNCHANGED, or UNSUPPORTED
- Server name still appears in the report header for context
- Reporting behavior matches serialization behavior (both use `get_excluded_fields()`)

## Field Support Matrix

| Field | Claude | VSCode | Cursor | Gemini | Kiro | Codex |
|-------|--------|--------|--------|--------|------|-------|
| command, args, env | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| url, headers | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| type | ✓ | ✓ | ✓ | - | - | - |
| envFile | - | ✓ | ✓ | - | - | - |
| inputs | - | ✓ | - | - | - | - |
| httpUrl | - | - | - | ✓ | - | - |
| trust, timeout | - | - | - | ✓ | - | - |
| disabled, autoApprove | - | - | - | - | ✓ | - |
| enabled, enabled_tools | - | - | - | - | - | ✓ |

## Integration Points

### Adapter Integration

Every adapter integrates with the validation and serialization system:

```python
from hatch.mcp_host_config.adapters import get_adapter
from hatch.mcp_host_config import MCPServerConfig

# Create unified config
config = MCPServerConfig(
    name="my-server",
    command="python",
    args=["server.py"],
    env={"DEBUG": "true"},
)

# Serialize for specific host (filter → validate → transform)
adapter = get_adapter("claude-desktop")
data = adapter.serialize(config)
# Result: {"command": "python", "args": ["server.py"], "env": {"DEBUG": "true"}}

# Cross-host sync: serialize for Codex (applies field mappings)
codex = get_adapter("codex")
codex_data = codex.serialize(config)
# Result: {"command": "python", "arguments": ["server.py"], "env": {"DEBUG": "true"}}
# Note: 'args' mapped to 'arguments', 'type' filtered out
```

### Backup System Integration

Strategy classes integrate with the backup system via `MCPHostConfigBackupManager`:

```python
from hatch.mcp_host_config.backup import MCPHostConfigBackupManager, AtomicFileOperations

def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
    backup_manager = MCPHostConfigBackupManager()
    atomic_ops = AtomicFileOperations()
    atomic_ops.atomic_write_with_backup(
        file_path=config_path,
        data=existing_data,
        backup_manager=backup_manager,
        hostname="your-host",
        skip_backup=no_backup
    )
```

### Environment Manager Integration

The system integrates with environment management:

- **Single-server-per-package constraint**: One MCP server per installed package
- **Multi-host configuration**: One server can be configured across multiple hosts
- **Synchronization support**: Environment data can be synced to available hosts

## Extension Points

### Adding New Host Platforms

To add a new host, complete these steps:

| Step | Files to Modify |
|------|-----------------|
| 1. Add host type enum | `models.py` (MCPHostType) |
| 2. Create adapter class | `adapters/your_host.py` + `adapters/__init__.py` |
| 3. Create strategy class | `strategies.py` |
| 4. Add tests | `tests/unit/mcp/`, `tests/integration/mcp/` |

**Minimal adapter implementation:**

```python
from hatch.mcp_host_config.adapters.base import BaseAdapter, AdapterValidationError
from hatch.mcp_host_config.fields import UNIVERSAL_FIELDS

class NewHostAdapter(BaseAdapter):
    @property
    def host_name(self) -> str:
        return "new-host"

    def get_supported_fields(self) -> FrozenSet[str]:
        return UNIVERSAL_FIELDS | frozenset({"your_specific_field"})

    def validate(self, config: MCPServerConfig) -> None:
        """DEPRECATED: Use validate_filtered() instead."""
        pass

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        has_command = "command" in filtered
        has_url = "url" in filtered
        if not has_command and not has_url:
            raise AdapterValidationError("Need command or url")
        if has_command and has_url:
            raise AdapterValidationError("Only one transport allowed")

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        filtered = self.filter_fields(config)
        self.validate_filtered(filtered)
        return filtered
```

See [Implementation Guide](../implementation_guides/mcp_host_configuration_extension.md) for complete instructions.

## Design Patterns

### Declarative Field Support

Each adapter declares its supported fields as a `FrozenSet`:

```python
class YourAdapter(BaseAdapter):
    def get_supported_fields(self) -> FrozenSet[str]:
        return UNIVERSAL_FIELDS | frozenset({"your_field"})
```

The base class provides `filter_fields()` which:
1. Filters to only supported fields
2. Removes excluded fields (`name`)
3. Removes `None` values

### Field Mappings (Optional)

If your host uses different field names:

```python
CODEX_FIELD_MAPPINGS = {
    "args": "arguments",       # Universal → Codex naming
    "headers": "http_headers", # Universal → Codex naming
}
```

### Atomic Operations Pattern

All configuration changes use atomic operations:

1. **Create backup** of current configuration
2. **Perform modification** to configuration file
3. **Verify success** and update state
4. **Clean up** or rollback on failure

## Module Organization

```
hatch/mcp_host_config/
├── __init__.py          # Public API exports
├── models.py            # MCPServerConfig, MCPHostType, HostConfiguration
├── fields.py            # Field constants (UNIVERSAL_FIELDS, EXCLUDED_ALWAYS, etc.)
├── reporting.py         # User feedback reporting system
├── host_management.py   # Registry and configuration manager
├── strategies.py        # Host strategy implementations (I/O)
├── backup.py            # Backup manager and atomic operations
└── adapters/
    ├── __init__.py      # Adapter exports
    ├── base.py          # BaseAdapter abstract class
    ├── registry.py      # AdapterRegistry
    ├── claude.py        # ClaudeAdapter
    ├── vscode.py        # VSCodeAdapter
    ├── cursor.py        # CursorAdapter
    ├── gemini.py        # GeminiAdapter
    ├── kiro.py          # KiroAdapter
    ├── codex.py         # CodexAdapter
    └── lmstudio.py      # LMStudioAdapter
```

## Error Handling

The system uses both exceptions and result objects:

- **Validation errors**: `AdapterValidationError` with field and host context
- **Configuration operations**: `ConfigurationResult` with success status and messages

```python
try:
    adapter.validate(config)
except AdapterValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field: {e.field}, Host: {e.host_name}")
```

## Testing Strategy

The test architecture uses a data-driven approach with property-based assertions:

| Tier | Location | Purpose | Approach |
|------|----------|---------|----------|
| Unit | `tests/unit/mcp/` | Adapter protocol, model validation, registry | Traditional |
| Integration | `tests/integration/mcp/` | Cross-host sync (64 pairs), host config (8 hosts) | Data-driven |
| Regression | `tests/regression/mcp/` | Validation bugs, field filtering (211+ tests) | Data-driven |

**Data-driven infrastructure** (`tests/test_data/mcp_adapters/`):

- `canonical_configs.json`: Canonical config values for all 8 hosts
- `host_registry.py`: HostRegistry derives metadata from fields.py
- `assertions.py`: Property-based assertions verify adapter contracts

Adding a new host requires zero test code changes — only a fixture entry and fields.py update.
