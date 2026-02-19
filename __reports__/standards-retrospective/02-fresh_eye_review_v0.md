# Fresh-Eye Review — Post-Implementation Gap Analysis (v0)

Date: 2026-02-19
Follows: `01-instructions_redesign_v3.md` implementation via `__roadmap__/instructions-redesign/`

## Executive Summary

After the instruction files were rewritten/edited per the v3 redesign, a fresh-eye review reveals **residual stale terminology** in 6 files that were NOT in the §11 affected list, **1 stale cross-reference** in a file that WAS edited, and **1 useful addition** (the `roadmap-execution.instructions.md`) that emerged during implementation but wasn't anticipated in the architecture report. A companion JSON schema (`roadmap-document-schema.json`) is proposed and delivered alongside this report.

## Findings

### F1: Stale "Phase N" Terminology in Edited Files

These files were in the §11 scope and were edited, but retain stale Phase references:

| File | Location | Stale Text | Suggested Fix |
|:-----|:---------|:-----------|:--------------|
| `reporting.instructions.md` | §2 "Default artifacts" | "Phase 1: Mermaid diagrams…" / "Phase 2: Risk-driven test matrix…" | Replace with "Architecture reports:" / "Test definition reports:" (drop phase numbering) |
| `reporting.instructions.md` | §"Specialized reporting guidance" | "Phase 1 architecture guidance" / "Phase 2 test definition reports" | "Architecture reporting guidance" / "Test definition reporting guidance" |
| `reporting.instructions.md` | §"Where reports go" | "Use `__design__/` for durable design/roadmaps." | "Use `__design__/` for durable architectural decisions." (roadmaps go in `__roadmap__/`, already stated in reporting-structure) |
| `reporting-architecture.instructions.md` | Title + front-matter + opening line | "Phase 1" in title, description, and body | "Stage 1" or simply "Architecture Reporting" |
| `reporting-structure.instructions.md` | §3 README convention | "Phase 1/2/3 etc." | "Stage 1/2/3 etc." or "Analysis/Roadmap/Execution" |

**Severity**: Low — cosmetic inconsistency, but agents parsing these instructions may be confused by mixed terminology.

### F2: Stale "Phase N" Terminology in Files Outside §11 Scope

These files were NOT listed in §11 and were not touched during the campaign:

| File | Location | Stale Text | Suggested Fix |
|:-----|:---------|:-----------|:--------------|
| `reporting-tests.instructions.md` | Title, front-matter, §body (6+ occurrences) | "Phase 2" throughout | "Stage 1" or "Test Definition Reporting" (tests are defined during Analysis, not a separate phase) |
| `reporting-templates.instructions.md` | Front-matter + section headers | "Phase 1" / "Phase 2" template headers | "Architecture Analysis" / "Test Definition" |
| `reporting-templates.instructions.md` | §Roadmap Recommendation | "create `__design__/<topic>_roadmap_vN.md`" | "create a roadmap directory tree under `__roadmap__/<campaign>/`" |
| `reporting-knowledge-transfer.instructions.md` | §"What not to do" | "link to Phase 1 artifacts" | "link to Stage 1 analysis artifacts" |
| `analytic-behavior.instructions.md` | §"Two-Phase Work Process" | "Phase 1: Analysis and Documentation" / "Phase 2: Implementation with Context Refresh" | This is a different "phase" concept (analysis vs implementation within a single session), not the old 7-phase model. **Ambiguous but arguably fine** — the two-phase work process here is about agent behavior, not the code-change workflow. Consider renaming to "Two-Step Work Process" or "Analysis-First Work Process" to avoid confusion. |
| `testing.instructions.md` | §2.3 | "Phase 2 report format" | "Test definition report format" |
| `testing.instructions.md` | §2.3 reference text | "Phase 2 in code change phases" | "Stage 1 (Analysis) in code change phases" |

**Severity**: Medium for `reporting-tests.instructions.md` and `reporting-templates.instructions.md` (heavily used during Stage 1 work). Low for the others.

### F3: Missing Cross-Reference in `code-change-phases.instructions.md`

Stage 3 (Execution) describes the breadth-first algorithm but does NOT link to `roadmap-execution.instructions.md`, which contains the detailed operational manual (failure handling escalation ladder, subagent dispatch protocol, status update discipline, completion checklist).

**Suggested fix**: Add a reference in Stage 3:
```markdown
For the detailed operational manual (failure handling, subagent dispatch, status updates), see [roadmap-execution.instructions.md](./roadmap-execution.instructions.md).
```

### F4: `roadmap-execution.instructions.md` — Unanticipated but Valuable

This file was created during the campaign but was not listed in v3 §11. It fills a genuine gap: the v3 report describes WHAT the execution model is, but the execution manual describes HOW an agent should operationally navigate it (including the escalation ladder, subagent dispatch, and status update discipline).

**Recommendation**: Acknowledge in the v3 report's §11 table as an addition, or simply note it in the campaign's amendment log. No action needed — the file is well-written and consistent with the model.

### F5: Schema Companion Delivered

A JSON Schema (`roadmap-document-schema.json`) has been created alongside this report. It formally defines the required and optional fields for:
- `README.md` (directory-level entry point)
- Leaf Task files
- Steps within leaf tasks
- Supporting types (status values, amendment log entries, progress entries, Mermaid node definitions)

Location: `cracking-shells-playbook/instructions/roadmap-document-schema.json`

---

## Prioritized Fix List

| Priority | Finding | Files Affected | Effort |
|:---------|:--------|:---------------|:-------|
| 1 | F1: Stale terminology in edited files | 3 files | ~15 min (surgical text replacements) |
| 2 | F3: Missing cross-reference | 1 file | ~2 min |
| 3 | F2: Stale terminology in unscoped files | 5 files | ~45 min (more occurrences, some require judgment) |
| 4 | F4: Acknowledge execution manual | 1 file (v3 report or amendment log) | ~5 min |

## Decision Required

- **F1 + F3**: Straightforward fixes, recommend immediate application.
- **F2**: Larger scope. The `reporting-tests.instructions.md` and `reporting-templates.instructions.md` files have "Phase" deeply embedded. A dedicated task or amendment may be warranted.
- **F2 (analytic-behavior)**: The "Two-Phase Work Process" is arguably a different concept. Stakeholder judgment needed on whether to rename.
