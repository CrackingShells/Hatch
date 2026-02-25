# Write Testing Fixtures

**Goal**: Document the test fixture registration process and verification commands.
**Pre-conditions**:
- [ ] Branch `task/write-testing-fixtures` created from `milestone/adding-mcp-hosts-skill`
**Success Gates**:
- `__design__/skills/adding-mcp-hosts/references/testing-fixtures.md` exists
- Documents fixture schema, registry entries, auto-generation counts, and verification commands
**References**: Codebase `tests/test_data/mcp_adapters/` — canonical_configs.json, host_registry.py, assertions.py

---

## Step 1: Write testing-fixtures.md

**Goal**: Create the reference file documenting how to register test fixtures for a new host.

**Implementation Logic**:
Create `__design__/skills/adding-mcp-hosts/references/testing-fixtures.md` (`mkdir -p` the path first). Derive from inspection of `tests/test_data/mcp_adapters/`. Read the following files:
- `tests/test_data/mcp_adapters/canonical_configs.json` — fixture structure and existing entries
- `tests/test_data/mcp_adapters/host_registry.py` — `HostSpec`, `HostRegistry`, `FIELD_SETS`, generator functions
- `tests/test_data/mcp_adapters/assertions.py` — property-based assertion library
- `tests/integration/mcp/test_host_configuration.py` — how canonical configs drive parametrized tests
- `tests/integration/mcp/test_cross_host_sync.py` — how sync test matrix auto-expands

Structure:

1. **canonical_configs.json entry** — Schema for the fixture. Each host entry:
   - Uses host-native field names (post-mapping if host has FIELD_MAPPINGS)
   - Sets `null` for unsupported fields
   - Must include at least one transport (command/url/httpUrl)
   Show a minimal example entry derived from an existing host.

2. **host_registry.py entries** — Three additions:
   - `FIELD_SETS` dict — maps host name string → `fields.py` field set constant (e.g., `"your-host": YOUR_HOST_FIELDS`)
   - `adapter_map` in `HostSpec.get_adapter()` — maps host name → adapter instance (e.g., `"your-host": YourHostAdapter()`)
   - Reverse mappings (conditional) — only for hosts with `FIELD_MAPPINGS`. Maps host-native names back to canonical names for test verification.

3. **What auto-generates** — Adding fixture data produces ~20+ test cases without writing any test code:
   - 1 host configuration test (serialization roundtrip per host)
   - 16 new cross-host sync tests (8 from-host + 8 to-host pair combinations)
   - Validation property tests (transport mutual exclusion, tool list coexistence if applicable)
   - Field filtering regression tests (one per unsupported field)

4. **Verification commands** — Exact pytest invocations to run after registration:
   - Full suite: `python -m pytest tests/integration/mcp/ tests/unit/mcp/ tests/regression/mcp/ -v`
   - Quick smoke: `python -m pytest tests/integration/mcp/test_host_configuration.py -v`
   - Protocol compliance: `python -m pytest tests/unit/mcp/test_adapter_protocol.py -v`
   - Cross-host sync: `python -m pytest tests/integration/mcp/test_cross_host_sync.py -v`

5. **Expected results** — New host name appears in parametrized test IDs (e.g., `test_configure_host[your-host]`). All tests pass. No regressions in existing host tests.

**Deliverables**: `__design__/skills/adding-mcp-hosts/references/testing-fixtures.md` (~80-120 lines)
**Consistency Checks**: File documents fixture schema, all 3 registry entries, auto-gen counts, 4 pytest commands
**Commit**: `feat(skill): add testing fixtures reference`
