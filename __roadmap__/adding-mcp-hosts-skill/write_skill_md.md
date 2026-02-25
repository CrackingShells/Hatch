# Write Skill MD

**Goal**: Write the main SKILL.md with frontmatter and 5-step workflow body.
**Pre-conditions**:
- [ ] Branch `task/write-skill-md` created from `milestone/adding-mcp-hosts-skill`
**Success Gates**:
- `__design__/skills/adding-mcp-hosts/SKILL.md` exists with valid frontmatter
- Body under 500 lines with 5-step workflow
- Links to all 4 reference files by relative path
**References**:
- [R01 §2-3](../../__reports__/mcp_support_extension_skill/skill-design-analysis.md) — Proposed structure and workflow
- [R03](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — Frontmatter rules, description guidelines

---

## Step 1: Write SKILL.md

**Goal**: Create the main skill file with frontmatter and workflow body.

**Implementation Logic**:
Create `__design__/skills/adding-mcp-hosts/SKILL.md` (`mkdir -p` the path first).

**Frontmatter** (YAML):
- `name`: `adding-mcp-hosts`
- `description`: Third-person, ~200-300 chars. Must cover:
  - WHAT: Adds support for a new MCP host platform to the Hatch CLI multi-host configuration system
  - WHEN: When asked to add, integrate, or extend MCP host support for a new IDE, editor, or AI coding tool (e.g., Windsurf, Zed, Copilot)
  - HOW: 5-step workflow from discovery through test verification
  No angle brackets. No reserved words. Max 1024 chars.

**Body** (Markdown, target 150-200 lines). Use imperative form throughout. Structure:

1. **Workflow checklist** — Copy-paste progress tracker:
   ```
   - [ ] Step 1: Discover host requirements
   - [ ] Step 2: Add enum and field set
   - [ ] Step 3: Create adapter and strategy
   - [ ] Step 4: Wire integration points
   - [ ] Step 5: Register test fixtures
   ```

2. **Step 1: Discover host requirements** (~15 lines):
   - "Read [references/discovery-guide.md](references/discovery-guide.md) for the full discovery workflow."
   - Summarize: use web tools to research, fall back to user questionnaire, produce Host Spec YAML.
   - Output: structured Host Spec feeding all subsequent steps.

3. **Step 2: Add enum and field set** (~20 lines, inline):
   - Add `MCPHostType` enum value in `hatch/mcp_host_config/models.py`
   - Add `<HOST>_FIELDS` frozenset in `hatch/mcp_host_config/fields.py` (pattern: `UNIVERSAL_FIELDS | {extras}`)
   - Optionally add new `MCPServerConfig` fields if host introduces novel fields
   - Verification: `python -c "from hatch.mcp_host_config.models import MCPHostType; print(MCPHostType.YOUR_HOST)"`

4. **Step 3: Create adapter and strategy** (~20 lines):
   - "Read [references/adapter-contract.md](references/adapter-contract.md) for the adapter interface."
   - "Read [references/strategy-contract.md](references/strategy-contract.md) for the strategy interface."
   - Mention variant pattern shortcut (if host is functionally identical to existing host)
   - Mention strategy family decision (inherit from ClaudeHostStrategy, CursorBasedHostStrategy, or standalone)
   - Verification: import and instantiate the adapter.

5. **Step 4: Wire integration points** (~20 lines, inline):
   - `adapters/__init__.py` — export new adapter
   - `adapters/registry.py` — add `_register_defaults()` entry
   - `backup.py` — add hostname to `supported_hosts` set
   - `reporting.py` — add `MCPHostType → host_name` mapping
   - Verification: `python -c "from hatch.mcp_host_config.adapters.registry import AdapterRegistry; ..."`

6. **Step 5: Register test fixtures** (~15 lines):
   - "Read [references/testing-fixtures.md](references/testing-fixtures.md) for fixture schemas and registration."
   - Add entry to `tests/test_data/mcp_adapters/canonical_configs.json`
   - Add entries to `tests/test_data/mcp_adapters/host_registry.py`
   - Verification: `python -m pytest tests/integration/mcp/ tests/unit/mcp/ tests/regression/mcp/ -v`

7. **Cross-references table** (~10 lines):
   | Reference | Covers | Read when |
   | discovery-guide.md | Host research, questionnaire, Host Spec YAML | Step 1 (always) |
   | adapter-contract.md | BaseAdapter interface, field sets, registry wiring | Step 3 (always) |
   | strategy-contract.md | MCPHostStrategy interface, families, platform paths | Step 3 (always) |
   | testing-fixtures.md | Fixture schema, auto-generated tests, pytest commands | Step 5 (always) |

No conceptual explanations. No "what is Pydantic." No architecture overview. Just the recipe.

**Deliverables**: `__design__/skills/adding-mcp-hosts/SKILL.md` (~150-200 lines)
**Consistency Checks**: `python quick_validate.py __design__/skills/adding-mcp-hosts/` (expected: PASS)
**Commit**: `feat(skill): write SKILL.md with 5-step workflow`
