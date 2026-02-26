# Write Discovery Guide

**Goal**: Write the discovery workflow reference for researching a new host's MCP config requirements.
**Pre-conditions**:
- [ ] Branch `task/write-discovery-guide` created from `milestone/adding-mcp-hosts-skill`
**Success Gates**:
- `__design__/skills/adding-mcp-hosts/references/discovery-guide.md` exists
- Contains all 4 question categories, 3 escalation tiers, and Host Spec YAML template
**References**: [R02](../../__reports__/mcp_support_extension_skill/discovery-questionnaire.md) — Primary source for all content

---

## Step 1: Write discovery-guide.md

**Goal**: Create the reference file that guides an agent through host requirement discovery.

**Implementation Logic**:
Create `__design__/skills/adding-mcp-hosts/references/discovery-guide.md` (`mkdir -p` the path first). Derive content from R02. Structure:

1. **Tool priority ladder** — Ordered fallback chain:
   - Web search + fetch → find official MCP config docs for the target host
   - Context7 → query library documentation for the host
   - Codebase retrieval → check if host config format is already partially documented
   - User escalation → structured questionnaire (see below)
   For each level: what to search for, what "success" looks like, when to fall through.

2. **Structured questionnaire** — All 17 questions from R02 across 4 categories:
   - **Category A: Host Identity & Config Location** (A1-A5) — canonical name, config paths per platform, format (JSON/TOML), root key, detection method
   - **Category B: Field Support** (B1-B5) — transport types, type discriminator, host-specific fields, field name mappings, cross-host equivalents
   - **Category C: Validation & Serialization** (C1-C5) — transport mutual exclusion, field mutual exclusions, conditional requirements, structural transforms, preserved config sections
   - **Category D: Architectural Fit** (D1-D2) — variant of existing host, strategy family match
   Each question: ID, question text, why it matters, which file(s) it affects.

3. **Escalation tiers** — Progressive disclosure for user questioning:
   - **Tier 1 (Blocking)**: A1, A2, A3, A4, B1, B3 — cannot proceed without these
   - **Tier 2 (Complexity-triggered)**: B4, B5, C1, C4, C5 — ask if Tier 1 reveals non-standard behavior
   - **Tier 3 (Ambiguity-only)**: A5, B2, C2, C3, D1, D2 — ask only if reading existing code leaves answer unclear

4. **Existing host reference table** — All 8 current hosts (claude-desktop, claude-code, vscode, cursor, lmstudio, gemini, kiro, codex) with: format, root key, macOS path, detection method. Gives the agent comparison points.

5. **Host Spec YAML output format** — The structured artifact the discovery step produces. Include the full YAML template from R02 §6 with all fields annotated by question ID.

**Deliverables**: `__design__/skills/adding-mcp-hosts/references/discovery-guide.md` (~150-200 lines)
**Consistency Checks**: File contains sections for all 4 categories, all 3 tiers, reference table, and YAML template
**Commit**: `feat(skill): add discovery guide reference`
