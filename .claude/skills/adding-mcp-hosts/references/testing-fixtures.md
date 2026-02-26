# Testing Fixtures Reference

Register test fixtures for a new MCP host so that all data-driven tests auto-generate.

## 1. canonical_configs.json entry

Add one entry to `tests/test_data/mcp_adapters/canonical_configs.json`.

Schema rules:
- Key is the host name string (e.g., `"newhost"`).
- Use host-native field names (post-mapping). If the host has `FIELD_MAPPINGS` that rename `args` to `arguments`, write `"arguments"` in the fixture.
- Set `null` for unsupported transport fields so the fixture documents their absence.
- Include at least one transport field (`command`, `url`, or `httpUrl`) with a non-null value.

Minimal example (modeled on the `lmstudio` entry, which uses `CLAUDE_FIELDS`):

```json
"newhost": {
  "command": "python",
  "args": ["-m", "mcp_server"],
  "env": {"API_KEY": "test_key"},
  "url": null,
  "headers": null,
  "type": "stdio"
}
```

For hosts with extra fields, add them alongside the universals (see `gemini` or `codex` entries for examples with `httpUrl`, `timeout`, `includeTools`, `cwd`, etc.).

## 2. host_registry.py entries

Make three additions in `tests/test_data/mcp_adapters/host_registry.py`.

**A. `FIELD_SETS` dict** -- map host name string to the `fields.py` constant:

```python
FIELD_SETS: Dict[str, FrozenSet[str]] = {
    # ... existing entries ...
    "newhost": NEWHOST_FIELDS,
}
```

Import `NEWHOST_FIELDS` from `hatch.mcp_host_config.fields` at the top of the file.

**B. `adapter_map` in `HostSpec.get_adapter()`** -- map host name to adapter factory:

```python
adapter_map = {
    # ... existing entries ...
    "newhost": NewHostAdapter,
}
```

Import `NewHostAdapter` from `hatch.mcp_host_config.adapters.newhost` at the top of the file.

**C. Reverse mappings (conditional)** -- only required if the host defines `FIELD_MAPPINGS` in `fields.py`. Add a reverse dict and wire it into `HostSpec.load_config()`. Follow the Codex pattern:

```python
# At module level
NEWHOST_REVERSE_MAPPINGS: Dict[str, str] = {v: k for k, v in NEWHOST_FIELD_MAPPINGS.items()}

# In HostRegistry.__init__, inside the loop
if host_name == "newhost":
    mappings = dict(NEWHOST_FIELD_MAPPINGS)

# In HostSpec.load_config(), extend the reverse lookup
universal_key = CODEX_REVERSE_MAPPINGS.get(key, key)
universal_key = NEWHOST_REVERSE_MAPPINGS.get(universal_key, universal_key)
```

Skip this step entirely if the new host uses standard field names with no mappings.

## 3. What auto-generates

Adding one host (going from 8 to 9 hosts) produces these new test cases without writing any test code:

| Test file | Generator | Current (8 hosts) | New cases added |
|---|---|---|---|
| `test_host_configuration.py` | `ALL_HOSTS` parametrize | 8 | +1 (serialization roundtrip) |
| `test_cross_host_sync.py` | `generate_sync_test_cases` | 64 (8x8) | +17 (9x9 - 8x8 = 17 new pairs) |
| `test_validation_bugs.py` (transport) | `generate_validation_test_cases` | 8 | +1 (transport mutual exclusion) |
| `test_validation_bugs.py` (tool lists) | `generate_validation_test_cases` | 2 (gemini, codex) | +1 if host has tool lists, else +0 |
| `test_field_filtering_v2.py` | `generate_unsupported_field_test_cases` | 211 | +N (one per unsupported field for the new host) |

**Minimum new test cases**: 1 + 17 + 1 + 0 + N = **19 + N** (where N = total_possible_fields - host_supported_fields). With the current 36-field union, a host supporting 6 fields adds 30 filtering tests, totaling **49** new test cases.

## 4. Verification commands

Run from the repository root.

Full MCP test suite:
```
python -m pytest tests/integration/mcp/ tests/unit/mcp/ tests/regression/mcp/ -v
```

Quick smoke (host configuration roundtrip only):
```
python -m pytest tests/integration/mcp/test_host_configuration.py -v
```

Protocol compliance (adapter contract checks):
```
python -m pytest tests/unit/mcp/test_adapter_protocol.py -v
```

Cross-host sync (all pair combinations):
```
python -m pytest tests/integration/mcp/test_cross_host_sync.py -v
```

Field filtering regression:
```
python -m pytest tests/regression/mcp/test_field_filtering_v2.py -v
```

## 5. Expected results

- The new host name appears in parametrized test IDs (e.g., `test_configure_host[newhost]`, `sync_claude-desktop_to_newhost`, `newhost_filters_envFile`).
- All tests pass. Zero failures, zero errors.
- Existing test IDs remain unchanged. No regressions in prior host tests.
- Total test count increases by the amounts in section 3.
