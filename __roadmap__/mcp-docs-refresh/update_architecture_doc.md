# Update Architecture Doc

**Goal**: Bring `docs/articles/devs/architecture/mcp_host_configuration.md` into alignment with the current codebase.
**Pre-conditions**:
- [ ] Branch `task/update-architecture-doc` created from `milestone/mcp-docs-refresh`
**Success Gates**:
- Field support matrix matches all per-host field sets in `hatch/mcp_host_config/fields.py`
- `CODEX_FIELD_MAPPINGS` shows all 4 entries (not 2)
- Strategy layer, `MCPHostStrategy` interface, and `@register_host_strategy` decorator are documented
- `ClaudeAdapter` variant pattern documented
- Testing section documents `HostSpec`, `HostRegistry`, generator functions, assertion functions, and `canonical_configs.json` structure
**References**: [R01 Gap Analysis](../../__reports__/mcp-docs-refresh/docs-vs-codebase-gap-analysis.md) — findings 1a-1d, 2a-2d

---

## Step 1: Update field support matrix and field mapping documentation

**Goal**: Make the field support matrix and field mapping examples match the actual field constants in `fields.py` and the actual mapping dicts in adapter modules.

**Implementation Logic**:

1. Read `hatch/mcp_host_config/fields.py` and extract every per-host field set (`CLAUDE_FIELDS`, `VSCODE_FIELDS`, `CURSOR_FIELDS`, `GEMINI_FIELDS`, `KIRO_FIELDS`, `CODEX_FIELDS`, `LMSTUDIO_FIELDS`).
2. Rebuild the Field Support Matrix table in the architecture doc to include ALL fields present in any host's set. Add an LM Studio column. Add the missing Gemini OAuth fields (`oauth_enabled`, `oauth_clientId`, etc.) and missing Codex fields (`cwd`, `env_vars`, `startup_timeout_sec`, etc.).
3. Read `hatch/mcp_host_config/adapters/codex.py` and extract the actual `CODEX_FIELD_MAPPINGS` dict. Update the "Field Mappings (Optional)" section to show all 4 mappings, not just 2.
4. Update the `MCPServerConfig` model snippet to reflect the actual field set (currently shows `~12` fields with `# ... additional fields per host` — expand to show the full set or at minimum group by host with accurate counts).

**Deliverables**: Updated Field Support Matrix section, updated Field Mappings section, updated model snippet in `docs/articles/devs/architecture/mcp_host_configuration.md`
**Consistency Checks**: Diff the field names in the matrix against `fields.py` constants — every field in every host set must appear in the matrix (expected: PASS)
**Commit**: `docs(mcp): update field support matrix and field mapping documentation`

---

## Step 2: Document missing architectural patterns

**Goal**: Add documentation for the strategy layer interface, the strategy registration decorator, and the Claude adapter variant pattern.

**Implementation Logic**:

1. Read `hatch/mcp_host_config/strategies.py` and extract the `MCPHostStrategy` base class interface (methods: `get_config_path()`, `is_host_available()`, `get_config_key()`, `read_configuration()`, `write_configuration()`, `validate_server_config()`). Also extract the `@register_host_strategy` decorator and explain its role in auto-registration.
2. Add a new subsection under "Key Components" (after BaseAdapter Protocol) titled "MCPHostStrategy Interface" that documents the strategy base class and its methods, analogous to the BaseAdapter Protocol section.
3. Read `hatch/mcp_host_config/adapters/claude.py` and document the variant pattern: a single `ClaudeAdapter` class serving both `claude-desktop` and `claude-code` via a `variant` constructor parameter. Explain this in the "Design Patterns" section.
4. In the BaseAdapter Protocol section, clarify the `validate()` deprecation: state that `validate()` is retained for backward compatibility but `validate_filtered()` is the current contract used by `serialize()`. The extension guide template (Step 2) should implement `validate_filtered()` as the primary validation path.
5. In the Error Handling section, update the example to use `validate_filtered()` instead of `validate()`.

**Deliverables**: New "MCPHostStrategy Interface" subsection, updated "Design Patterns" section, clarified deprecation note in BaseAdapter Protocol, updated Error Handling example in `docs/articles/devs/architecture/mcp_host_configuration.md`
**Consistency Checks**: Verify every method documented in the MCPHostStrategy section exists in `hatch/mcp_host_config/strategies.py` (expected: PASS)
**Commit**: `docs(mcp): document strategy interface, registration decorator, and adapter variant pattern`

---

## Step 3: Rewrite testing infrastructure section

**Goal**: Replace the brief testing section with comprehensive documentation of the data-driven testing architecture.

**Implementation Logic**:

1. Read `tests/test_data/mcp_adapters/host_registry.py`, `assertions.py`, and `canonical_configs.json` to understand the full infrastructure.
2. Rewrite the "Testing Strategy" section to cover:
   - **Three-tier table** (keep, but update test counts to ~285 total auto-generated).
   - **Data-driven infrastructure** subsection: Explain the module at `tests/test_data/mcp_adapters/` with its three files and their roles.
   - **`HostSpec` dataclass**: Document its attributes (`name`, `adapter`, `fields`, `field_mappings`) and key methods (`load_config()`, `get_adapter()`, `compute_expected_fields()`).
   - **`HostRegistry` class**: Document how it derives metadata from `fields.py` at import time and provides `all_hosts()`, `get_host()`, `all_pairs()`, `hosts_supporting_field()`.
   - **Generator functions**: Document `generate_sync_test_cases()`, `generate_validation_test_cases()`, `generate_unsupported_field_test_cases()` and how they feed `pytest.mark.parametrize`.
   - **Assertion functions**: List the 8 `assert_*` functions in `assertions.py` and explain they encode adapter contracts as reusable property checks.
   - **`canonical_configs.json` structure**: Show the JSON schema (host name -> field name -> value) and note the reverse mapping mechanism for Codex.
3. Fix the "zero test code changes" claim. Replace with accurate guidance: adding a new host requires (a) a new entry in `canonical_configs.json`, (b) adding the host's field set to `FIELD_SETS` in `host_registry.py`, and (c) updating `fields.py`. No changes to actual test files are needed — the generators pick up the new host automatically.
4. Acknowledge the two deprecated test files (`test_adapter_serialization.py`, `test_field_filtering.py`) with a note that they are `@pytest.mark.skip` and scheduled for removal in v0.9.0.

**Deliverables**: Rewritten "Testing Strategy" section in `docs/articles/devs/architecture/mcp_host_configuration.md`
**Consistency Checks**: Verify every class/function name referenced in the testing section exists in `tests/test_data/mcp_adapters/` (expected: PASS)
**Commit**: `docs(mcp): rewrite testing section with data-driven infrastructure documentation`
