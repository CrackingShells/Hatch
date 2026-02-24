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
    command: Optional[str] = None          # stdio transport
    url: Optional[str] = None              # sse transport
    httpUrl: Optional[str] = None          # http transport (Gemini)

    # Universal fields (all hosts)
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    type: Optional[Literal["stdio", "sse", "http"]] = None

    # VSCode/Cursor fields
    envFile: Optional[str] = None          # Path to environment file
    inputs: Optional[List[Dict]] = None    # Input variable definitions (VSCode only)

    # Gemini fields (16 total including OAuth)
    cwd: Optional[str] = None              # Working directory (Gemini/Codex)
    timeout: Optional[int] = None          # Request timeout in milliseconds
    trust: Optional[bool] = None           # Bypass tool call confirmations
    includeTools: Optional[List[str]] = None   # Tools to include (allowlist)
    excludeTools: Optional[List[str]] = None   # Tools to exclude (blocklist)
    oauth_enabled: Optional[bool] = None       # Enable OAuth for this server
    oauth_clientId: Optional[str] = None       # OAuth client identifier
    oauth_clientSecret: Optional[str] = None   # OAuth client secret
    oauth_authorizationUrl: Optional[str] = None  # OAuth authorization endpoint
    oauth_tokenUrl: Optional[str] = None       # OAuth token endpoint
    oauth_scopes: Optional[List[str]] = None   # Required OAuth scopes
    oauth_redirectUri: Optional[str] = None    # Custom redirect URI
    oauth_tokenParamName: Optional[str] = None # Query parameter name for tokens
    oauth_audiences: Optional[List[str]] = None  # OAuth audiences
    authProviderType: Optional[str] = None     # Authentication provider type

    # Kiro fields
    disabled: Optional[bool] = None        # Whether server is disabled
    autoApprove: Optional[List[str]] = None   # Auto-approved tool names
    disabledTools: Optional[List[str]] = None  # Disabled tool names

    # Codex fields (10 host-specific)
    env_vars: Optional[List[str]] = None       # Environment variables to whitelist/forward
    startup_timeout_sec: Optional[int] = None  # Server startup timeout
    tool_timeout_sec: Optional[int] = None     # Tool execution timeout
    enabled: Optional[bool] = None             # Enable/disable server
    enabled_tools: Optional[List[str]] = None  # Allow-list of tools
    disabled_tools: Optional[List[str]] = None # Deny-list of tools
    bearer_token_env_var: Optional[str] = None # Env var containing bearer token
    http_headers: Optional[Dict[str, str]] = None   # HTTP headers (Codex naming)
    env_http_headers: Optional[Dict[str, str]] = None  # Header names to env var names
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

Field support is defined in `fields.py` as the single source of truth. Every host's field set is built by extending `UNIVERSAL_FIELDS` with host-specific additions:

```python
# Universal fields (supported by ALL hosts) — 5 fields
UNIVERSAL_FIELDS = frozenset({"command", "args", "env", "url", "headers"})

# Hosts that support the 'type' discriminator field
TYPE_SUPPORTING_HOSTS = frozenset({"claude-desktop", "claude-code", "vscode", "cursor"})

# Host-specific field sets — 7 constants, 8 hosts
CLAUDE_FIELDS   = UNIVERSAL_FIELDS | {"type"}                              # 6 fields
VSCODE_FIELDS   = CLAUDE_FIELDS   | {"envFile", "inputs"}                  # 8 fields
CURSOR_FIELDS   = CLAUDE_FIELDS   | {"envFile"}                            # 7 fields
LMSTUDIO_FIELDS = CLAUDE_FIELDS                                            # 6 fields (alias)
GEMINI_FIELDS   = UNIVERSAL_FIELDS | {"httpUrl", "timeout", "trust", "cwd",
                    "includeTools", "excludeTools",
                    "oauth_enabled", "oauth_clientId", "oauth_clientSecret",
                    "oauth_authorizationUrl", "oauth_tokenUrl", "oauth_scopes",
                    "oauth_redirectUri", "oauth_tokenParamName",
                    "oauth_audiences", "authProviderType"}                  # 21 fields
KIRO_FIELDS     = UNIVERSAL_FIELDS | {"disabled", "autoApprove",
                    "disabledTools"}                                        # 8 fields
CODEX_FIELDS    = UNIVERSAL_FIELDS | {"cwd", "env_vars", "startup_timeout_sec",
                    "tool_timeout_sec", "enabled", "enabled_tools",
                    "disabled_tools", "bearer_token_env_var",
                    "http_headers", "env_http_headers"}                     # 15 fields

# Metadata fields (never serialized or reported)
EXCLUDED_ALWAYS = frozenset({"name"})
```

Note that `LMSTUDIO_FIELDS` is a direct alias for `CLAUDE_FIELDS` — LM Studio supports the same field set as Claude Desktop and Claude Code.

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

The matrix below lists every field present in any host's field set (defined in `fields.py`). Claude Desktop, Claude Code, and LM Studio share the same field set (`CLAUDE_FIELDS`), so LM Studio is shown in its own column to make this explicit.

| Field | Claude Desktop/Code | VSCode | Cursor | LM Studio | Gemini | Kiro | Codex |
|-------|:-------------------:|:------:|:------:|:---------:|:------:|:----:|:-----:|
| **Universal fields** | | | | | | | |
| command | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| args | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| env | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| url | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| headers | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Transport discriminator** | | | | | | | |
| type | ✓ | ✓ | ✓ | ✓ | - | - | - |
| **VSCode/Cursor fields** | | | | | | | |
| envFile | - | ✓ | ✓ | - | - | - | - |
| inputs | - | ✓ | - | - | - | - | - |
| **Gemini fields** | | | | | | | |
| httpUrl | - | - | - | - | ✓ | - | - |
| timeout | - | - | - | - | ✓ | - | - |
| trust | - | - | - | - | ✓ | - | - |
| cwd | - | - | - | - | ✓ | - | ✓ |
| includeTools | - | - | - | - | ✓ | - | - |
| excludeTools | - | - | - | - | ✓ | - | - |
| **Gemini OAuth fields** | | | | | | | |
| oauth_enabled | - | - | - | - | ✓ | - | - |
| oauth_clientId | - | - | - | - | ✓ | - | - |
| oauth_clientSecret | - | - | - | - | ✓ | - | - |
| oauth_authorizationUrl | - | - | - | - | ✓ | - | - |
| oauth_tokenUrl | - | - | - | - | ✓ | - | - |
| oauth_scopes | - | - | - | - | ✓ | - | - |
| oauth_redirectUri | - | - | - | - | ✓ | - | - |
| oauth_tokenParamName | - | - | - | - | ✓ | - | - |
| oauth_audiences | - | - | - | - | ✓ | - | - |
| authProviderType | - | - | - | - | ✓ | - | - |
| **Kiro fields** | | | | | | | |
| disabled | - | - | - | - | - | ✓ | - |
| autoApprove | - | - | - | - | - | ✓ | - |
| disabledTools | - | - | - | - | - | ✓ | - |
| **Codex fields** | | | | | | | |
| env_vars | - | - | - | - | - | - | ✓ |
| startup_timeout_sec | - | - | - | - | - | - | ✓ |
| tool_timeout_sec | - | - | - | - | - | - | ✓ |
| enabled | - | - | - | - | - | - | ✓ |
| enabled_tools | - | - | - | - | - | - | ✓ |
| disabled_tools | - | - | - | - | - | - | ✓ |
| bearer_token_env_var | - | - | - | - | - | - | ✓ |
| http_headers | - | - | - | - | - | - | ✓ |
| env_http_headers | - | - | - | - | - | - | ✓ |

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

If your host uses different field names, define a mapping dict in `fields.py`. During serialization, the adapter's `apply_transformations()` method renames fields from the universal schema to the host-native names. Codex is currently the only host that requires this:

```python
CODEX_FIELD_MAPPINGS = {
    "args": "arguments",           # Universal → Codex naming
    "headers": "http_headers",     # Universal → Codex naming
    "includeTools": "enabled_tools",  # Gemini naming → Codex naming (cross-host sync)
    "excludeTools": "disabled_tools", # Gemini naming → Codex naming (cross-host sync)
}
```

The last two entries (`includeTools` -> `enabled_tools`, `excludeTools` -> `disabled_tools`) enable transparent cross-host sync from Gemini to Codex: a Gemini config containing `includeTools` will be serialized as `enabled_tools` in the Codex output.

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
