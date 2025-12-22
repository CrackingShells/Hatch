# Hatch

![Hatch Logo](https://raw.githubusercontent.com/CrackingShells/Hatch/refs/heads/main/docs/resources/images/Logo/hatch_wide_dark_bg_transparent.png)

## Introduction

Hatch is the package manager for managing Model Context Protocol (MCP) servers with environment isolation, multi-type dependency resolution, and multi-host deployment. Deploy MCP servers to Claude Desktop, VS Code, Cursor, Kiro, Codex, and other platforms with automatic dependency management.

The canonical documentation is at `docs/index.md` and published at <https://hatch.readthedocs.io/en/latest/>.

## Key Features

- **Environment Isolation** — Create separate, isolated workspaces for different projects without conflicts
- **Multi-Type Dependency Resolution** — Automatically resolve and install system packages, Python packages, Docker containers, and Hatch packages
- **Multi-Host Deployment** — Configure MCP servers on multiple host platforms
- **Package Validation** — Ensure packages meet schema requirements before distribution
- **Development-Focused** — Optimized for rapid development and testing of MCP server ecosystems

## Supported MCP Hosts

Hatch supports deployment to the following MCP host platforms:

- **Claude Desktop** — Anthropic's desktop application for Claude with native MCP support
- **Claude Code** — Claude integration for VS Code with MCP capabilities
- **VS Code** — Visual Studio Code with the MCP extension for tool integration
- **Cursor** — AI-first code editor with built-in MCP server support
- **Kiro** — Kiro IDE with MCP support
- **Codex** — OpenAI Codex with MCP server configuration support
- **LM Studio** — Local LLM inference platform with MCP server integration
- **Google Gemini CLI** — Command-line interface for Google's Gemini model with MCP support

## Quick Start

### Install from PyPI

```bash
pip install hatch-xclam
```

Verify installation:

```bash
hatch --version
```

### Install from source

```bash
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch
pip install -e .
```

### Create your first environment and *Hatch!* MCP server package

```bash
# Create an isolated environment
hatch env create my_project

# Switch to it
hatch env use my_project

# Create a package template
hatch create my_mcp_server --description "My MCP server"

# Validate the package
hatch validate ./my_mcp_server
```

### Deploy MCP servers to your tools

**Package-First Deployment (Recommended)** — Add a Hatch package and automatically configure it on Claude Desktop and Cursor:

```bash
hatch package add ./my_mcp_server --host claude-desktop,cursor
```

**Direct Configuration (Advanced)** — Configure arbitrary MCP servers on your hosts:

```bash
# Remote server example: GitHub MCP Server with authentication
export GIT_PAT_TOKEN=your_github_personal_access_token
hatch mcp configure github-mcp --host gemini \
  --httpUrl https://api.github.com/mcp \
  --header Authorization="Bearer $GIT_PAT_TOKEN"

# Local server example: Context7 via npx
hatch mcp configure context7 --host vscode \
  --command npx --args "-y @upstash/context7-mcp"
```

## Documentation

- **[Full Documentation](https://hatch.readthedocs.io/en/latest/)** — Complete reference and guides
- **[Getting Started](./docs/articles/users/GettingStarted.md)** — Quick start for users
- **[CLI Reference](./docs/articles/users/CLIReference.md)** — All commands and options
- **[Tutorials](./docs/articles/users/tutorials/)** — Step-by-step guides from installation to package authoring
- **[MCP Host Configuration](./docs/articles/users/MCPHostConfiguration.md)** — Deploy to multiple platforms
- **[Developer Docs](./docs/articles/devs/)** — Architecture, implementation guides, and contribution guidelines
- **[Troubleshooting](./docs/articles/users/Troubleshooting/ReportIssues.md)** — Common issues and solutions

## Contributing

We welcome contributions! See the [How to Contribute](./docs/articles/devs/contribution_guides/how_to_contribute.md) guide for details.

### Quick start for developers

1. **Fork and clone** the repository
2. **Install dependencies**: `pip install -e .` and `npm install`
3. **Create a feature branch**: `git checkout -b feat/your-feature`
4. **Make changes** and add tests
5. **Use conventional commits**: `npm run commit` for guided commits
6. **Run tests**: `wobble`
7. **Create a pull request**

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning. Use `npm run commit` for guided commit messages.

## Getting Help

- Search existing [GitHub Issues](https://github.com/CrackingShells/Hatch/issues)
- Read [Troubleshooting](./docs/articles/users/Troubleshooting/ReportIssues.md) for common problems
- Check [Developer Onboarding](./docs/articles/devs/development_processes/developer_onboarding.md) for setup help

## License

This project is licensed under the GNU Affero General Public License v3 — see `LICENSE` for details.
