# Hatch

![Hatch Logo](./docs/resources/images/Logo/hatch_wide_dark_bg_transparent.png)

Hatch is the package manager for the Cracking Shells ecosystem, designed specifically for managing Model Context Protocol (MCP) servers. It handles complex dependency resolution across system packages, Python packages, Docker containers, and other Hatch packages — all in isolated environments.

The canonical documentation is at `docs/index.md` and published at <https://hatch.readthedocs.io/en/latest/>.

## Quick start

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

Add a Hatch package and automatically configure it on Claude Desktop and Cursor:

```bash
hatch package add ./my_mcp_server --host claude-desktop,cursor
```

Configure an arbitrary MCP server (non-Hatch package) on Claude Desktop:

```bash
# Local server with command and arguments
hatch mcp configure my-weather-server --host claude-desktop \
  --command python --args weather_server.py \
  --env-var API_KEY=your_key

# Remote server with URL
hatch mcp configure api-server --host gemini \
  --httpUrl https://api.example.com \
  --header Authorization="Bearer token"
```

List configured servers and hosts:

```bash
hatch mcp list servers
hatch mcp list hosts --detailed
```

## Key features

- **Environment isolation**: Create separate workspaces for different projects
- **Multi-type dependencies**: Automatically resolve and install system packages, Python packages, Docker containers, and Hatch packages
- **MCP host configuration**: Deploy MCP servers to Claude Desktop, Cursor, VSCode, and other platforms
- **Package validation**: Ensure packages meet schema requirements before distribution
- **Development-focused**: Optimized for rapid development and testing of MCP server ecosystems

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
6. **Run tests**: `python -m pytest tests/`
7. **Create a pull request**

We use [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning. Use `npm run commit` for guided commit messages.

## Getting help

- Search existing [GitHub Issues](https://github.com/CrackingShells/Hatch/issues)
- Read [Troubleshooting](./docs/articles/users/Troubleshooting/ReportIssues.md) for common problems
- Check [Developer Onboarding](./docs/articles/devs/development_processes/developer_onboarding.md) for setup help

## License

This project is licensed under the GNU Affero General Public License v3 — see `LICENSE` for details.
