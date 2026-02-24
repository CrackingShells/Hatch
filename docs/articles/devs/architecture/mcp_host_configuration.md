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

    def filter_fields(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Filter config to only include supported, non-excluded, non-None fields."""
        ...

    def get_excluded_fields(self) -> FrozenSet[str]:
        """Return fields that should always be excluded (default: EXCLUDED_ALWAYS)."""
        ...
```

**Validation migration note:** `validate()` is retained as an abstract method for backward compatibility, but `validate_filtered()` is the current contract used by `serialize()`. All existing adapters implement both methods, but new adapters should implement `validate_filtered()` as the primary validation path. The `validate()` method will be removed in v0.9.0.

**Serialization pattern (validate-after-filter):**

```
filter_fields(config) → validate_filtered(filtered) → apply_transformations(filtered) → return
```

This pattern ensures validation only checks fields the host actually supports,
preventing false rejections during cross-host sync operations.

### MCPHostStrategy Interface

The strategy layer handles file I/O and host detection. All strategy classes inherit from `MCPHostStrategy` (defined in `host_management.py`) and are auto-registered using the `@register_host_strategy` decorator:

```python
class MCPHostStrategy:
    """Abstract base class for host configuration strategies."""

    def get_config_path(self) -> Optional[Path]:
        """Get configuration file path for this host."""
        ...

    def is_host_available(self) -> bool:
        """Check if host is available on system."""
        ...

    def get_config_key(self) -> str:
        """Get the root configuration key for MCP servers (default: 'mcpServers')."""
        ...

    def read_configuration(self) -> HostConfiguration:
        """Read and parse host configuration."""
        ...

    def write_configuration(self, config: HostConfiguration, no_backup: bool = False) -> bool:
        """Write configuration to host file."""
        ...

    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Validate server configuration for this host."""
        ...
```

**Auto-registration with `@register_host_strategy`:**

The `@register_host_strategy` decorator (a convenience wrapper around `MCPHostRegistry.register()`) registers a strategy class at import time. When `strategies.py` is imported, each decorated class is automatically added to the `MCPHostRegistry`, making it available via `MCPHostRegistry.get_strategy(host_type)`:

```python
from hatch.mcp_host_config.host_management import MCPHostStrategy, register_host_strategy
from hatch.mcp_host_config.models import MCPHostType

@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".your-host" / "config.json"

    def is_host_available(self) -> bool:
        return self.get_config_path().parent.exists()

    # ... remaining methods
```

This decorator-based registration follows the same pattern used throughout Hatch. No manual registry wiring is needed — adding the decorator is sufficient.

**Strategy families:**

Some strategies share implementation through base classes:

- `ClaudeHostStrategy`: Base for `ClaudeDesktopStrategy` and `ClaudeCodeStrategy` (shared JSON read/write, `_preserve_claude_settings()`)
- `CursorBasedHostStrategy`: Base for `CursorHostStrategy` and `LMStudioHostStrategy` (shared Cursor-format JSON read/write)

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

### Adapter Variant Pattern

When two hosts share the same field set and validation logic but differ only in identity, a single adapter class can serve both via a `variant` constructor parameter. This avoids code duplication without introducing an inheritance hierarchy.

`ClaudeAdapter` demonstrates this pattern. Claude Desktop and Claude Code share identical field support (`CLAUDE_FIELDS`) and validation rules, so a single class handles both:

```python
class ClaudeAdapter(BaseAdapter):
    def __init__(self, variant: str = "desktop"):
        if variant not in ("desktop", "code"):
            raise ValueError(f"Invalid Claude variant: {variant}")
        self._variant = variant

    @property
    def host_name(self) -> str:
        return f"claude-{self._variant}"  # "claude-desktop" or "claude-code"

    def get_supported_fields(self) -> FrozenSet[str]:
        return CLAUDE_FIELDS  # Same field set for both variants
```

The `AdapterRegistry` registers two entries pointing to different instances of the same class:

```python
ClaudeAdapter(variant="desktop")  # registered as "claude-desktop"
ClaudeAdapter(variant="code")     # registered as "claude-code"
```

Use this pattern when adding a new host that is functionally identical to an existing one but requires a distinct host name in the registry.

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
    filtered = adapter.filter_fields(config)
    adapter.validate_filtered(filtered)
except AdapterValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field: {e.field}, Host: {e.host_name}")
```

In practice, calling `adapter.serialize(config)` is preferred since it executes the full filter-validate-transform pipeline and will raise `AdapterValidationError` on validation failure.

## Testing Strategy

The test architecture uses a data-driven approach with property-based assertions. Approximately 285 test cases are auto-generated from metadata in `fields.py` and fixture data in `canonical_configs.json`.

### Three-Tier Test Structure

| Tier | Location | Purpose | Approach |
|------|----------|---------|----------|
| Unit | `tests/unit/mcp/` | Adapter protocol, model validation, registry | Traditional |
| Integration | `tests/integration/mcp/` | Cross-host sync (64 pairs), host config (8 hosts) | Data-driven |
| Regression | `tests/regression/mcp/` | Validation bugs, field filtering (~285 auto-generated) | Data-driven |

### Data-Driven Infrastructure

The module at `tests/test_data/mcp_adapters/` contains three files that form the data-driven test infrastructure:

| File | Role |
|------|------|
| `canonical_configs.json` | Fixture data: canonical config values for all 8 hosts |
| `host_registry.py` | Registry: derives host metadata from `fields.py`, generates test cases |
| `assertions.py` | Assertions: reusable property checks encoding adapter contracts |

### `HostSpec` Dataclass

`HostSpec` is the per-host test specification. It combines minimal fixture data (config values) with complete metadata derived from `fields.py`:

```python
@dataclass
class HostSpec:
    host_name: str                           # e.g., "claude-desktop", "codex"
    canonical_config: Dict[str, Any]         # Raw config values from fixture (host-native names)
    supported_fields: FrozenSet[str]         # From fields.py (e.g., CLAUDE_FIELDS)
    field_mappings: Dict[str, str]           # From fields.py (e.g., CODEX_FIELD_MAPPINGS)
```

Key methods:

- `load_config()` -- Builds an `MCPServerConfig` from canonical config values, applying reverse field mappings for hosts with non-standard names (e.g., Codex `arguments` -> `args`)
- `get_adapter()` -- Instantiates the correct adapter for this host (handles `ClaudeAdapter` variant dispatch)
- `compute_expected_fields(input_fields)` -- Returns `(input_fields & supported_fields) - EXCLUDED_ALWAYS`, predicting which fields should survive filtering

### `HostRegistry` Class

`HostRegistry` bridges fixture data with `fields.py` metadata. At construction time, it loads `canonical_configs.json` and derives each host's `HostSpec` by looking up the corresponding field set in the `FIELD_SETS` mapping (which maps host names to `fields.py` constants like `CLAUDE_FIELDS`, `GEMINI_FIELDS`, etc.):

```python
registry = HostRegistry(Path("tests/test_data/mcp_adapters/canonical_configs.json"))
```

Methods:

- `all_hosts()` -- Returns all `HostSpec` instances sorted by name
- `get_host(name)` -- Returns a specific `HostSpec` by host name
- `all_pairs()` -- Generates all `(from_host, to_host)` combinations for O(n^2) cross-host sync testing (8 x 8 = 64 pairs)
- `hosts_supporting_field(field_name)` -- Finds hosts that support a specific field (e.g., all hosts supporting `httpUrl`)

### Generator Functions

Three generator functions create parameterized test cases from registry data. These are called at module level and fed directly to `pytest.mark.parametrize`:

- `generate_sync_test_cases(registry)` -- Produces one `SyncTestCase` per (from, to) host pair (64 cases for 8 hosts)
- `generate_validation_test_cases(registry)` -- Produces `ValidationTestCase` entries for transport mutual exclusion (all hosts) and tool list coexistence (hosts with tool list support)
- `generate_unsupported_field_test_cases(registry)` -- For each host, computes the set of fields it does NOT support (from the union of all host field sets) and produces one `FilterTestCase` per unsupported field

### Assertion Functions

The `assertions.py` module contains 7 `assert_*` functions that encode adapter contracts as reusable property checks. Tests call these functions instead of writing inline assertions:

| Function | Contract Verified |
|----------|-------------------|
| `assert_only_supported_fields()` | Result contains only fields from `fields.py` for this host (including mapped names) |
| `assert_excluded_fields_absent()` | `EXCLUDED_ALWAYS` fields (e.g., `name`) are not in result |
| `assert_transport_present()` | At least one transport field (`command`, `url`, `httpUrl`) is present |
| `assert_transport_mutual_exclusion()` | Exactly one transport field is present |
| `assert_field_mappings_applied()` | Universal field names are replaced by host-native names (e.g., no `args` in Codex output) |
| `assert_tool_lists_coexist()` | Both allowlist and denylist fields are present when applicable |
| `assert_unsupported_field_absent()` | A specific unsupported field was filtered out |

### `canonical_configs.json` Structure

The fixture file uses a flat JSON schema mapping host names to field-value pairs:

```json
{
  "claude-desktop": {
    "command": "python",
    "args": ["-m", "mcp_server"],
    "env": {"API_KEY": "test_key"},
    "url": null,
    "headers": null,
    "type": "stdio"
  },
  "codex": {
    "command": "python",
    "arguments": ["-m", "mcp_server"],
    "env": {"API_KEY": "test_key"},
    "url": null,
    "http_headers": null,
    "cwd": "/app",
    "enabled_tools": ["tool1", "tool2"],
    "disabled_tools": ["tool3"]
  }
}
```

Note that Codex entries use host-native field names (e.g., `arguments` instead of `args`, `http_headers` instead of `headers`). The `HostSpec.load_config()` method applies reverse mappings (`CODEX_REVERSE_MAPPINGS`) to convert these back to universal names when constructing `MCPServerConfig` objects.

### Adding a New Host to Tests

Adding a new host does not require changes to any test files. The generators automatically pick up the new host. The required steps are:

1. Add a new entry in `canonical_configs.json` with representative config values using the host's native field names
2. Add the host's field set to the `FIELD_SETS` mapping in `host_registry.py` (mapping the host name to the corresponding constant from `fields.py`)
3. Update `fields.py` with the new host's field set constant

No changes to actual test files (`test_cross_host_sync.py`, `test_host_configuration.py`, etc.) are needed -- the generators pick up the new host automatically via the registry.

### Deprecated Test Files

Two legacy test files are marked with `@pytest.mark.skip` and scheduled for removal in v0.9.0:

- `tests/integration/mcp/test_adapter_serialization.py` -- Replaced by `test_host_configuration.py` (per-host) and `test_cross_host_sync.py` (cross-host)
- `tests/regression/mcp/test_field_filtering.py` -- Replaced by `test_field_filtering_v2.py` (data-driven)

These files remain in the codebase for reference during the migration period but are not executed in CI.
