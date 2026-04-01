# MCP Host Config Dev Docs Refresh

## Context

Standalone doc cleanup campaign. The developer documentation for the MCP host configuration system has diverged from the codebase, primarily in the testing infrastructure section but also in the field support matrix, architectural patterns, and extension guide templates. This campaign updates both the architecture reference doc and the extension guide to match codebase reality.

## Reference Documents

- [R01 Gap Analysis](../../__reports__/mcp-docs-refresh/docs-vs-codebase-gap-analysis.md) — Full docs-vs-codebase comparison with severity ratings

## Goal

Align MCP host config dev docs with the current codebase state so contributors get accurate guidance when adding new hosts.

## Pre-conditions

- [x] Gap analysis report reviewed (R01)
- [x] `dev` branch checked out

## Success Gates

- All documented field support matches `fields.py` constants
- All documented patterns match codebase implementations
- Testing section accurately describes `tests/test_data/mcp_adapters/` infrastructure
- Extension guide Step 2-4 templates produce working implementations when followed literally

## Gotchas

- `validate()` is deprecated but still abstract in `BaseAdapter` — document the migration path without removing it yet (that's a code change for v0.9.0, not a doc change).
- LM Studio is missing from the field support matrix entirely — verify whether it needs its own column or shares Claude's field set.
- Both tasks edit separate files (`mcp_host_configuration.md` vs `mcp_host_configuration_extension.md`), so they can safely execute in parallel. Cross-references between the two docs should be verified after both complete.

## Status

```mermaid
graph TD
    update_architecture_doc[Update Architecture Doc]:::done
    update_extension_guide[Update Extension Guide]:::done

    classDef done fill:#166534,color:#bbf7d0
    classDef inprogress fill:#854d0e,color:#fef08a
    classDef planned fill:#374151,color:#e5e7eb
    classDef amendment fill:#1e3a5f,color:#bfdbfe
    classDef blocked fill:#7f1d1d,color:#fecaca
```

## Nodes

| Node | Type | Status |
|:-----|:-----|:-------|
| `update_architecture_doc.md` | Leaf Task | Done |
| `update_extension_guide.md` | Leaf Task | Done |

## Amendment Log

| ID | Date | Source | Nodes Added | Rationale |
|:---|:-----|:-------|:------------|:----------|

## Progress

| Node | Branch | Commits | Notes |
|:-----|:-------|:--------|:------|
| `update_architecture_doc.md` | `task/update-architecture-doc` | 3 | Field matrix, strategy/variant patterns, testing section |
| `update_extension_guide.md` | `task/update-extension-guide` | 3 | validate_filtered template, strategy interface docs, data-driven testing |
