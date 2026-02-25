# Discovery Guide: Host Requirement Research

Reference for the discovery step when adding a new MCP host to Hatch.
Produces a Host Spec YAML artifact consumed by all subsequent steps.

---

## 1. Tool Priority Ladder

Research the target host in order. Fall through when the current level yields no definitive answer.

### Level 1: Web Search + Fetch

| Action | Detail |
|--------|--------|
| Search query | `"<host-name> MCP server configuration" site:github.com OR site:docs.*` |
| Fetch targets | Official docs page, README, or config schema file |
| Success | Config path, format, root key, and supported fields are all documented |
| Fall through | Docs missing, incomplete, or ambiguous on field support |

### Level 2: Context7 Library Docs

| Action | Detail |
|--------|--------|
| Resolve library | `resolve-library-id` with the host package name |
| Query | `"MCP server configuration format and supported fields"` |
| Success | Field names, types, and validation rules documented |
| Fall through | Host not indexed, or MCP config undocumented |

### Level 3: Codebase Retrieval

| Action | Detail |
|--------|--------|
| Query | `"configuration strategy for <host-name>"` against project root |
| Inspect | `hatch/mcp_host_config/strategies.py`, `fields.py`, `models.py` |
| Success | Existing strategy, adapter, or field set provides needed data |
| Fall through | Host is entirely new with no existing references |

### Level 4: User Escalation

| Action | Detail |
|--------|--------|
| Start with | Tier 1 (blocking questions) |
| Expand to | Tier 2 if Tier 1 reveals non-standard behavior |
| Ask Tier 3 | Only for remaining ambiguities after Tiers 1-2 |
| Success | All blocking questions answered; remaining gaps have safe defaults |

---

## 2. Structured Questionnaire

17 questions across 4 categories.

### Category A: Host Identity & Config Location

| ID | Question | Why It Matters | Files Affected |
|----|----------|----------------|----------------|
| A1 | What is the host's canonical name? (lowercase, hyphens, e.g. `"kiro"`) | Becomes `MCPHostType` enum value and adapter `host_name`. | `models.py`, all files |
| A2 | Where is the config file on each platform? (macOS, Linux, Windows paths) | Strategy `get_config_path()` requires platform-specific path logic. | `strategies.py` |
| A3 | What is the config file format? (JSON or TOML) | Determines strategy read/write implementation and which strategy family to inherit. | `strategies.py` |
| A4 | What is the root key for MCP servers in the config file? | Strategy `get_config_key()`. Known values: `mcpServers`, `servers`, `mcp_servers`. | `strategies.py` |
| A5 | How to detect if the host is installed on the system? | Strategy `is_host_available()`. Most hosts check for a directory's existence. | `strategies.py` |

### Category B: Field Support

| ID | Question | Why It Matters | Files Affected |
|----|----------|----------------|----------------|
| B1 | Which transport types does the host support? (stdio, sse, http) | Drives validation rules in `validate_filtered()`. | adapter |
| B2 | Does the host support the `type` discriminator field? (`"type": "stdio"` / `"sse"`) | Determines membership in `TYPE_SUPPORTING_HOSTS` in `fields.py`. | `fields.py` |
| B3 | What host-specific fields exist beyond the universal set? (name, type, description, required/optional for each) | Defines the field set constant in `fields.py` and new `MCPServerConfig` field declarations. | `fields.py`, `models.py` |
| B4 | Does the host use different names for standard fields? (e.g. Codex: `arguments` instead of `args`) | Determines whether a `FIELD_MAPPINGS` dict and `apply_transformations()` override are needed. | `fields.py`, adapter |
| B5 | Are there fields semantically equivalent to another host's fields? (e.g. Gemini `includeTools` = Codex `enabled_tools`) | Cross-host sync field mappings. Without mappings, sync silently drops the field. | `fields.py`, adapter |

### Category C: Validation & Serialization

| ID | Question | Why It Matters | Files Affected |
|----|----------|----------------|----------------|
| C1 | Can the host have multiple transports simultaneously, or exactly one? | Core validation in `validate_filtered()`. Most hosts require exactly one. | adapter |
| C2 | Are any fields mutually exclusive? (beyond transports) | Additional validation rules. | adapter |
| C3 | Are any fields conditionally required? (e.g. `oauth_enabled=true` requires `oauth_clientId`) | Additional validation rules. | adapter |
| C4 | Does serialization require structural transformation beyond field renaming? | Whether a custom `serialize()` override is needed. | adapter |
| C5 | Does the config file contain non-MCP sections that must be preserved on write? | Strategy `write_configuration()` must read-before-write and merge. | `strategies.py` |

### Category D: Architectural Fit

| ID | Question | Why It Matters | Files Affected |
|----|----------|----------------|----------------|
| D1 | Is this host functionally identical to an existing host? (same fields, same validation, different name only) | Variant pattern: reuse an existing adapter with a `variant` parameter instead of a new class. | adapter, `registry.py` |
| D2 | Does this host share config format and I/O logic with an existing host? | Strategy family: inherit from `ClaudeHostStrategy` or `CursorBasedHostStrategy` instead of bare `MCPHostStrategy`. | `strategies.py` |

---

## 3. Escalation Tiers

Present questions progressively. Do not ask Tier 2 or 3 unless triggered.

### Tier 1: Blocking -- cannot proceed without answers (A1, A2, A3, A4, B1, B3)

| ID | Summary |
|----|---------|
| A1 | Host canonical name |
| A2 | Config file path per platform |
| A3 | Config file format (JSON/TOML) |
| A4 | Root key for MCP servers |
| B1 | Supported transport types |
| B3 | Host-specific fields beyond universal set |

### Tier 2: Complexity-triggered -- ask if Tier 1 reveals non-standard behavior

| ID | Trigger condition |
|----|-------------------|
| B4 | Host uses different names for standard fields |
| B5 | Host has tool filtering fields that map to another host's equivalents |
| C1 | Unclear whether transports are mutually exclusive |
| C4 | Config format requires structural nesting beyond flat key-value |
| C5 | Config file has non-MCP sections |

### Tier 3: Ambiguity-only -- ask only if reading existing adapters leaves it unclear

| ID | Trigger condition |
|----|-------------------|
| A5 | Host detection mechanism is non-obvious |
| B2 | Unclear whether host uses `type` discriminator |
| C2 | Possible field mutual exclusion beyond transports |
| C3 | Possible conditional field requirements |
| D1 | Host looks identical to an existing one |
| D2 | Host I/O looks similar to an existing strategy family |

---

## 4. Existing Host Reference Table

| Host | Format | Root Key | macOS Path | Detection |
|------|--------|----------|------------|-----------|
| `claude-desktop` | JSON | `mcpServers` | `~/Library/Application Support/Claude/claude_desktop_config.json` | Config parent dir exists |
| `claude-code` | JSON | `mcpServers` | `~/.claude.json` | File exists |
| `vscode` | JSON | `servers` | `~/Library/Application Support/Code/User/mcp.json` | Code User dir exists |
| `cursor` | JSON | `mcpServers` | `~/.cursor/mcp.json` | `.cursor/` exists |
| `lmstudio` | JSON | `mcpServers` | `~/.lmstudio/mcp.json` | `.lmstudio/` exists |
| `gemini` | JSON | `mcpServers` | `~/.gemini/settings.json` | `.gemini/` exists |
| `kiro` | JSON | `mcpServers` | `~/.kiro/settings/mcp.json` | `.kiro/settings/` exists |
| `codex` | TOML | `mcp_servers` | `~/.codex/config.toml` | `.codex/` exists |

### Strategy Families

| Family Base Class | Members | Provides |
|-------------------|---------|----------|
| `ClaudeHostStrategy` | `ClaudeDesktopStrategy`, `ClaudeCodeStrategy` | Shared JSON read/write, `_preserve_claude_settings()` |
| `CursorBasedHostStrategy` | `CursorHostStrategy`, `LMStudioHostStrategy` | Shared Cursor-format JSON read/write |
| `MCPHostStrategy` (standalone) | `VSCodeHostStrategy`, `GeminiHostStrategy`, `KiroHostStrategy`, `CodexHostStrategy` | No shared logic -- each owns its I/O |

### Type Discriminator Support

Hosts in `TYPE_SUPPORTING_HOSTS`: `claude-desktop`, `claude-code`, `vscode`, `cursor`.

All other hosts (`lmstudio`, `gemini`, `kiro`, `codex`) do NOT emit the `type` field.

---

## 5. Host Spec YAML Output Format

Fill every field; use `null` or `[]` for inapplicable values.

```yaml
host:
  name: "<canonical-name>"            # A1
  config_format: "json"               # A3 — "json" or "toml"
  config_key: "mcpServers"            # A4

paths:                                 # A2
  darwin: "~/path/to/config.json"
  linux: "~/path/to/config.json"
  windows: "~/path/to/config.json"

detection:                             # A5
  method: "directory_exists"           # "directory_exists" | "file_exists"
  path: "~/.<host-name>/"

transports:                            # B1
  supported: ["stdio", "sse"]
  mutual_exclusion: true               # C1

fields:                                # B2, B3
  type_discriminator: true             # B2 — join TYPE_SUPPORTING_HOSTS?
  host_specific:                       # B3 — list each non-universal field
    - name: "field_name"
      type: "Optional[str]"
      description: "What this field does"
    - name: "another_field"
      type: "Optional[bool]"
      description: "What this field does"

field_mappings:                        # B4, B5
  args: "arguments"                    # universal name -> host name (B4)
  includeTools: "enabled_tools"        # cross-host equivalent (B5)

validation:                            # C2, C3
  mutual_exclusions: []                # field pairs that cannot coexist
  conditional_requirements: []         # {if: "field=value", then: "required_field"}

serialization:                         # C4
  structural_transform: false          # true if custom serialize() needed

config_file:                           # C5
  preserved_sections: []               # non-MCP keys to preserve on write

architecture:                          # D1, D2
  variant_of: null                     # existing adapter to reuse, or null
  strategy_family: null                # base class to inherit, or null
```

Validate the completed spec against these rules before proceeding:
- `host.name` matches lowercase-with-hyphens pattern
- `paths` has at least `darwin` or `linux` defined
- `transports.supported` is non-empty
- If `field_mappings` is non-empty, verify each source field exists in another host's field set
- If `architecture.variant_of` is set, confirm the named adapter exists in the registry
- If `architecture.strategy_family` is set, confirm the named base class exists in `strategies.py`
