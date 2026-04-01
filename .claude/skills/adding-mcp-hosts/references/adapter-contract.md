# Adapter Contract Reference

Interface contract for implementing a new MCP host adapter in the Hatch CLI.

## 1. MCPHostType Enum

File: `hatch/mcp_host_config/models.py`. Convention: `UPPER_SNAKE = "kebab-case"`.

```python
class MCPHostType(str, Enum):
    # ... existing members ...
    NEW_HOST = "new-host"
```

The enum value string is the canonical host identifier used everywhere.

## 2. Field Set Declaration

File: `hatch/mcp_host_config/fields.py`. Define a `<HOST>_FIELDS` frozenset.

```python
# Without 'type' support — build from UNIVERSAL_FIELDS
NEW_HOST_FIELDS: FrozenSet[str] = UNIVERSAL_FIELDS | frozenset({"host_specific_field"})

# With 'type' support — build from CLAUDE_FIELDS (which is UNIVERSAL_FIELDS | {"type"})
NEW_HOST_FIELDS: FrozenSet[str] = CLAUDE_FIELDS | frozenset({"host_specific_field"})
```

If the host supports the `type` discriminator, also add its kebab-case name to `TYPE_SUPPORTING_HOSTS`. Hosts without `type` support (Gemini, Kiro, Codex) omit this.

## 3. MCPServerConfig Fields

File: `hatch/mcp_host_config/models.py`. Add new fields to `MCPServerConfig` only when the host introduces fields not already in the model. Every field: `Optional`, default `None`.

```python
disabled: Optional[bool] = Field(None, description="Whether server is disabled")
```

If the host reuses existing fields only (e.g., LMStudio reuses `CLAUDE_FIELDS`), skip this step. The model uses `extra="allow"` but explicit declarations are preferred.

## 4. Adapter Class

File: `hatch/mcp_host_config/adapters/<host>.py`. Extend `BaseAdapter`.

```python
from typing import Any, Dict, FrozenSet
from hatch.mcp_host_config.adapters.base import AdapterValidationError, BaseAdapter
from hatch.mcp_host_config.fields import NEW_HOST_FIELDS
from hatch.mcp_host_config.models import MCPServerConfig

class NewHostAdapter(BaseAdapter):

    @property
    def host_name(self) -> str:
        return "new-host"

    def get_supported_fields(self) -> FrozenSet[str]:
        return NEW_HOST_FIELDS

    def validate(self, config: MCPServerConfig) -> None:
        pass  # DEPRECATED — kept for ABC compliance until v0.9.0

    def validate_filtered(self, filtered: Dict[str, Any]) -> None:
        has_command = "command" in filtered
        has_url = "url" in filtered
        if not has_command and not has_url:
            raise AdapterValidationError(
                "Either 'command' (local) or 'url' (remote) must be specified",
                host_name=self.host_name,
            )
        if has_command and has_url:
            raise AdapterValidationError(
                "Cannot specify both 'command' and 'url' - choose one transport",
                host_name=self.host_name,
            )

    def serialize(self, config: MCPServerConfig) -> Dict[str, Any]:
        filtered = self.filter_fields(config)
        self.validate_filtered(filtered)
        return filtered  # add apply_transformations() call if field mappings exist
```

**validate_filtered() rules:** Transport mutual exclusion (`command` XOR `url` for most hosts; Gemini enforces exactly-one-of-three including `httpUrl`). If host supports `type`, verify consistency (`type='stdio'` requires `command`, etc.).

**serialize() pipeline:** Always `filter_fields` -> `validate_filtered` -> optionally `apply_transformations` -> return.

## 5. Field Mappings

File: `hatch/mcp_host_config/fields.py`. Define only when the host uses different field names. Pattern: `{"universal_name": "host_name"}`. Canonical example:

```python
CODEX_FIELD_MAPPINGS: dict[str, str] = {
    "args": "arguments",
    "headers": "http_headers",
    "includeTools": "enabled_tools",
    "excludeTools": "disabled_tools",
}
```

Reference in `apply_transformations()`:

```python
def apply_transformations(self, filtered: Dict[str, Any]) -> Dict[str, Any]:
    result = filtered.copy()
    for universal_name, host_name in NEW_HOST_FIELD_MAPPINGS.items():
        if universal_name in result:
            result[host_name] = result.pop(universal_name)
    return result
```

Skip entirely if the host uses standard field names (most do).

## 6. Variant Pattern

Reuse one adapter class with a `variant` parameter when two host identifiers share identical fields and validation. Canonical example:

```python
class ClaudeAdapter(BaseAdapter):
    def __init__(self, variant: str = "desktop"):
        if variant not in ("desktop", "code"):
            raise ValueError(f"Invalid Claude variant: {variant}")
        self._variant = variant

    @property
    def host_name(self) -> str:
        return f"claude-{self._variant}"
```

Use when field set, validation, and serialization are identical. If any diverge, create a separate class.

## 7. Wiring and Integration Points

Four files require one-liner additions for every new host.

**`hatch/mcp_host_config/adapters/__init__.py`** -- Add import and `__all__` entry:
```python
from hatch.mcp_host_config.adapters.new_host import NewHostAdapter
# add "NewHostAdapter" to __all__
```

**`hatch/mcp_host_config/adapters/registry.py`** -- Add to `_register_defaults()`:
```python
self.register(NewHostAdapter())  # import at top of file
```

**`hatch/mcp_host_config/backup.py`** -- Add hostname string to `supported_hosts` set in `BackupInfo.validate_hostname()`:
```python
supported_hosts = {
    # ... existing hosts ...
    "new-host",
}
```

**`hatch/mcp_host_config/reporting.py`** -- Add entry to mapping dict in `_get_adapter_host_name()`:
```python
MCPHostType.NEW_HOST: "new-host",
```
