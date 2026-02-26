# Discovery Questionnaire: Adding a New MCP Host

## Purpose

Exhaustive list of information the agent needs to add support for a new MCP host platform. Derived from tracing every codepath that makes a host-specific decision across 10+ source files.

This questionnaire serves two purposes:
1. **Discovery checklist** — what the agent must find via web research or codebase retrieval
2. **User escalation template** — what to ask the user when discovery tools are unavailable or insufficient

---

## Category A: Host Identity & Config Location

Discoverable via official docs, GitHub repos, or config file examples.

| # | Question | Why it matters | File(s) affected |
|---|----------|----------------|------------------|
| A1 | What is the host's canonical name? (e.g., `"kiro"`, `"claude-desktop"`) | Becomes the `MCPHostType` enum value and the adapter `host_name`. Convention: lowercase with hyphens. | `models.py`, every other file |
| A2 | Where is the config file on each platform? (macOS, Linux, Windows paths) | Strategy `get_config_path()` — every existing host has platform-specific path logic. | `strategies.py` |
| A3 | What is the config file format? (JSON or TOML) | Determines strategy `read_configuration()` / `write_configuration()` implementation and which strategy family to inherit from. Only Codex uses TOML; all others use JSON. | `strategies.py` |
| A4 | What is the root key for MCP servers in the config file? | Strategy `get_config_key()`. Known values: `"mcpServers"` (most hosts), `"servers"` (VSCode), `"mcp_servers"` (Codex). | `strategies.py` |
| A5 | How to detect if host is installed on the system? | Strategy `is_host_available()`. Most hosts check for a directory's existence (e.g., `~/.kiro/settings/`). | `strategies.py` |

### Existing host examples for reference

| Host | Format | Root Key | macOS Path | Detection |
|------|--------|----------|------------|-----------|
| claude-desktop | JSON | `mcpServers` | `~/Library/Application Support/Claude/claude_desktop_config.json` | Config parent dir exists |
| claude-code | JSON | `mcpServers` | `~/.claude.json` | File exists |
| vscode | JSON | `servers` | `~/Library/Application Support/Code/User/mcp.json` | Code dir exists |
| cursor | JSON | `mcpServers` | `~/.cursor/mcp.json` | `.cursor/` exists |
| lmstudio | JSON | `mcpServers` | `~/.lmstudio/mcp.json` | `.lmstudio/` exists |
| gemini | JSON | `mcpServers` | `~/.gemini/settings.json` | `.gemini/` exists |
| kiro | JSON | `mcpServers` | `~/.kiro/settings/mcp.json` | `.kiro/settings/` exists |
| codex | TOML | `mcp_servers` | `~/.codex/config.toml` | `.codex/` exists |

---

## Category B: Field Support

Partially discoverable from host documentation. This is where web research helps most — host docs usually list supported config fields.

| # | Question | Why it matters | File(s) affected |
|---|----------|----------------|------------------|
| B1 | Which transport types does the host support? (stdio, sse, http) | Drives validation rules in `validate_filtered()`. Most hosts support stdio + sse. Gemini also supports http via `httpUrl`. | adapter |
| B2 | Does the host support the `type` discriminator field? (the `"type": "stdio"` / `"sse"` field) | Determines whether host joins `TYPE_SUPPORTING_HOSTS` in `fields.py`. Claude, VSCode, Cursor, LM Studio support it. Gemini, Kiro, Codex do not. | `fields.py` |
| B3 | What host-specific fields exist beyond the universal set? (List each with: field name, type, description, required/optional) | Defines the field set constant in `fields.py` and potentially new `MCPServerConfig` field declarations in `models.py`. | `fields.py`, `models.py` |
| B4 | Does the host use different names for standard fields? (e.g., Codex uses `arguments` instead of `args`, `http_headers` instead of `headers`) | Determines whether a `FIELD_MAPPINGS` dict and `apply_transformations()` override are needed. | `fields.py`, adapter |
| B5 | Are there fields semantically equivalent to another host's fields? (e.g., Gemini `includeTools` ≈ Codex `enabled_tools`) | Cross-host sync field mappings. Codex maps `includeTools` → `enabled_tools` and `excludeTools` → `disabled_tools` to enable transparent Gemini→Codex sync. Without mappings, sync silently drops the field. | `fields.py`, adapter |

### Universal fields (supported by ALL hosts)

Every host inherits these 5 fields from `UNIVERSAL_FIELDS`:

| Field | Type | Description |
|-------|------|-------------|
| `command` | `str` | stdio transport — command to execute |
| `args` | `List[str]` | Command arguments |
| `env` | `Dict[str, str]` | Environment variables |
| `url` | `str` | sse/http transport — server URL |
| `headers` | `Dict[str, str]` | HTTP headers for remote transports |

---

## Category C: Validation & Serialization Rules

Often discoverable from host documentation, sometimes ambiguous.

| # | Question | Why it matters | File(s) affected |
|---|----------|----------------|------------------|
| C1 | Transport mutual exclusion: can the host have multiple transports simultaneously, or exactly one? | Core validation logic in `validate_filtered()`. Most hosts require exactly one. Gemini supports three (`command`, `url`, `httpUrl`) but still requires exactly one at a time. | adapter |
| C2 | Are any fields mutually exclusive? (beyond transports) | Additional validation rules in `validate_filtered()`. | adapter |
| C3 | Are any fields conditionally required? (e.g., "if `oauth_enabled` is true, then `oauth_clientId` is required") | Additional validation rules in `validate_filtered()`. | adapter |
| C4 | Does serialization require structural transformation beyond field renaming? (e.g., nesting fields under a sub-key, wrapping transport in a sub-object) | Whether a custom `serialize()` override is needed instead of the standard filter→validate→transform pipeline. | adapter |
| C5 | Does the config file contain non-MCP sections that must be preserved on write? (e.g., Codex preserves `[features]`, Gemini preserves other settings keys) | Strategy `write_configuration()` must read-before-write and merge, not overwrite. | `strategies.py` |

---

## Category D: Architectural Fit

Requires judgment based on comparing the new host against existing implementations. Rarely discoverable from external docs alone.

| # | Question | Why it matters | File(s) affected |
|---|----------|----------------|------------------|
| D1 | Is this host functionally identical to an existing host? (same fields, same validation, different name only) | Variant pattern: reuse an existing adapter class with a `variant` constructor parameter (like `ClaudeAdapter(variant="desktop")` / `ClaudeAdapter(variant="code")`) instead of creating a new class. | adapter, `registry.py` |
| D2 | Does this host share config format and I/O logic with an existing host? | Strategy family: inherit from `ClaudeHostStrategy` or `CursorBasedHostStrategy` instead of bare `MCPHostStrategy`, getting `read_configuration()` and `write_configuration()` for free. | `strategies.py` |

### Existing strategy families

| Family Base Class | Members | What it provides |
|-------------------|---------|------------------|
| `ClaudeHostStrategy` | `ClaudeDesktopStrategy`, `ClaudeCodeStrategy` | Shared JSON read/write, `_preserve_claude_settings()` |
| `CursorBasedHostStrategy` | `CursorHostStrategy`, `LMStudioHostStrategy` | Shared Cursor-format JSON read/write |
| `MCPHostStrategy` (standalone) | `VSCodeHostStrategy`, `GeminiHostStrategy`, `KiroHostStrategy`, `CodexHostStrategy` | No shared logic — each implements its own I/O |

---

## 5. Escalation Tiers

When the agent must ask the user (because discovery tools are unavailable or returned insufficient data), present questions in tiers to avoid overwhelming with a single wall of questions.

### Tier 1: Blocking — cannot proceed without answers

Ask these first. Every answer feeds directly into a required file modification.

| Question IDs | Summary |
|--------------|---------|
| A1 | Host canonical name |
| A2 | Config file path per platform |
| A3 | Config file format (JSON/TOML) |
| A4 | Root key for MCP servers |
| B1 | Supported transport types |
| B3 | Host-specific fields (names, types, descriptions) |

### Tier 2: Important — ask if Tier 1 reveals complexity

Ask these after Tier 1 if the host has non-standard behavior.

| Question IDs | Trigger condition |
|--------------|-------------------|
| B4 | Host uses different names for standard fields |
| B5 | Host has tool filtering fields that map to another host's equivalents |
| C1 | Unclear whether transports are mutually exclusive |
| C4 | Config format requires structural nesting beyond flat key-value |
| C5 | Config file has non-MCP sections |

### Tier 3: Clarification — ask only if ambiguous

Ask these only if reading existing adapters and strategies leaves the answer unclear.

| Question IDs | Trigger condition |
|--------------|-------------------|
| A5 | Host detection mechanism is non-obvious |
| B2 | Unclear whether host uses `type` discriminator field |
| C2 | Possible field mutual exclusion beyond transports |
| C3 | Possible conditional field requirements |
| D1 | Host looks identical to an existing one |
| D2 | Host I/O looks similar to an existing strategy family |

---

## 6. Discovery Output Format

Whether the information comes from web research or user answers, the agent should produce a structured **Host Spec** before proceeding to implementation. This artifact feeds steps 2-5 of the skill workflow.

```yaml
host:
  name: "your-host"               # A1
  config_format: "json"           # A3
  config_key: "mcpServers"        # A4

paths:                             # A2
  darwin: "~/.your-host/config.json"
  linux: "~/.config/your-host/config.json"
  windows: "~/.your-host/config.json"

detection:                         # A5
  method: "directory_exists"
  path: "~/.your-host/"

transports:                        # B1
  supported: ["stdio", "sse"]
  mutual_exclusion: true           # C1

fields:                            # B2, B3
  type_discriminator: true
  host_specific:
    - name: "your_field"
      type: "Optional[str]"
      description: "Description"
    - name: "another_field"
      type: "Optional[bool]"
      description: "Description"

field_mappings: {}                 # B4, B5 (empty if no mappings)

validation:                        # C2, C3
  mutual_exclusions: []
  conditional_requirements: []

serialization:                     # C4
  structural_transform: false

config_file:                       # C5
  preserved_sections: []

architecture:                      # D1, D2
  variant_of: null
  strategy_family: null
```

---

## 7. Key Design Decisions for Skill Authoring

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| Architecture doc content in skill? | No — stays as developer documentation | Agent doesn't need architectural understanding to follow the recipe |
| Field support matrix in skill? | No — agent reads `fields.py` directly | Avoids stale duplication; agent can inspect the source of truth |
| MCPServerConfig model listing? | No — agent reads `models.py` directly | Same rationale |
| Testing infrastructure deep-dive? | Minimal — just "add these fixtures, run these commands" | Agent doesn't need to understand generators to add fixture data |
| Discovery step as first step? | Yes | Biggest bottleneck is knowing what fields the host supports; makes the rest mechanical |
| Structured output from discovery? | Yes — Host Spec YAML | Decouples information gathering from implementation; same spec whether from web or user |
| Progressive disclosure? | Yes — adapter/strategy/testing contracts in `references/` | Keeps SKILL.md lean; loaded only when host has non-standard needs |
