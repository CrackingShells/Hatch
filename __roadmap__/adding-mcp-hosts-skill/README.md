# Adding MCP Hosts Skill

## Context

Standalone skill authoring campaign. Converts the MCP host configuration extension workflow into a Claude Code agent skill. The skill enables an LLM agent to autonomously add support for a new MCP host platform to the Hatch CLI — from discovery through implementation to test verification.

## Reference Documents

- [R01 Skill Design Analysis](../../__reports__/mcp_support_extension_skill/skill-design-analysis.md) — Skill relevance assessment, proposed structure, 5-step workflow, complete 10-11 file modification surface
- [R02 Discovery Questionnaire](../../__reports__/mcp_support_extension_skill/discovery-questionnaire.md) — 17 questions across 4 categories, 3 escalation tiers, Host Spec YAML output format
- [R03 Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Official skill authoring best practices (web)

## Goal

Produce a packaged `adding-mcp-hosts.skill` file that an agent can use to add support for any new MCP host platform.

## Pre-conditions

- [x] Design reports reviewed (R01, R02)
- [x] Best practices consulted (R03)
- [x] MCP docs refresh campaign completed (architecture doc + extension guide up to date)

## Success Gates

- SKILL.md under 500 lines with 5-step workflow checklist
- 4 reference files with progressive disclosure (discovery, adapter, strategy, testing)
- Skill passes `package_skill.py` validation (frontmatter, naming, description)
- Packaged `.skill` file produced

## Gotchas

- No `init_skill.py` step — each parallel task creates its target file directly. Tasks must `mkdir -p` the skill directory before writing.
- `package_skill.py` imports `quick_validate` from its own directory — must set PYTHONPATH accordingly.
- Skill name must be kebab-case, max 64 chars, no reserved words ("anthropic", "claude"). Using `adding-mcp-hosts`.
- Description must be third-person, max 1024 chars, no angle brackets.
- Reference files should be one level deep from SKILL.md (no nested references).
- All 5 content leaves target different files in `__design__/skills/adding-mcp-hosts/` — worktree merges will be conflict-free.

## Status

```mermaid
graph TD
    write_discovery_guide[Write Discovery Guide]:::done
    write_adapter_contract[Write Adapter Contract]:::done
    write_strategy_contract[Write Strategy Contract]:::done
    write_testing_fixtures[Write Testing Fixtures]:::done
    write_skill_md[Write Skill MD]:::done
    package[Package]:::done

    classDef done fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned fill:#374151,color:#e5e7eb
    classDef amendment fill:#1e3a5f,color:#bfdbfe
    classDef blocked fill:#7f1d1d,color:#fecaca
```

## Nodes

| Node | Type | Status |
|:-----|:-----|:-------|
| `write_discovery_guide.md` | Leaf Task | Done |
| `write_adapter_contract.md` | Leaf Task | Done |
| `write_strategy_contract.md` | Leaf Task | Done |
| `write_testing_fixtures.md` | Leaf Task | Done |
| `write_skill_md.md` | Leaf Task | Done |
| `package/` | Directory | Done |

## Amendment Log

| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress

| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `write_discovery_guide.md` | `task/write-discovery-guide` | 1 | 218 lines, 5 sections |
| `write_adapter_contract.md` | `task/write-adapter-contract` | 1 | 157 lines, 7 subsections |
| `write_strategy_contract.md` | `task/write-strategy-contract` | 1 | 226 lines, 5 sections |
| `write_testing_fixtures.md` | `task/write-testing-fixtures` | 1 | 121 lines, 5 sections |
| `write_skill_md.md` | `task/write-skill-md` | 1 | 202 lines, 5-step workflow |
| `package/package_skill.md` | `task/package-skill` | 1 | Validated + packaged .skill |
