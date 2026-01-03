# Extending MCP Host Configuration

**Quick Start:** Create an adapter (validation + serialization), create a strategy (file I/O), add tests. Most implementations are 50-100 lines per file.

## Before You Start: Integration Checklist

The Unified Adapter Architecture requires only **4 integration points**:

| Integration Point | Required? | Files to Modify |
|-------------------|-----------|-----------------|
| ☐ Host type enum | Always | `models.py` |
| ☐ Adapter class | Always | `adapters/your_host.py`, `adapters/__init__.py` |
| ☐ Strategy class | Always | `strategies.py` |
| ☐ Test infrastructure | Always | `tests/unit/mcp/`, `tests/integration/mcp/` |

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
| **Adapter** | Validation + Serialization | `validate()`, `serialize()`, `get_supported_fields()` |
| **Strategy** | File I/O | `read_configuration()`, `write_configuration()`, `get_config_path()` |

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
        """Validate configuration for Your Host."""
        # Check transport requirements
        if not config.command and not config.url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) required",
                host_name=self.host_name
            )
        
        # Add any host-specific validation
        # if config.command and config.url:
        #     raise AdapterValidationError("Cannot have both", ...)
    
    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        """Serialize configuration for Your Host format."""
        self.validate(config)
        return self.filter_fields(config)
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
    
    # read_configuration() and write_configuration() 
    # can inherit from a base class or implement from scratch
```

**Inheriting from existing strategy families:**

```python
# If similar to Claude (standard JSON format)
class YourHostStrategy(ClaudeHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".your_host" / "config.json"

# If similar to Cursor (flexible path handling)
class YourHostStrategy(CursorBasedHostStrategy):
    def get_config_path(self) -> Optional[Path]:
        return Path.home() / ".your_host" / "config.json"
```

### Step 4: Add Tests

**Unit tests** (`tests/unit/mcp/test_your_host_adapter.py`):

```python
class TestYourHostAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = YourHostAdapter()
    
    def test_host_name(self):
        self.assertEqual(self.adapter.host_name, "your-host")
    
    def test_supported_fields(self):
        fields = self.adapter.get_supported_fields()
        self.assertIn("command", fields)
    
    def test_validate_requires_transport(self):
        config = MCPServerConfig(name="test")
        with self.assertRaises(AdapterValidationError):
            self.adapter.validate(config)
    
    def test_serialize_filters_unsupported(self):
        config = MCPServerConfig(name="test", command="python", httpUrl="http://x")
        result = self.adapter.serialize(config)
        self.assertNotIn("httpUrl", result)  # Assuming not supported
```

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

If your host uses different names for standard fields:

```python
# In your adapter
def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
    self.validate(config)
    result = self.filter_fields(config)

    # Apply mappings (e.g., 'args' → 'arguments')
    if "args" in result:
        result["arguments"] = result.pop("args")

    return result
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
def validate(self, config: MCPServerConfig) -> None:
    transports = sum([
        config.command is not None,
        config.url is not None,
        config.httpUrl is not None,
    ])

    if transports == 0:
        raise AdapterValidationError("At least one transport required")

    # Allow multiple transports if your host supports it
```

### Strict Single Transport

Some hosts (like Claude) require exactly one transport:

```python
def validate(self, config: MCPServerConfig) -> None:
    has_command = config.command is not None
    has_url = config.url is not None

    if not has_command and not has_url:
        raise AdapterValidationError("Need command or url")

    if has_command and has_url:
        raise AdapterValidationError("Cannot have both command and url")
```

### Custom Serialization

Override `serialize()` for custom output format:

```python
def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
    self.validate(config)
    result = self.filter_fields(config)

    # Transform to your host's expected structure
    if config.type == "stdio":
        result["transport"] = {"type": "stdio", "command": result.pop("command")}

    return result
```

## Testing Your Implementation

### Test Categories

| Category | What to Test |
|----------|--------------|
| **Protocol** | `host_name`, `get_supported_fields()` return correct values |
| **Validation** | `validate()` accepts valid configs, rejects invalid |
| **Serialization** | `serialize()` produces correct format, filters fields |
| **Integration** | Adapter works with registry, strategy reads/writes files |

### Test File Location

```
tests/
├── unit/mcp/
│   └── test_your_host_adapter.py   # Protocol + validation + serialization
└── integration/mcp/
    └── test_your_host_strategy.py  # File I/O + end-to-end
```

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Adapter not found | Not registered in registry | Add to `_register_defaults()` |
| Field not serialized | Not in `get_supported_fields()` | Add field to set |
| Validation always fails | Logic error in `validate()` | Check conditions |
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
2. **Create adapter** with `validate()` + `serialize()` + `get_supported_fields()`
3. **Create strategy** with `get_config_path()` + file I/O methods
4. **Add tests** for adapter and strategy

The unified model handles all fields. Adapters filter and validate. Strategies handle files. No model conversion needed.

