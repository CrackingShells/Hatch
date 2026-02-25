# Gap Analysis: MCP Host Config Dev Docs vs Codebase

## Problem Statement

The developer documentation for the MCP host configuration system (`mcp_host_configuration.md` and `mcp_host_configuration_extension.md`) has fallen behind the codebase, particularly in the testing infrastructure sections. This creates misleading guidance for contributors adding new host support.

## Evidence

Systematic comparison of the three dev docs against the current codebase state (commit `c544cb3` on `dev`).

### Tested Docs

| Doc | Path |
|:----|:-----|
| Architecture | `docs/articles/devs/architecture/mcp_host_configuration.md` |
| Extension Guide | `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md` |
| Testing Standards | `docs/articles/devs/development_processes/testing_standards.md` |

---

## Findings

### 1. Testing Infrastructure (Severity: High)

The testing section in both docs is significantly behind the actual implementation.

#### 1a. Data-driven infrastructure undocumented

| Component | Location | Lines | Docs Coverage |
|:----------|:---------|------:|:--------------|
| `HostSpec` dataclass | `tests/test_data/mcp_adapters/host_registry.py` | ~95 | Brief mention, no detail |
| `HostRegistry` class (5+ methods) | `tests/test_data/mcp_adapters/host_registry.py` | ~77 | Brief mention, no detail |
| 3 generator functions | `tests/test_data/mcp_adapters/host_registry.py` | ~83 | Not documented |
| 8 assertion functions | `tests/test_data/mcp_adapters/assertions.py` | ~143 | Not documented |
| Canonical fixture data | `tests/test_data/mcp_adapters/canonical_configs.json` | full | Not documented |
| `CODEX_REVERSE_MAPPINGS` | `tests/test_data/mcp_adapters/host_registry.py:61` | ~3 | Not documented |

#### 1b. "Zero test code changes" claim is misleading

The extension guide claims adding a new host requires zero test code changes. In reality it requires:

- Adding an entry to `canonical_configs.json`
- Adding a `HostSpec` entry in `host_registry.py` (lines 226-242 in `FIELD_SETS` dict + `HostRegistry._build_specs()`)

#### 1c. Test count undersold

- Docs say "211+ tests"
- Actual auto-generated count: ~285 (64 sync pairs + 10 validation + 211 field filtering)

#### 1d. Deprecated test files unacknowledged

Two files marked `@pytest.mark.skip` and scheduled for removal in v0.9.0:

- `tests/integration/mcp/test_adapter_serialization.py`
- `tests/regression/mcp/test_field_filtering.py`

Neither mentioned in any documentation.

---

### 2. Architecture Doc Gaps (Severity: Medium-High)

#### 2a. Field support matrix incomplete

Missing from the matrix:

- **Gemini**: ~10 OAuth fields (`oauth_enabled`, `oauth_clientId`, `oauth_clientSecret`, `oauth_scopes`, `oauth_redirectUrl`, `oauth_tokenUrl`, `oauth_authUrl`, `oauth_extraParams`)
- **Codex**: advanced fields (`cwd`, `env_vars`, `startup_timeout_sec`, `bearer_token_env_var`, `http_headers`)

#### 2b. `CODEX_FIELD_MAPPINGS` incomplete

Docs show 2 mappings (`args`->`arguments`, `headers`->`http_headers`).
Actual code has 4 (also `includeTools`->`enabled_tools`, `excludeTools`->`disabled_tools`).

#### 2c. Missing architectural patterns

| Pattern | Status |
|:--------|:-------|
| `@register_host_strategy(MCPHostType.X)` decorator | Not documented |
| `MCPHostStrategy` base class interface | Not documented |
| `ClaudeAdapter` variant parameter (`desktop` vs `code`) | Not documented |

#### 2d. `validate()` deprecation inconsistency

- Architecture doc marks `validate()` as deprecated (v0.9.0)
- Extension guide Step 2 template still uses `validate()`, not `validate_filtered()`
- No migration guidance provided

---

### 3. What Is Accurate

- Module organization matches exactly
- 8 host names/enum values correct
- `UNIVERSAL_FIELDS`, per-host field constants match
- `BaseAdapter` protocol methods match
- Three-layer architecture description accurate
- `EXCLUDED_ALWAYS` pattern correct

---

## Root Cause

The testing infrastructure was overhauled to a data-driven architecture (HostRegistry, generators, property-based assertions) but the documentation was not updated to reflect these changes. The architecture doc and extension guide were written against the pre-overhaul state.

## Impact Assessment

- **Scope**: Architecture doc testing section, extension guide Step 2-4, field support matrix
- **Dependencies**: Any contributor following the extension guide to add a new host will get incomplete guidance on testing requirements
- **Risk**: New host contributions may skip fixture/registry setup, causing CI gaps

## Recommendations

1. Rewrite the architecture doc testing section to document the full data-driven infrastructure
2. Rewrite the extension guide Step 4 with actual testing requirements
3. Fix validate() → validate_filtered() in templates
4. Complete the field support matrix
5. Document missing architectural patterns (strategy decorator, MCPHostStrategy interface, ClaudeAdapter variant)
