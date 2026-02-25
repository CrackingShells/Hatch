# Package Skill

**Goal**: Validate and package the skill into a distributable `.skill` file.
**Pre-conditions**:
- [ ] Branch `task/package-skill` created from `milestone/adding-mcp-hosts-skill`
- [ ] All 5 content files present in `__design__/skills/adding-mcp-hosts/`
**Success Gates**:
- `package_skill.py` exits 0
- `.skill` file contains exactly 5 files: SKILL.md + 4 references
**References**: Skill creator scripts at `~/.claude/plugins/cache/anthropic-agent-skills/example-skills/*/skills/skill-creator/scripts/`

---

## Step 1: Validate and package

**Goal**: Run the packaging script and verify the output.

**Implementation Logic**:
1. Locate the skill-creator scripts directory (glob for `**/skill-creator/scripts/package_skill.py` under `~/.claude/plugins/cache/`)
2. Create output directory: `mkdir -p __design__/skills/dist/`
3. Run packaging with PYTHONPATH set for the `quick_validate` import:
   ```bash
   PYTHONPATH=<scripts-dir> python <scripts-dir>/package_skill.py __design__/skills/adding-mcp-hosts/ __design__/skills/dist/
   ```
4. If validation fails:
   - Read the error message
   - Fix the issue in SKILL.md (most likely frontmatter problem)
   - Re-run packaging
5. Verify the produced `.skill` file:
   ```bash
   python -c "import zipfile; [print(f) for f in zipfile.ZipFile('__design__/skills/dist/adding-mcp-hosts.skill').namelist()]"
   ```
   Expected contents:
   - `adding-mcp-hosts/SKILL.md`
   - `adding-mcp-hosts/references/discovery-guide.md`
   - `adding-mcp-hosts/references/adapter-contract.md`
   - `adding-mcp-hosts/references/strategy-contract.md`
   - `adding-mcp-hosts/references/testing-fixtures.md`
6. Report the `.skill` file path to the user.

**Deliverables**: `__design__/skills/dist/adding-mcp-hosts.skill`
**Consistency Checks**: `package_skill.py` exit code 0; zip contains exactly 5 files
**Commit**: `chore(skill): package adding-mcp-hosts skill`
