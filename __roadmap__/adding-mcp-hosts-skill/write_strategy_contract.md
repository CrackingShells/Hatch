# Write Strategy Contract

**Goal**: Document the strategy interface contract for implementing host file I/O.
**Pre-conditions**:
- [ ] Branch `task/write-strategy-contract` created from `milestone/adding-mcp-hosts-skill`
**Success Gates**:
- `__design__/skills/adding-mcp-hosts/references/strategy-contract.md` exists
- Documents all 5 abstract methods, decorator pattern, and all 3 strategy families
**References**: Codebase `hatch/mcp_host_config/strategies.py` — all existing strategy implementations

---

## Step 1: Write strategy-contract.md

**Goal**: Create the reference file documenting everything an agent needs to implement a host strategy.

**Implementation Logic**:
Create `__design__/skills/adding-mcp-hosts/references/strategy-contract.md` (`mkdir -p` the path first). Derive from codebase inspection of `hatch/mcp_host_config/strategies.py`. Read the file to extract exact patterns for all existing strategies.

Structure:

1. **MCPHostStrategy interface** — Abstract methods to implement:
   - `get_config_path() → Path` — platform-specific config file location (`sys.platform` dispatch)
   - `get_config_key() → str` — root key for MCP servers in config (e.g., `"mcpServers"`, `"servers"`)
   - `read_configuration() → dict` — read and parse the config file
   - `write_configuration(config: dict)` — write config, preserving non-MCP sections if applicable
   - `is_host_available() → bool` — detect whether host is installed on the system
   Include lean method signature template.

2. **@register_host_strategy decorator** — Usage: `@register_host_strategy(MCPHostType.YOUR_HOST)`. Explain that this auto-registers the strategy so `HostConfigurationManager` can discover it by host type. File: `hatch/mcp_host_config/strategies.py`.

3. **Strategy families** — Decision tree for base class selection:
   - `ClaudeHostStrategy` → if host shares Claude's JSON format with settings preservation. Members: `ClaudeDesktopStrategy`, `ClaudeCodeStrategy`. Provides `_preserve_claude_settings()`.
   - `CursorBasedHostStrategy` → if host shares Cursor's simple JSON format (flat JSON, `mcpServers` key). Members: `CursorHostStrategy`, `LMStudioHostStrategy`.
   - `MCPHostStrategy` (standalone) → if host has unique I/O needs. Members: `VSCodeHostStrategy`, `GeminiHostStrategy`, `KiroHostStrategy`, `CodexHostStrategy`.

4. **Platform path patterns** — Common patterns from existing strategies:
   - Simple home-relative: `Path.home() / ".host-dir" / "config.json"` (Cursor, LM Studio, Gemini, Kiro, Codex)
   - macOS Application Support: `Path.home() / "Library" / "Application Support" / "AppName" / "config.json"` (Claude Desktop, VSCode)
   - XDG on Linux: `Path.home() / ".config" / "host-dir" / "config.json"` (VSCode)

5. **Config preservation** — Read-before-write pattern for files with non-MCP sections:
   - Codex: preserves `[features]` and other TOML sections
   - Gemini: preserves other keys in `settings.json`
   - Claude Desktop: preserves non-mcpServers keys
   Describe the merge pattern: read existing → update MCP section → write back.

**Deliverables**: `__design__/skills/adding-mcp-hosts/references/strategy-contract.md` (~80-120 lines)
**Consistency Checks**: File documents all 5 abstract methods, decorator, 3 families with members, path patterns, preservation pattern
**Commit**: `feat(skill): add strategy contract reference`
