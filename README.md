# Hatch

![Hatch Logo](https://raw.githubusercontent.com/CrackingShells/Hatch/refs/heads/main/docs/resources/images/Logo/hatch_wide_dark_bg_transparent.png)

Hatch is a CLI tool for configuring MCP servers across AI host platforms. Adding a server to Claude Desktop, Cursor, VS Code, and others normally means editing separate JSON config files in different locations. Hatch does it from one command.

It also has a package system for managing MCP servers with dependency isolation, though that part is still being developed — see [Getting Started](./docs/articles/users/GettingStarted.md) for the current state.

**Current status:** suitable for development and trusted environments. Not hardened for production or multi-tenant use yet — see [Security and Trust](./docs/articles/users/SecurityAndTrust.md).

## What it does

- Configure MCP servers on one or more AI host platforms at once
- Discover which host platforms are installed on your machine
- List and inspect server registrations across all your tools
- Manage MCP server packages with dependency isolation (system, Python, Docker)

## Supported MCP Hosts

Claude Desktop, Claude Code, VS Code, Cursor, Kiro, Codex, LM Studio, Google Gemini CLI, Mistral Vibe, OpenCode, Augment Code (Auggie CLI and Intent)

## Install

```bash
pip install hatch-xclam
```

Verify:

```bash
hatch --version
```

Or install from source:

```bash
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch
pip install -e .
```

## Usage

### Configure MCP servers on your hosts

```bash
# Local server via npx — register it on VS Code
hatch mcp configure context7 --host vscode \
  --command npx --args "-y @upstash/context7-mcp"

# Remote server with an auth header — register it on Gemini CLI
export GIT_PAT_TOKEN=your_github_personal_access_token
hatch mcp configure github-mcp --host gemini \
  --httpUrl https://api.github.com/mcp \
  --header Authorization="Bearer $GIT_PAT_TOKEN"

# Register the same server on multiple hosts using sync
hatch mcp configure my-server --host claude-desktop \
  --command python --args "-m my_server"
hatch mcp sync --from-host claude-desktop --to-host cursor,vscode
```

### Inspect what is configured

```bash
# See all servers across all hosts
hatch mcp list servers

# Filter servers by name
hatch mcp list servers weather

# See all hosts a specific server is registered on
hatch mcp show servers context7

# Detect which MCP host platforms are installed
hatch mcp discover hosts
```

### Package management (in development)

The package system lets you install MCP servers with automatic dependency resolution and environment isolation. It is functional but being reworked for better integration with MCP registries.

```bash
hatch env create my_project
hatch env use my_project
hatch package add ./my_mcp_server
```

## Documentation

- **[Full Documentation](https://hatch.readthedocs.io/en/latest/)**
- **[Getting Started](./docs/articles/users/GettingStarted.md)**
- **[CLI Reference](./docs/articles/users/CLIReference.md)**
- **[MCP Host Configuration](./docs/articles/users/MCPHostConfiguration.md)**
- **[Tutorials](./docs/articles/users/tutorials/)**
- **[Troubleshooting](./docs/articles/users/Troubleshooting/ReportIssues.md)**

## Contributing

We welcome contributions. See [How to Contribute](./docs/articles/devs/contribution_guides/how_to_contribute.md) for details.

Quick setup:

1. Fork and clone the repository
2. Install dependencies: `pip install -e .` and `npm install`
3. Create a feature branch: `git checkout -b feat/your-feature`
4. Make changes and add tests
5. Use conventional commits: `npm run commit`
6. Run tests: `wobble`
7. Open a pull request

## License

GNU Affero General Public License v3 — see `LICENSE` for details.
