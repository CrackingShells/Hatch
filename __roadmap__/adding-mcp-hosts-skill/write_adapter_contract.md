# Write Adapter Contract

**Goal**: Document the adapter interface contract for implementing a new host adapter.
**Pre-conditions**:
- [ ] Branch `task/write-adapter-contract` created from `milestone/adding-mcp-hosts-skill`
**Success Gates**:
- `__design__/skills/adding-mcp-hosts/references/adapter-contract.md` exists
- Covers all 7 subsections and references all 10 files from R01 §4
**References**: [R01 §4](../../__reports__/mcp_support_extension_skill/skill-design-analysis.md) — Complete file modification surface

---

## Step 1: Write adapter-contract.md

**Goal**: Create the reference file documenting everything an agent needs to implement a host adapter.

**Implementation Logic**:
Create `__design__/skills/adding-mcp-hosts/references/adapter-contract.md` (`mkdir -p` the path first). Derive from R01 §4 cross-referenced with the codebase. Read the following files to extract exact patterns:
- `hatch/mcp_host_config/fields.py` — field set constants, UNIVERSAL_FIELDS, TYPE_SUPPORTING_HOSTS, existing FIELD_MAPPINGS
- `hatch/mcp_host_config/models.py` — MCPHostType enum, MCPServerConfig model
- `hatch/mcp_host_config/adapters/` — BaseAdapter ABC, existing adapter implementations
- `hatch/mcp_host_config/adapters/__init__.py` — export pattern
- `hatch/mcp_host_config/adapters/registry.py` — `_register_defaults()` pattern
- `hatch/mcp_host_config/backup.py` — `supported_hosts` set in `BackupInfo.validate_hostname()`
- `hatch/mcp_host_config/reporting.py` — `MCPHostType → host_name` mapping in `_get_adapter_host_name()`

Structure:

1. **MCPHostType enum** — How to add the enum value. Convention: `UPPER_SNAKE = "kebab-case"`. File: `hatch/mcp_host_config/models.py`.

2. **Field set declaration** — How to define `<HOST>_FIELDS` frozenset in `hatch/mcp_host_config/fields.py`. Pattern: `UNIVERSAL_FIELDS | {host-specific fields}`. Include `TYPE_SUPPORTING_HOSTS` membership decision.

3. **MCPServerConfig fields** — When to add new field declarations to `MCPServerConfig`. Only needed if host introduces fields not already in the model. File: `hatch/mcp_host_config/models.py`.

4. **Adapter class** — `BaseAdapter` interface. Lean template with required method signatures:
   - `get_supported_fields()` → return the field set constant
   - `validate_filtered()` → transport mutual exclusion + host-specific rules
   - `apply_transformations()` → field renaming via mappings dict (if applicable)
   - `serialize()` → standard pipeline (filter → validate → transform), override only if structural transformation needed
   Show the `validate_filtered()` template snippet from the extension guide.

5. **Field mappings** — When to define `<HOST>_FIELD_MAPPINGS` dict. Pattern: `{"standard_name": "host_name"}`. Reference `CODEX_FIELD_MAPPINGS` as canonical example.

6. **Variant pattern** — When to reuse an existing adapter with a variant parameter instead of a new class. Reference `ClaudeAdapter(variant="desktop"|"code")` as canonical example.

7. **Wiring and integration points** — All 4 one-liner integration files:
   - `adapters/__init__.py` — export new adapter class
   - `adapters/registry.py` — `_register_defaults()` entry mapping `MCPHostType → adapter instance`
   - `backup.py` — add hostname string to `supported_hosts` set
   - `reporting.py` — add `MCPHostType → host_name` entry in mapping dict

**Deliverables**: `__design__/skills/adding-mcp-hosts/references/adapter-contract.md` (~120-160 lines)
**Consistency Checks**: File covers all 7 subsections; references all source files listed above
**Commit**: `feat(skill): add adapter contract reference`
