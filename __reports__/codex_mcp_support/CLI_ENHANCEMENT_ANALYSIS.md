# Codex MCP CLI Enhancement - Analysis & Recommendation Report

**Date**: December 15, 2025
**Author**: Augment Agent
**Status**: Analysis Complete - Ready for Implementation

---

## Executive Summary

**Recommendation**: Add 6 new CLI arguments and reuse 4 existing arguments to support all 10 Codex-specific configuration fields.

**Rationale**: This approach follows the existing codebase pattern of shared arguments across hosts, provides clear semantics, requires simple implementation, and introduces no breaking changes.

**Implementation Complexity**: LOW (~100-150 lines of code)
**Risk Level**: VERY LOW (purely additive changes)

---

## 1. Existing CLI Architecture Analysis

### 1.1 Current Structure

**Main Command**: `hatch mcp configure`

**Argument Flow**:
1. Arguments parsed by argparse in `setup_mcp_configure_parser()`
2. Passed to `handle_mcp_configure()` handler
3. Mapped to `omni_config_data` dictionary
4. Used to create `MCPServerConfigOmni` instance
5. Converted to host-specific model via `from_omni()`

**Location**: `hatch/cli_hatch.py` (lines 1571-1654 for parser, 783-850 for handler)

### 1.2 Existing CLI Arguments by Category

**Universal Arguments** (all hosts):
- `--command` → command (str)
- `--url` → url (str)
- `--args` → args (List[str], action="append")
- `--env-var` → env (Dict[str, str], KEY=VALUE format)
- `--header` → headers (Dict[str, str], KEY=VALUE format)

**Gemini-Specific Arguments**:
- `--timeout` → timeout (int, milliseconds)
- `--trust` → trust (bool)
- `--cwd` → cwd (str)
- `--http-url` → httpUrl (str)
- `--include-tools` → includeTools (List[str])
- `--exclude-tools` → excludeTools (List[str])

**Cursor/VS Code/LM Studio Arguments**:
- `--env-file` → envFile (str)

**VS Code Arguments**:
- `--input` → input (str)

**Kiro Arguments**:
- `--disabled` → disabled (bool)
- `--auto-approve-tools` → autoApprove (List[str])
- `--disable-tools` → disabledTools (List[str])

### 1.3 Argument Patterns

**List Arguments**: Use `action="append"` (e.g., `--args`, `--include-tools`)
**Dict Arguments**: Use `action="append"` with KEY=VALUE parsing (e.g., `--env-var`, `--header`)
**Boolean Flags**: Use `action="store_true"` (e.g., `--trust`, `--disabled`)
**String/Int Arguments**: Use `type=str` or `type=int` (e.g., `--command`, `--timeout`)

---

## 2. Codex Field Mapping Analysis

### 2.1 Complete Field Inventory

**Codex Fields in MCPServerConfigOmni** (lines 680-689):
1. `env_vars` - List[str] - Environment variable names to whitelist
2. `startup_timeout_sec` - int - Server startup timeout in seconds
3. `tool_timeout_sec` - int - Tool execution timeout in seconds
4. `enabled` - bool - Enable/disable server without deleting
5. `enabled_tools` - List[str] - Tool allow-list
6. `disabled_tools` - List[str] - Tool deny-list
7. `bearer_token_env_var` - str - Env var name for bearer token
8. `http_headers` - Dict[str, str] - Static HTTP headers
9. `env_http_headers` - Dict[str, str] - Headers from env vars
10. `cwd` - str - Working directory (already in Omni as Gemini field)

### 2.2 Field-to-Argument Mapping Table

| # | Codex Field | Type | Existing CLI Arg | New CLI Arg | Decision | Rationale |
|---|-------------|------|------------------|-------------|----------|-----------|
| 1 | cwd | str | --cwd | - | **REUSE** | Already exists for Gemini, exact same semantics |
| 2 | env_vars | List[str] | - | --env-vars | **NEW** | Different from --env-var (names vs values) |
| 3 | startup_timeout_sec | int | - | --startup-timeout | **NEW** | Different from --timeout (purpose & units) |
| 4 | tool_timeout_sec | int | - | --tool-timeout | **NEW** | No existing equivalent |
| 5 | enabled | bool | - | --enabled | **NEW** | Inverse of --disabled (different host) |
| 6 | enabled_tools | List[str] | --include-tools | - | **REUSE** | Exact same semantics as Gemini |
| 7 | disabled_tools | List[str] | --exclude-tools | - | **REUSE** | Exact same semantics as Gemini |
| 8 | bearer_token_env_var | str | - | --bearer-token-env-var | **NEW** | No existing equivalent |
| 9 | http_headers | Dict[str,str] | --header | - | **REUSE** | Exact same semantics (universal) |
| 10 | env_http_headers | Dict[str,str] | - | --env-header | **NEW** | Different from --header (env vars) |

**Summary**: 4 reused, 6 new arguments




---

## 3. Semantic Analysis Details

### 3.1 Fields Requiring New Arguments

**1. env_vars (NEW: --env-vars)**
- **Codex semantics**: List of environment variable NAMES to whitelist/forward
- **Existing --env-var**: Sets KEY=VALUE pairs (Dict[str, str])
- **Why different**: env_vars whitelists which vars to forward, env-var sets values
- **Example**: `--env-vars PATH --env-vars HOME` (forward PATH and HOME from parent env)

**2. startup_timeout_sec (NEW: --startup-timeout)**
- **Codex semantics**: Timeout in seconds for server startup (default: 10)
- **Existing --timeout**: Gemini request timeout in milliseconds
- **Why different**: Different purpose (startup vs request) and units (seconds vs milliseconds)
- **Example**: `--startup-timeout 15` (wait 15 seconds for server to start)

**3. tool_timeout_sec (NEW: --tool-timeout)**
- **Codex semantics**: Timeout in seconds for tool execution (default: 60)
- **No existing equivalent**
- **Example**: `--tool-timeout 120` (allow 2 minutes for tool execution)

**4. enabled (NEW: --enabled)**
- **Codex semantics**: Boolean to enable/disable server without deleting config
- **Existing --disabled**: Kiro-specific disable flag
- **Why different**: Different hosts, inverse semantics (enabled vs disabled)
- **Example**: `--enabled` (enable the server)

**5. bearer_token_env_var (NEW: --bearer-token-env-var)**
- **Codex semantics**: Name of env var containing bearer token for Authorization header
- **No existing equivalent**
- **Example**: `--bearer-token-env-var FIGMA_OAUTH_TOKEN`

**6. env_http_headers (NEW: --env-header)**
- **Codex semantics**: Map of header names to env var names (values pulled from env)
- **Existing --header**: Sets static header values
- **Why different**: env-header pulls values from environment, header uses static values
- **Example**: `--env-header X-API-Key=API_KEY_VAR` (header value from $API_KEY_VAR)

### 3.2 Fields Reusing Existing Arguments

**1. cwd (REUSE: --cwd)**
- **Shared by**: Gemini, Codex
- **Semantics**: Working directory to launch server from
- **Already supported**: Yes (line 1614 in cli_hatch.py)

**2. enabled_tools (REUSE: --include-tools)**
- **Shared by**: Gemini (includeTools), Codex (enabled_tools)
- **Semantics**: Allow-list of tools to expose from server
- **Already supported**: Yes (line 1618 in cli_hatch.py)

**3. disabled_tools (REUSE: --exclude-tools)**
- **Shared by**: Gemini (excludeTools), Codex (disabled_tools)
- **Semantics**: Deny-list of tools to hide
- **Already supported**: Yes (line 1622 in cli_hatch.py)

**4. http_headers (REUSE: --header)**
- **Shared by**: All hosts (universal)
- **Semantics**: Static HTTP headers
- **Already supported**: Yes (line 1590 in cli_hatch.py)

---

## 4. Alias Feasibility Assessment

### 4.1 Argparse Alias Capabilities

**Native Support**: argparse does NOT support argument aliases natively

**Available Options**:
1. Multiple flags for same dest: `parser.add_argument('-v', '--verbose', dest='verbose')`
2. Post-processing: Check multiple args and merge
3. Custom action classes: Complex, not worth it

### 4.2 Current Codebase Pattern

**Pattern Used**: Shared arguments across hosts
- Same CLI argument name used by multiple hosts
- Example: `--include-tools` used by both Gemini and Codex
- Mapping happens in omni_config_data dictionary
- Host-specific models extract relevant fields via `from_omni()`

**Why This Works**:
- MCPServerConfigOmni contains ALL fields from ALL hosts
- Each host's `from_omni()` extracts only supported fields
- CLI doesn't need to know which host uses which field
- Simple, clean, maintainable

### 4.3 Conclusion

**No aliases needed**. The existing shared argument pattern is simpler and more maintainable.

---

## 5. Trade-off Analysis

### 5.1 Chosen Approach: 6 New + 4 Reused Arguments

**Benefits**:
1. ✅ Clear semantics - each argument name matches its purpose
2. ✅ Follows existing pattern - shared args across hosts
3. ✅ Simple implementation - just add new arguments to parser
4. ✅ No breaking changes - existing args continue to work
5. ✅ Type safety - argparse handles validation
6. ✅ Easy to document - clear help text for each arg
7. ✅ Maintainable - no complex logic or workarounds

**Costs**:
1. ⚠️ More total CLI options (6 new args)
2. ⚠️ Slightly longer help text
3. ⚠️ Users need to learn new args for Codex features

**Risk Assessment**: **VERY LOW**
- Purely additive changes
- No modifications to existing argument behavior
- No complex logic or edge cases
- Follows established patterns

### 5.2 Alternative Considered: Argparse Aliases

**Why Rejected**:
- Not supported natively by argparse
- Would require custom implementation
- More complex to maintain
- No clear benefit over shared arguments
- Doesn't fit existing codebase pattern


---

## 6. Edge Cases & Risks

### 6.1 Identified Edge Cases

**1. env_vars vs env-var Confusion**
- **Risk**: Users might confuse `--env-vars` (names) with `--env-var` (values)
- **Mitigation**: Very clear help text explaining the difference
- **Example help text**:
  - `--env-var`: "Set environment variable (KEY=VALUE format)"
  - `--env-vars`: "Whitelist environment variable names to forward (Codex only)"

**2. Timeout Field Confusion**
- **Risk**: Users might use wrong timeout for wrong host
- **Mitigation**: Help text specifies which host uses which timeout
- **Example help text**:
  - `--timeout`: "Request timeout in milliseconds (Gemini only)"
  - `--startup-timeout`: "Server startup timeout in seconds (Codex only)"
  - `--tool-timeout`: "Tool execution timeout in seconds (Codex only)"

**3. http_headers vs env_http_headers**
- **Risk**: Users might confuse when to use which
- **Mitigation**: Clear help text explaining the difference
- **Example help text**:
  - `--header`: "Static HTTP header (KEY=VALUE format)"
  - `--env-header`: "HTTP header from env var (KEY=ENV_VAR_NAME, Codex only)"

**4. enabled vs disabled**
- **Risk**: Confusion about which to use
- **Mitigation**: Help text clarifies which host uses which
- **Example help text**:
  - `--enabled`: "Enable server (Codex only)"
  - `--disabled`: "Disable server (Kiro only)"

### 6.2 Backward Compatibility

**Impact**: NONE - All changes are purely additive
- ✅ All existing arguments continue to work
- ✅ No changes to existing argument behavior
- ✅ New arguments are optional
- ✅ Existing hosts (Claude, Cursor, Kiro, Gemini) unaffected

### 6.3 Missing Field Investigation

**Question**: Is `cwd` missing from MCPServerConfigOmni?

**Answer**: NO - `cwd` already exists in Omni (line 654) as a Gemini-specific field
- Gemini uses it: ✅
- Codex uses it: ✅
- Already in CLI: ✅ (--cwd, line 1614)
- No changes needed: ✅

---

## 7. Final Recommendation

### 7.1 Implementation Plan

**Add 6 New CLI Arguments**:
1. `--env-vars` - List of env var names (action="append")
2. `--startup-timeout` - Startup timeout in seconds (type=int)
3. `--tool-timeout` - Tool execution timeout in seconds (type=int)
4. `--enabled` - Enable server flag (action="store_true")
5. `--bearer-token-env-var` - Bearer token env var name (type=str)
6. `--env-header` - Header from env var (action="append", KEY=ENV_VAR format)

**Reuse 4 Existing Arguments**:
1. `--cwd` - Working directory (already exists)
2. `--include-tools` - Tool allow-list (already exists)
3. `--exclude-tools` - Tool deny-list (already exists)
4. `--header` - Static headers (already exists)

### 7.2 Implementation Checklist

**Code Changes**:
- [ ] Add 6 argument definitions to `setup_mcp_configure_parser()` (~30 lines)
- [ ] Add 6 mappings to `omni_config_data` in `handle_mcp_configure()` (~6 lines)
- [ ] Update help text for clarity (~6 lines)

**Testing**:
- [ ] Add CLI tests for each new argument (~50-100 lines)
- [ ] Test argument parsing and mapping
- [ ] Test integration with Codex strategy
- [ ] Verify existing hosts unaffected

**Documentation**:
- [ ] Update CLI help text
- [ ] Update user documentation (if exists)

**Estimated Effort**: 2-3 hours
**Estimated LOC**: ~100-150 lines

### 7.3 Success Criteria

1. ✅ All 10 Codex fields configurable via CLI
2. ✅ No breaking changes to existing functionality
3. ✅ Clear, user-friendly help text
4. ✅ All tests pass
5. ✅ Consistent with existing CLI patterns

---

## 8. Conclusion

The analysis supports a straightforward implementation: **add 6 new CLI arguments and reuse 4 existing arguments**. This approach:

- Follows existing codebase patterns
- Provides clear semantics
- Requires simple implementation
- Introduces no breaking changes
- Maintains type safety
- Is easy to document and maintain

**Status**: ✅ Analysis Complete - Ready to proceed with implementation (Task 2)

---

## Appendix A: Argument Naming Conventions

| Pattern | Example | Usage |
|---------|---------|-------|
| Kebab-case | --env-var | Standard for multi-word args |
| Action append | --args | For list arguments |
| KEY=VALUE | --env-var KEY=VALUE | For dict arguments |
| store_true | --enabled | For boolean flags |
| Type hints | type=int | For typed arguments |

## Appendix B: References

- CLI Parser: `hatch/cli_hatch.py` lines 1571-1654
- CLI Handler: `hatch/cli_hatch.py` lines 783-850
- Omni Model: `hatch/mcp_host_config/models.py` lines 632-700
- Codex Model: `hatch/mcp_host_config/models.py` lines 567-630
