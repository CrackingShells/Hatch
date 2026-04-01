# Update Extension Guide

**Goal**: Bring `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md` into alignment with the current codebase.
**Pre-conditions**:
- [ ] Branch `task/update-extension-guide` created from `milestone/mcp-docs-refresh`
**Success Gates**:
- Step 2 adapter template uses `validate_filtered()` in the `serialize()` method (not `validate()`)
- Step 3 strategy template includes `@register_host_strategy` decorator and documents `MCPHostStrategy` interface
- Step 4 documents the actual test data fixture requirements (`canonical_configs.json`, `host_registry.py`)
- "Testing Your Implementation" section cross-references the architecture doc's testing section
**References**: [R01 Gap Analysis](../../__reports__/mcp-docs-refresh/docs-vs-codebase-gap-analysis.md) — findings 1b, 2d

---

## Step 1: Fix Step 2 adapter template to use validate_filtered()

**Goal**: Replace the deprecated `validate()` pattern in the adapter template with the current `validate_filtered()` contract.

**Implementation Logic**:

1. In the Step 2 template code block, change the `serialize()` method from calling `self.validate(config)` to calling `self.filter_fields(config)` then `self.validate_filtered(filtered)` then returning the filtered result. This matches the actual pattern used by all current adapters.
2. Update the `validate()` method stub to include a docstring marking it as deprecated with a pointer to `validate_filtered()`. Keep it as a pass-through since it's still abstract in `BaseAdapter`.
3. Add a `validate_filtered()` method to the template with the transport validation logic that's currently only in `validate()`.
4. Update the "Interface" table at the top of the guide: change `validate()` to `validate_filtered()` in the Adapter row, or list both with a deprecation note.
5. In "Common Patterns" section, update the "Multiple Transport Support" and "Strict Single Transport" examples to use `validate_filtered(self, filtered)` signatures (checking `"command" in filtered` instead of `config.command is not None`).
6. In "Field Mappings (Optional)" section, update the `serialize()` example to use `validate_filtered()`.

**Deliverables**: Updated Step 2 template, updated Common Patterns section, updated Field Mappings section in `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md`
**Consistency Checks**: Confirm every adapter in `hatch/mcp_host_config/adapters/` uses `validate_filtered()` inside `serialize()` (expected: PASS)
**Commit**: `docs(mcp): update extension guide adapter template to use validate_filtered()`

---

## Step 2: Update Step 3 strategy template with registration decorator

**Goal**: Document the `@register_host_strategy` decorator and the `MCPHostStrategy` base class interface in the strategy template.

**Implementation Logic**:

1. The Step 3 template already shows `@register_host_strategy(MCPHostType.YOUR_HOST)` — verify it's correct and add a brief explanation of what the decorator does (registers the strategy in a global dict so `get_strategy_for_host()` can look it up).
2. Add a brief list of `MCPHostStrategy` methods that can be overridden vs inherited. Currently the template shows `get_config_path()`, `is_host_available()`, `get_config_key()` but doesn't mention `read_configuration()`, `write_configuration()`, or `validate_server_config()`. Add a table showing which methods typically need overriding vs which inherit well from base/family classes.
3. Cross-reference the architecture doc's "MCPHostStrategy Interface" subsection.

**Deliverables**: Updated Step 3 section in `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md`
**Consistency Checks**: Verify the decorator name and signature match `hatch/mcp_host_config/strategies.py` (expected: PASS)
**Commit**: `docs(mcp): update extension guide strategy template with interface documentation`

---

## Step 3: Rewrite Step 4 and Testing Your Implementation section

**Goal**: Replace the current testing guidance with accurate documentation of the data-driven testing infrastructure requirements.

**Implementation Logic**:

1. Rewrite Step 4 to explain what's actually needed when adding a new host:
   - **a)** Add a fixture entry to `tests/test_data/mcp_adapters/canonical_configs.json` — show the JSON structure (host name key, field-name-to-value mapping using host-native field names).
   - **b)** Add the host's field set to `FIELD_SETS` in `tests/test_data/mcp_adapters/host_registry.py` — one line mapping host name to the `fields.py` constant.
   - **c)** If the host uses field mappings (like Codex), add reverse mappings to `REVERSE_MAPPINGS` in `host_registry.py`.
   - **d)** Explain that the generator functions (`generate_sync_test_cases`, `generate_validation_test_cases`, `generate_unsupported_field_test_cases`) will automatically pick up the new host and generate parameterized test cases. No changes to test files themselves.
2. Remove the misleading unit test template (Step 4 currently shows a `TestYourHostAdapter` class with handwritten test methods). Replace with a note that unit tests for adapter protocol compliance, field filtering, and cross-host sync are all auto-generated. Only add bespoke unit tests if the adapter has unusual behavior (e.g., complex field transformations).
3. Update the "Testing Your Implementation" section to cross-reference the architecture doc's testing section. Replace the "Test Categories" table with a table showing what's auto-generated vs what needs manual tests.
4. Update the "Test File Location" tree to include `tests/test_data/mcp_adapters/` and show the actual regression test directory.
5. Fix the "zero test code changes" claim in both the extension guide and any cross-references. State the accurate requirement: fixture data updates in `canonical_configs.json` and `host_registry.py`, but zero changes to test functions.

**Deliverables**: Rewritten Step 4 section, rewritten "Testing Your Implementation" section, updated test file tree in `docs/articles/devs/implementation_guides/mcp_host_configuration_extension.md`
**Consistency Checks**: Follow the documented steps mentally for a hypothetical new host and verify each instruction points to real files that exist in the codebase (expected: PASS)
**Commit**: `docs(mcp): rewrite extension guide testing section with data-driven infrastructure`
