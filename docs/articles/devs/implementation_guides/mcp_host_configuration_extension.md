# Extending MCP Host Configuration

**Quick Start:** Create an adapter (validation + serialization), create a strategy (file I/O), add tests. Most implementations are 50-100 lines per file.

## Before You Start: Integration Checklist

The Unified Adapter Architecture requires only **4 integration points**:

| Integration Point | Required? | Files to Modify |
|-------------------|-----------|-----------------|
| ☐ Host type enum | Always | `models.py` |
| ☐ Adapter class | Always | `adapters/your_host.py`, `adapters/__init__.py` |
| ☐ Strategy class | Always | `strategies.py` |
| ☐ Test fixtures | Always | `tests/test_data/mcp_adapters/canonical_configs.json`, `host_registry.py` |

> **Note:** No host-specific models, no `from_omni()` conversion, no model registry integration. The unified model handles all fields.

## When You Need This

You want Hatch to configure MCP servers on a new host platform:

- A code editor not yet supported (Zed, Neovim, etc.)
- A custom MCP host implementation
- Cloud-based development environments
- Specialized MCP server platforms

## The Pattern: Adapter + Strategy

The Unified Adapter Architecture separates concerns:

| Component | Responsibility | Interface |
|-----------|----------------|-----------|
| **Adapter** | Validation + Serialization | `validate_filtered()`, `serialize()`, `get_supported_fields()` |
| **Strategy** | File I/O | `read_configuration()`, `write_configuration()`, `get_config_path()` |

> **Note:** `validate()` is deprecated (will be removed in v0.9.0). All new adapters should implement `validate_filtered()` for the validate-after-filter pattern. See [Architecture Doc](../architecture/mcp_host_configuration.md#baseadapter-protocol) for details.

```
MCPServerConfig (unified model)
      │
      ▼
┌──────────────┐
│   Adapter    │ ← Validates fields, serializes to host format
└──────────────┘
      │
      ▼
┌──────────────┐
│   Strategy   │ ← Reads/writes configuration files
└──────────────┘
      │
      ▼
   config.json
```

## Implementation Steps

### Step 1: Add Host Type Enum

Add your host to `MCPHostType` in `hatch/mcp_host_config/models.py`:

```python
class MCPHostType(str, Enum):
    # ... existing types ...
    YOUR_HOST = "your-host"  # Use lowercase with hyphens
```

### Step 2: Create Host Adapter

Create `hatch/mcp_host_config/adapters/your_host.py`:

```python
"""Your Host adapter for MCP host configuration."""

from typing import Any, Dict, FrozenSet

from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import UNIVERSAL_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig


class YourHostAdapter(BaseAdapter):
    """Adapter for Your Host."""

    @property
    def host_name(self) -> str:
        return "your-host"

    def get_supported_fields(self) -> FrozenSet[str]:
        """Return fields Your Host accepts."""
        # Start with universal fields, add host-specific ones
        return UNIVERSAL_FIELDS | frozenset({
            "type",  # If your host supports transport type
            # "your_specific_field",
        })

    def validate(self, config: MCPServerConfig) -> None:
        """DEPRECATED: Will be removed in v0.9.0. Use validate_filtered() instead.

        Still required by BaseAdapter's abstract interface. Implement as a
        pass-through until the abstract method is removed.
        """
        pass

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        """Validate ONLY fields that survived filtering.

        This is the primary validation method. It receives a dictionary
        of fields that have already been filtered to only those this host
        supports, with None values and excluded fields removed.
        """
        has_command = "command" in filtered
        has_url = "url" in filtered

        if not has_command and not has_url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) required",
                host_name=self.host_name,
            )

        # Add any host-specific validation
        # if has_command and has_url:
        #     raise AdapterValidationError("Cannot have both", ...)

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Your Host format.

        Follows the validate-after-filter pattern:
        1. Filter to supported fields
        2. Validate filtered fields
        3. Return filtered (or apply transformations if needed)
        """
        filtered = self.filter_fields(config)
        self.validate_filtered(filtered)
        return filtered
```

**Then register in `hatch/mcp_host_config/adapters/__init__.py`:**

```python
from hatch.mcp_host_config.adapters.your_host import YourHostAdapter

__all__ = [
    # ... existing exports ...
    "YourHostAdapter",
]
```

**And add to registry in `hatch/mcp_host_config/adapters/registry.py`:**

```python
from hatch.mcp_host_config.adapters.your_host import YourHostAdapter

def _register_defaults(self) -> None:
    # ... existing registrations ...
    self.register(YourHostAdapter())
```

### Step 3: Create Host Strategy

Add to `hatch/mcp_host_config/strategies.py`:

```python
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(MCPHostStrategy):
    """Strategy for Your Host file I/O."""

    def get_config_path(self) -> Optional[Path]:
        """Return path to config file."""
        return Path.home() / ".your_host" / "config.json"

    def is_host_available(self) -> bool:
        """Check if host is installed."""
        config_path = self.get_config_path()
        return config_path is not None and config_path.parent.exists()

    def get_config_key(self) -> str:
        """Return the key containing MCP servers."""
        return "mcpServers"  # Most hosts use this

    def get_adapter_host_name(self) -> str:
        """Return the adapter host name for registry lookup."""
        return "your-host"

    def validate_server_config(self, server_config: MCPServerConfig) -> bool:
        """Basic transport validation before adapter processing."""
        return server_config.command is not None or server_config.url is not None

    def read_configuration(self) -> HostConfiguration:
        """Read and parse host configuration file."""
        # Implement JSON/TOML parsing for your host's config format
        ...

    def write_configuration(
        self, config: HostConfiguration, no_backup: bool = False
    ) -> bool:
        """Write configuration using adapter serialization."""
        # Use get_adapter(self.get_adapter_host_name()) for serialization
        ...
```

**The `@register_host_strategy` decorator** registers the strategy class in a global dictionary (`MCPHostRegistry._strategies`) keyed by `MCPHostType`. This enables `MCPHostRegistry.get_strategy(host_type)` to look up and instantiate the correct strategy at runtime. The decorator is defined in `host_management.py` as a convenience wrapper around `MCPHostRegistry.register()`.

#### MCPHostStrategy Interface

The base `MCPHostStrategy` class (defined in `host_management.py`) provides the full strategy interface. The table below shows which methods typically need overriding vs which can be inherited from family base classes.

| Method | Must Override | Can Inherit | Notes |
|--------|:------------:|:-----------:|-------|
| `get_config_path()` | Always | -- | Platform-specific path to config file |
| `is_host_available()` | Always | -- | Check if host is installed on system |
| `get_config_key()` | Usually | From family | Most hosts use `"mcpServers"` (default) |
| `get_adapter_host_name()` | Usually | From family | Maps strategy to adapter registry entry |
| `validate_server_config()` | Usually | From family | Basic transport presence check |
| `read_configuration()` | Sometimes | From family | JSON read is identical across families |
| `write_configuration()` | Sometimes | From family | JSON write with adapter serialization |

> **Cross-reference:** See the [Architecture Doc -- MCPHostStrategy](../architecture/mcp_host_configuration.md#key-components) for the full interface specification.

**Inheriting from existing strategy families:**

If your host uses a standard JSON format, inherit from an existing family base class to get `read_configuration()`, `write_configuration()`, and shared validation for free:

```python
# If similar to Claude (standard JSON format with mcpServers key)
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(ClaudeHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".your_host" / "config.json"

    def is_host_available(self) -> bool:
        return self.get_config_path().parent.exists()

# If similar to Cursor (flexible path handling)
@register_host_strategy(MCPHostType.YOUR_HOST)
class YourHostStrategy(CursorBasedHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".your_host" / "config.json"

    def is_host_available(self) -> bool:
        return self.get_config_path().parent.exists()
```

### Step 4: Register Test Fixtures

Hatch uses a **data-driven test infrastructure** that auto-generates parameterized tests for all adapters. Adding a new host requires fixture data updates, but **zero changes to test functions** themselves.

#### a) Add canonical config to `tests/test_data/mcp_adapters/canonical_configs.json`

Add an entry keyed by your host name, using **host-native field names** (i.e., the names your host's config file uses, after any field mappings). Values should represent a valid stdio-transport configuration:

```json
{
  "your-host": {
    "command": "python",
    "args": ["-m", "mcp_server"],
    "env": {"API_KEY": "test_key"},
    "url": null,
    "headers": null,
    "type": "stdio"
  }
}
```

For hosts with field mappings (like Codex, which uses `arguments` instead of `args`), use the host-native names in the fixture:

```json
{
  "codex": {
    "command": "python",
    "arguments": ["-m", "mcp_server"],
    "env": {"API_KEY": "test_key"},
    "url": null,
    "http_headers": null
  }
}
```

#### b) Add field set to `FIELD_SETS` in `tests/test_data/mcp_adapters/host_registry.py`

Map your host name to its field set constant from `fields.py`:

```python
FIELD_SETS: Dict[str, FrozenSet[str]] = {
    # ... existing hosts ...
    "your-host": YOUR_HOST_FIELDS,
}
```

#### c) Add reverse mappings if needed

If your host uses field mappings (like Codex), add the reverse mappings so `HostSpec.load_config()` can convert host-native names back to `MCPServerConfig` field names:

```python
# Already defined for Codex:
CODEX_REVERSE_MAPPINGS: Dict[str, str] = {v: k for k, v in CODEX_FIELD_MAPPINGS.items()}

# Add similar for your host if it has field mappings
```

#### d) Auto-generated test coverage

Once you add the fixture entry and field set mapping, the generator functions in `host_registry.py` will automatically pick up your new host and generate parameterized test cases:

| Generator Function | What It Generates | Coverage |
|--------------------|-------------------|----------|
| `generate_sync_test_cases()` | All cross-host sync pairs (N x N) | Your host syncing to/from every other host |
| `generate_validation_test_cases()` | Transport mutual exclusion, tool list coexistence | Validation contract tests for your host |
| `generate_unsupported_field_test_cases()` | One test per unsupported field | Verifies your adapter filters correctly |

No changes to test files (`test_cross_host_sync.py`, `test_field_filtering.py`, etc.) are needed. The tests consume data from the registry and assertions library.

> **When to add bespoke tests:** Only write custom unit tests if your adapter has unusual behavior not covered by the data-driven infrastructure (e.g., complex field transformations, multi-step validation, variant support like `ClaudeAdapter`'s desktop/code split).

## Declaring Field Support

### Using Field Constants

Import from `hatch/mcp_host_config/fields.py`:

```python
from hatch.mcp_host_config.fields import (
    UNIVERSAL_FIELDS,  # command, args, env, url, headers
    CLAUDE_FIELDS,     # UNIVERSAL + type
    VSCODE_FIELDS,     # CLAUDE + envFile, inputs
    CURSOR_FIELDS,     # CLAUDE + envFile
)

# Compose your host's fields
YOUR_HOST_FIELDS = UNIVERSAL_FIELDS | frozenset({
    "type",
    "your_specific_field",
})
```

### Adding New Host-Specific Fields

If your host has unique fields not in the unified model:

1. **Add to `MCPServerConfig`** in `models.py`:

```python
# Host-specific fields
your_field: Optional[str] = Field(None, description="Your Host specific field")
```

2. **Add to field constants** in `fields.py`:

```python
YOUR_HOST_FIELDS = UNIVERSAL_FIELDS | frozenset({
    "your_field",
})
```

3. **Add CLI argument** (optional) in `hatch/cli/__main__.py`:

```python
mcp_configure_parser.add_argument(
    "--your-field",
    help="Your Host specific field"
)
```

## Field Mappings (Optional)

If your host uses different names for standard fields, override `apply_transformations()`:

```python
# In your adapter
def apply_transformations(self, filtered: Dict[str, Any]) -> Dict[str, Any]:
    """Apply field name mappings after validation."""
    result = filtered.copy()
    if "args" in result:
        result["arguments"] = result.pop("args")
    return result

def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
    filtered = self.filter_fields(config)
    self.validate_filtered(filtered)
    transformed = self.apply_transformations(filtered)
    return transformed
```

Or define mappings centrally in `fields.py`:

```python
YOUR_HOST_FIELD_MAPPINGS = {
    "args": "arguments",
    "headers": "http_headers",
}
```

## Common Patterns

### Multiple Transport Support

Some hosts (like Gemini) support multiple transports:

```python
def validate_filtered(self, filtered: Dict[str, Any]) -> None:
    has_command = "command" in filtered
    has_url = "url" in filtered
    has_http_url = "httpUrl" in filtered

    transport_count = sum([has_command, has_url, has_http_url])

    if transport_count == 0:
        raise AdapterValidationError("At least one transport required")

    # Gemini requires exactly one transport (not multiple)
    if transport_count > 1:
        raise AdapterValidationError(
            "Only one transport allowed: command, url, or httpUrl"
        )
```

### Strict Single Transport

Some hosts (like Claude) require exactly one transport:

```python
def validate_filtered(self, filtered: Dict[str, Any]) -> None:
    has_command = "command" in filtered
    has_url = "url" in filtered

    if not has_command and not has_url:
        raise AdapterValidationError("Need command or url")

    if has_command and has_url:
        raise AdapterValidationError("Cannot have both command and url")
```

### Custom Serialization

Override `serialize()` for custom output format:

```python
def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
    filtered = self.filter_fields(config)
    self.validate_filtered(filtered)

    # Transform to your host's expected structure
    if "command" in filtered:
        filtered["transport"] = {"type": "stdio", "command": filtered.pop("command")}

    return filtered
```

## Testing Your Implementation

### What Is Auto-Generated vs Manual

| Category | Auto-Generated | Manual (if needed) |
|----------|:--------------:|:------------------:|
| **Adapter protocol** (host_name, fields) | Data-driven via `host_registry.py` | -- |
| **Validation contracts** (transport rules) | `generate_validation_test_cases()` | Complex multi-field validation |
| **Field filtering** (unsupported fields dropped) | `generate_unsupported_field_test_cases()` | -- |
| **Cross-host sync** (N x N pairs) | `generate_sync_test_cases()` | -- |
| **Serialization format** | Property-based assertions | Custom output structure |
| **Strategy file I/O** | -- | Always manual (host-specific paths) |

### Fixture Requirements

To integrate with the data-driven test infrastructure, you need:

1. **Fixture entry** in `tests/test_data/mcp_adapters/canonical_configs.json`
2. **Field set mapping** in `tests/test_data/mcp_adapters/host_registry.py` (`FIELD_SETS` dict)
3. **Reverse mappings** in `host_registry.py` (only if your host uses field mappings)

Zero changes to test functions are needed for standard adapter behavior. The test infrastructure derives all expectations from `fields.py` through the `HostSpec` dataclass and property-based assertions in `assertions.py`.

> **Cross-reference:** See the [Architecture Doc -- Testing Strategy](../architecture/mcp_host_configuration.md#testing-strategy) for the full testing infrastructure design, including the three test tiers (unit, integration, regression).

### Test File Location

```
tests/
├── unit/mcp/
│   ├── test_adapter_protocol.py      # Protocol compliance (data-driven)
│   ├── test_adapter_registry.py      # Registry operations
│   └── test_config_model.py          # Unified model validation
├── integration/mcp/
│   ├── test_cross_host_sync.py       # N×N cross-host sync (data-driven)
│   ├── test_host_configuration.py    # Strategy file I/O
│   └── test_adapter_serialization.py # Serialization correctness
├── regression/mcp/
│   ├── test_field_filtering.py       # Unsupported field filtering (data-driven)
│   ├── test_field_filtering_v2.py    # Extended field filtering
│   └── test_validation_bugs.py       # Validation edge cases
└── test_data/mcp_adapters/
    ├── canonical_configs.json         # Fixture: canonical config per host
    ├── host_registry.py               # HostRegistry + test case generators
    └── assertions.py                  # Property-based assertion library
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Adapter not found | Not registered in registry | Add to `_register_defaults()` |
| Field not serialized | Not in `get_supported_fields()` | Add field to set |
| Validation always fails | Logic error in `validate_filtered()` | Check conditions |
| Name appears in output | Not filtering excluded fields | Use `filter_fields()` |

### Debugging Tips

```python
# Print what adapter sees
adapter = get_adapter("your-host")
print(f"Supported fields: {adapter.get_supported_fields()}")

config = MCPServerConfig(name="test", command="python")
print(f"Filtered: {adapter.filter_fields(config)}")
print(f"Serialized: {adapter.serialize(config)}")
```

## Reference: Existing Adapters

Study these for patterns:

| Adapter | Notable Features |
|---------|------------------|
| `ClaudeAdapter` | Variant support (desktop/code), strict transport validation |
| `VSCodeAdapter` | Extended fields (envFile, inputs) |
| `GeminiAdapter` | Multiple transport support, many host-specific fields |
| `KiroAdapter` | Disabled/autoApprove fields |
| `CodexAdapter` | Field mappings (args→arguments) |

## Summary

Adding a new host is now a **4-step process**:

1. **Add enum** to `MCPHostType`
2. **Create adapter** with `validate_filtered()` + `serialize()` + `get_supported_fields()`
3. **Create strategy** with `get_config_path()` + file I/O methods
4. **Register test fixtures** in `canonical_configs.json` and `host_registry.py` (zero test code changes for standard adapters)

The unified model handles all fields. Adapters filter and validate. Strategies handle files. No model conversion needed.
