---
name: adding-mcp-hosts
description: |
  Adds support for a new MCP host platform to the Hatch CLI multi-host
  configuration system. Use when asked to add, integrate, or extend MCP host
  support for a new IDE, editor, or AI coding tool (e.g., Windsurf, Zed,
  Copilot). Follows a 5-step workflow: discover host requirements via web
  research or user questionnaire, add enum and field set declarations, create
  adapter and strategy implementations, wire integration points across 4
  registration files, and register test fixtures that auto-generate 20+ test
  cases without writing test code.
---

## Workflow Checklist

```
- [ ] Step 1: Discover host requirements
- [ ] Step 2: Add enum and field set
- [ ] Step 3: Create adapter and strategy
- [ ] Step 4: Wire integration points
- [ ] Step 5: Register test fixtures
```

---

## Step 1: Discover Host Requirements

Read [references/discovery-guide.md](references/discovery-guide.md) for the full discovery workflow.

Use web search and fetch tools to find the target host's official MCP configuration docs.
Identify: config file path per platform, config format (JSON/JSONC/TOML), top-level key
wrapping server entries, every supported field name and type, and any field name differences
from the universal set (`command`, `args`, `env`, `url`, `headers`).

If web tools are unavailable or return insufficient data, present the structured
questionnaire from the discovery guide to the user.

Produce a Host Spec YAML block capturing: host slug, config paths (macOS/Linux/Windows),
config format, supported fields, field mappings, and strategy family. This output feeds
all subsequent steps.

---

## Step 2: Add Enum and Field Set

Add `MCPHostType` enum value in `hatch/mcp_host_config/models.py`:

```python
class MCPHostType(str, Enum):
    # ... existing members ...
    YOUR_HOST = "your-host"  # lowercase-hyphenated, matching Host Spec slug
```

Add field set constant in `hatch/mcp_host_config/fields.py`:

```python
YOUR_HOST_FIELDS: FrozenSet[str] = UNIVERSAL_FIELDS | frozenset(
    {
        # host-specific fields from Host Spec
    }
)
```

Include `"type"` (via `CLAUDE_FIELDS` base) only if the host uses a transport type
discriminator. If the host uses different field names for universal concepts, add a
mappings dict (see `CODEX_FIELD_MAPPINGS` pattern in `fields.py`).

If the host introduces fields not in `MCPServerConfig`, add them as `Optional` fields
with `Field(None, description="...")` under a new section comment block in `models.py`.

Verify:

```bash
python -c "from hatch.mcp_host_config.models import MCPHostType; print(MCPHostType.YOUR_HOST)"
python -c "from hatch.mcp_host_config.fields import YOUR_HOST_FIELDS; print(YOUR_HOST_FIELDS)"
```

---

## Step 3: Create Adapter and Strategy

Read [references/adapter-contract.md](references/adapter-contract.md) for the `BaseAdapter`
interface, the `validate_filtered()` pipeline, and field mapping details.

Read [references/strategy-contract.md](references/strategy-contract.md) for the
`MCPHostStrategy` interface, `@register_host_strategy` decorator, platform path resolution,
and config serialization.

### Adapter

Create `hatch/mcp_host_config/adapters/your_host.py`. Implement `BaseAdapter` with:

- `host_name` property returning the slug
- `get_supported_fields()` returning the field set from Step 2
- `validate_filtered(filtered)` enforcing host-specific transport rules
- `serialize(config)` calling `filter_fields()` then `validate_filtered()` then returning
  the dict (apply field mappings if needed)

**Variant shortcut:** If the new host is functionally identical to an existing host,
register it as a variant instead of creating a new file. See
`ClaudeAdapter(variant=...)` in `hatch/mcp_host_config/adapters/claude.py`.

### Strategy

Add a strategy class in `hatch/mcp_host_config/strategies.py` decorated with
`@register_host_strategy(MCPHostType.YOUR_HOST)`. Decide the family:

- `ClaudeHostStrategy` -- JSON format with `mcpServers` key
- `CursorBasedHostStrategy` -- `.cursor/mcp.json`-like layout
- `MCPHostStrategy` (direct) -- standalone hosts with unique formats

Implement `get_config_path()`, `get_config_key()`, `validate_server_config()`,
`read_config()`, and `write_config()`.

Verify:

```bash
python -c "from hatch.mcp_host_config.adapters.your_host import YourHostAdapter; print(YourHostAdapter().host_name)"
```

---

## Step 4: Wire Integration Points

Four files need one-liner additions.

**`hatch/mcp_host_config/adapters/__init__.py`** -- Import and add to `__all__`:

```python
from hatch.mcp_host_config.adapters.your_host import YourHostAdapter
# Append "YourHostAdapter" to __all__
```

**`hatch/mcp_host_config/adapters/registry.py`** -- Import adapter, add
`self.register(YourHostAdapter())` inside `_register_defaults()`.

**`hatch/mcp_host_config/backup.py`** -- Add `"your-host"` to the `supported_hosts` set
in `BackupInfo.validate_hostname()`. Also update the `supported_hosts` set in
`EnvironmentPackageEntry.validate_host_names()` in `models.py`.

**`hatch/mcp_host_config/reporting.py`** -- Add `MCPHostType.YOUR_HOST: "your-host"` to
the `mapping` dict in `_get_adapter_host_name()`.

Verify:

```bash
python -c "
from hatch.mcp_host_config.adapters.registry import AdapterRegistry
r = AdapterRegistry()
print('your-host' in r.get_supported_hosts())
"
```

---

## Step 5: Register Test Fixtures

Read [references/testing-fixtures.md](references/testing-fixtures.md) for fixture schemas,
auto-generated test case details, and pytest commands.

Add canonical config entry in `tests/test_data/mcp_adapters/canonical_configs.json`:

```json
"your-host": {
  "command": "python",
  "args": ["-m", "mcp_server"],
  "env": {"API_KEY": "test_key"},
  "url": null,
  "headers": null
}
```

Include all host-specific fields with representative values. Use `null` for unused
transport fields.

Add host registry entries in `tests/test_data/mcp_adapters/host_registry.py`:

1. Import the new field set and adapter.
2. Add `FIELD_SETS` entry: `"your-host": YOUR_HOST_FIELDS`.
3. Add `adapter_map` entry in `HostSpec.get_adapter()`.
4. Add reverse mappings if the host has field name mappings.
5. Add the new field set to `all_possible_fields` in `generate_unsupported_field_test_cases()`.

Verify:

```bash
python -m pytest tests/integration/mcp/ tests/unit/mcp/ tests/regression/mcp/ -v
```

All existing tests must pass. The new host auto-generates test cases for cross-host sync
(N x N matrix), field filtering, transport validation, and property checks.

---

## Cross-References

| Reference | Covers | Read when |
|---|---|---|
| [references/discovery-guide.md](references/discovery-guide.md) | Host research, questionnaire, Host Spec YAML | Step 1 (always) |
| [references/adapter-contract.md](references/adapter-contract.md) | BaseAdapter interface, field sets, registry wiring | Step 3 (always) |
| [references/strategy-contract.md](references/strategy-contract.md) | MCPHostStrategy interface, families, platform paths | Step 3 (always) |
| [references/testing-fixtures.md](references/testing-fixtures.md) | Fixture schema, auto-generated tests, pytest commands | Step 5 (always) |
