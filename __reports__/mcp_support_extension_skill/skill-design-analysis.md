# Skill Design Analysis: MCP Host Configuration Extension

## Purpose

Design report for converting the MCP host configuration extension workflow into a Claude Code agent skill. The skill enables an LLM agent to autonomously add support for a new MCP host platform to the Hatch CLI.

---

## 1. Skill Relevance Assessment

### Why it fits

The core use case — "add support for a new MCP host" — is a bounded, repeatable, multi-step procedure with low tolerance for deviation. That is the sweet spot for skills. An agent needs:

1. Procedural steps it cannot infer (which files to touch, in what order)
2. Codebase-specific contracts (field set declaration, registry wiring, decorator usage)
3. Template code that must follow exact patterns (the `validate_filtered()` pipeline, `@register_host_strategy`)
4. Testing fixture requirements (`canonical_configs.json` structure, `FIELD_SETS` mapping)

None of this is general knowledge. An LLM cannot derive it from first principles.

### What does not translate directly from existing docs

The two developer docs (`mcp_host_configuration.md` and `mcp_host_configuration_extension.md`) cannot be transplanted as-is. They need restructuring to match how skills work.

#### 1. Architecture doc is reference material, not instructions

It explains *how the system works*, not *what to do*. In skill terms, it belongs in `references/`, not in SKILL.md. Much of it is context Claude already handles well — what Pydantic does, what ABC means, what "declarative" means. The field support matrix and testing infrastructure sections are the only parts an agent genuinely needs.

#### 2. Extension guide has too much "why"

Sections like "When You Need This", "The Pattern: Adapter + Strategy" overview, the ASCII diagram, the troubleshooting table, and the "Reference: Existing Adapters" table are developer onboarding material. An agent skill should be imperative: "do X, then Y." The existing doc explains concepts; a skill should prescribe actions.

#### 3. Both docs use relative file paths

They say `models.py` and `adapters/your_host.py`. A skill needs absolute paths from the repo root (`hatch/mcp_host_config/models.py`) so the agent can operate without ambiguity.

#### 4. No verification workflow

The extension guide says *what* to create but does not tell the agent how to verify its work. A skill should include the exact commands to run after each step.

#### 5. Information that should be discovered, not loaded

The full field support matrix (35 rows), the MCPServerConfig model (50 lines), and the HostSpec/HostRegistry documentation are heavyweight. An agent adding a new host does not need all of that in context — it needs to know *where to look* and *what to do*. The skill should point to files, not reproduce them.

#### 6. Extension guide understates the integration surface

The guide advertises 4 files to modify. The actual count is 10-11 (see Section 4). Two of the missing files (`backup.py`, `reporting.py`) are boilerplate one-liners but the agent will miss them without explicit instructions.

---

## 2. Proposed Skill Structure

```
add-mcp-host/
├── SKILL.md                    # ~150 lines: trigger, 5-step workflow, verification
└── references/
    ├── discovery-guide.md      # How to research host requirements using available tools
    ├── adapter-contract.md     # BaseAdapter interface, validate_filtered pattern,
    │                           # field mappings, variant pattern
    ├── strategy-contract.md    # MCPHostStrategy interface, decorator, families
    └── testing-fixtures.md     # canonical_configs.json schema, FIELD_SETS,
                                # reverse mappings, what gets auto-generated
```

### SKILL.md scope

- The 5-step checklist (discover → enum → adapter+strategy → wiring → test fixtures) with exact file paths
- Template snippets (lean — just the required method signatures, not full docstrings)
- Verification commands per step
- Conditional reads: "Read `references/adapter-contract.md` if the host needs field mappings or custom serialization"

### What stays outside the skill

The architecture doc (`mcp_host_configuration.md`) remains as developer documentation. The skill should reference it for humans but an agent does not need architectural understanding to follow the recipe.

---

## 3. Proposed Workflow: 5 Steps

The current extension guide has 4 steps. The skill adds a prior discovery step, making 5:

| Step | Name | Description |
|------|------|-------------|
| 1 | **Discover host requirements** | Research the target host's MCP config spec using web tools, Context7, or user escalation |
| 2 | **Add enum and field set** | `models.py` enum + `fields.py` field constant + optionally new MCPServerConfig fields |
| 3 | **Create adapter and strategy** | Adapter class + strategy class with `@register_host_strategy` |
| 4 | **Wire integration points** | `adapters/__init__.py`, `adapters/registry.py`, `backup.py`, `reporting.py` |
| 5 | **Register test fixtures** | `canonical_configs.json` + `host_registry.py` entries |

Step 1's output (a structured field spec) feeds all decisions in steps 2-5.

### Discovery step: tool priority ladder

The agent should try discovery tools in order and fall through gracefully:

1. **Web search + fetch** — find the host's official MCP config docs
2. **Context7** — query library documentation
3. **Codebase retrieval** — check if the host's config format is already partially documented in the repo
4. **Escalate to user** — structured questionnaire (see Section 5)

If web tools are unavailable in the agent's environment, it must escalate immediately.

---

## 4. Complete File Modification Surface

Every file the agent must touch when adding a new host:

| # | File (from repo root) | Always? | What to add |
|---|------|---------|-------------|
| 1 | `hatch/mcp_host_config/models.py` | Yes | `MCPHostType` enum value |
| 2 | `hatch/mcp_host_config/fields.py` | Yes | Field set constant (e.g., `NEW_HOST_FIELDS`), optionally field mappings dict |
| 3 | `hatch/mcp_host_config/adapters/new_host.py` | Yes | New adapter class (or variant registration if identical to existing host) |
| 4 | `hatch/mcp_host_config/adapters/__init__.py` | Yes | Export new adapter class |
| 5 | `hatch/mcp_host_config/adapters/registry.py` | Yes | `_register_defaults()` entry |
| 6 | `hatch/mcp_host_config/strategies.py` | Yes | Strategy class with `@register_host_strategy` decorator |
| 7 | `hatch/mcp_host_config/backup.py` | Yes | Add hostname string to `supported_hosts` set in `BackupInfo.validate_hostname()` |
| 8 | `hatch/mcp_host_config/reporting.py` | Yes | Add `MCPHostType → host_name` entry in `_get_adapter_host_name()` mapping |
| 9 | `tests/test_data/mcp_adapters/canonical_configs.json` | Yes | Canonical config fixture using host-native field names |
| 10 | `tests/test_data/mcp_adapters/host_registry.py` | Yes | `FIELD_SETS` entry, `adapter_map` entry in `HostSpec.get_adapter()`, optionally reverse mappings |
| 11 | `hatch/mcp_host_config/models.py` (MCPServerConfig) | Conditional | New field declarations — only if host introduces fields not already in the model |

Files 7 and 8 are boilerplate one-liners but are absent from the current extension guide. The agent will miss them without explicit instructions.
