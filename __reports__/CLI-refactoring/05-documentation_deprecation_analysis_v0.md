# Documentation Deprecation Analysis: CLI Refactoring Impact

**Date**: 2026-01-01  
**Phase**: Post-Implementation Documentation Review  
**Scope**: Identifying deprecated documentation after CLI handler-based architecture refactoring  
**Reference**: `__design__/cli-refactoring-milestone-v0.7.2-dev.1.md`

---

## Executive Summary

The CLI refactoring from monolithic `cli_hatch.py` (2,850 LOC) to handler-based architecture in `hatch/cli/` package has rendered several documentation references outdated. This report identifies affected files and specifies required updates.

**Architecture Change Summary:**
```
BEFORE:                          AFTER:
hatch/cli_hatch.py (2,850 LOC)   hatch/cli/
                                 ├── __init__.py      (57 LOC)
                                 ├── __main__.py      (840 LOC)
                                 ├── cli_utils.py     (270 LOC)
                                 ├── cli_mcp.py       (1,222 LOC)
                                 ├── cli_env.py       (375 LOC)
                                 ├── cli_package.py   (552 LOC)
                                 └── cli_system.py    (92 LOC)
                                 
                                 hatch/cli_hatch.py   (136 LOC) ← backward compat shim
```

---

## Affected Documentation Files

### Category 1: API Documentation (HIGH PRIORITY)

| File | Issue | Impact |
|------|-------|--------|
| `docs/articles/api/cli.md` | References `hatch.cli_hatch` only | mkdocstrings generates incomplete API docs |

**Current Content:**
```markdown
# CLI Module
::: hatch.cli_hatch
```

**Required Update:** Expand to document the full `hatch.cli` package structure with all submodules.

---

### Category 2: User Documentation (HIGH PRIORITY)

| File | Line | Issue |
|------|------|-------|
| `docs/articles/users/CLIReference.md` | 3 | States "implemented in `hatch/cli_hatch.py`" |

**Current Content (Line 3):**
```markdown
This document is a compact reference of all Hatch CLI commands and options implemented in `hatch/cli_hatch.py` presented as tables for quick lookup.
```

**Required Update:** Reference the new `hatch/cli/` package structure.

---

### Category 3: Developer Implementation Guides (HIGH PRIORITY)

| File | Lines | Issue |
|------|-------|-------|
| `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md` | 605, 613-626 | References `cli_hatch.py` for CLI integration |

**Affected Sections:**

1. **Line 605** - "Add CLI arguments in `cli_hatch.py`"
2. **Lines 613-626** - CLI Integration for Host-Specific Fields section

**Current Content:**
```markdown
4. **Add CLI arguments** in `cli_hatch.py` (see next section)
...
1. **Update function signature** in `handle_mcp_configure()`:
```python
def handle_mcp_configure(
    # ... existing params ...
    your_field: Optional[str] = None,  # Add your field
):
```
```

**Required Update:** 
- Argument parsing → `hatch/cli/__main__.py`
- Handler modifications → `hatch/cli/cli_mcp.py`

---

### Category 4: Architecture Documentation (MEDIUM PRIORITY)

| File | Line | Issue |
|------|------|-------|
| `docs/articles/devs/architecture/mcp_host_configuration.md` | 158 | References `cli_hatch.py` |

**Current Content (Line 158):**
```markdown
1. Extend `handle_mcp_configure()` function signature in `cli_hatch.py`
```

**Required Update:** Reference new module locations.

---

### Category 5: Architecture Diagrams (MEDIUM PRIORITY)

| File | Line | Issue |
|------|------|-------|
| `docs/resources/diagrams/architecture.puml` | 9 | Shows CLI as single `cli_hatch` component |

**Current Content:**
```plantuml
Container_Boundary(cli, "CLI Layer") {
    Component(cli_hatch, "CLI Interface", "Python", "Command-line interface\nArgument parsing and validation")
}
```

**Required Update:** Reflect modular CLI architecture with handler modules.

---

### Category 6: Instruction Templates (LOW PRIORITY)

| File | Lines | Issue |
|------|-------|-------|
| `cracking-shells-playbook/instructions/documentation-api.instructions.md` | 37-41 | Uses `hatch/cli_hatch.py` as example |

**Current Content:**
```markdown
**For a module `hatch/cli_hatch.py`, create `docs/articles/api/cli.md`:**
```markdown
# CLI Module
::: hatch.cli_hatch
```
```

**Required Update:** Update example to show new CLI package pattern.

---

## Files NOT to Modify

| Category | Files | Reason |
|----------|-------|--------|
| Historical Analysis | `__reports__/CLI-refactoring/00-04*.md` | Document pre-refactoring state |
| Design Documents | `__design__/cli-refactoring-*.md` | Document refactoring plan |
| Handover Documents | `__design__/handover-*.md` | Document session context |

---

## Update Strategy

### Handler Location Mapping

| Handler/Function | Old Location | New Location |
|------------------|--------------|--------------|
| `main()` | `hatch.cli_hatch` | `hatch.cli.__main__` |
| `handle_mcp_configure()` | `hatch.cli_hatch` | `hatch.cli.cli_mcp` |
| `handle_mcp_*()` | `hatch.cli_hatch` | `hatch.cli.cli_mcp` |
| `handle_env_*()` | `hatch.cli_hatch` | `hatch.cli.cli_env` |
| `handle_package_*()` | `hatch.cli_hatch` | `hatch.cli.cli_package` |
| `handle_create()`, `handle_validate()` | `hatch.cli_hatch` | `hatch.cli.cli_system` |
| `parse_host_list()`, utilities | `hatch.cli_hatch` | `hatch.cli.cli_utils` |
| Argument parsing | `hatch.cli_hatch` | `hatch.cli.__main__` |

### Backward Compatibility Note

`hatch/cli_hatch.py` remains as a backward compatibility shim that re-exports all public symbols. External consumers can still import from `hatch.cli_hatch`, but new code should use `hatch.cli.*`.

---

## Implementation Checklist

- [x] Update `docs/articles/api/cli.md` - Expand API documentation
- [x] Update `docs/articles/users/CLIReference.md` - Fix intro paragraph
- [x] Update `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md` - Fix CLI integration section
- [x] Update `docs/articles/devs/architecture/mcp_host_configuration.md` - Fix CLI reference
- [x] Update `docs/resources/diagrams/architecture.puml` - Update CLI component
- [x] Update `cracking-shells-playbook/instructions/documentation-api.instructions.md` - Update example

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Broken mkdocstrings generation | High | Medium | Test docs build after changes |
| Developer confusion from outdated guides | Medium | High | Prioritize implementation guide updates |
| Diagram regeneration issues | Low | Low | Verify PlantUML syntax |

