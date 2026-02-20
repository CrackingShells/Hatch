# 02: Create Environment

---
**Concepts covered:**

- What Hatch environments are and how they work
- Python environment integration via conda/mamba
- Environment metadata and configuration storage

**Skills you will practice:**

- Creating a new Hatch environment
- Creating environments with Python integration
- Managing environment options and configurations

---

This article covers creating your first Hatch environment for managing MCP server packages.

## Step 1: Create a Basic Environment

Create a simple Hatch environment without Python integration:

```bash
hatch env create my_first_env --description "My first Hatch environment" --no-python
```

This creates an environment that can manage Hatch packages but doesn't include a Python environment.

> [!NOTE]
> Environment names must be alphanumeric and can contain underscores.

## Step 2: Create an Environment with Python Integration

For most use cases, you'll want Python integration for running MCP servers:

```bash
hatch env create my_python_env --description "Environment with Python support" --python-version 3.11
```

This command:

- Creates a Hatch environment named `my_python_env`
- Sets up a Python 3.11 environment using conda/mamba
- Installs the hatch_mcp_server wrapper by default

### Understanding the Options

- `--python-version` - Specifies the Python version (e.g., 3.11, 3.12)
- `--no-python` - Skips Python environment creation
- `--no-hatch-mcp-server` - Skips installation of the hatch_mcp_server wrapper
- `--hatch_mcp_server_tag` - Specifies a git tag/branch for the wrapper (e.g., 'dev', 'v0.1.0')

## Step 3: Verify Environment Creation

List your environments to confirm they were created:

```bash
hatch env list
```

You should see output similar to:

```txt
Environments:
  Name             Python        Packages
  ───────────────────────────────────────
  * my_first_env   -                    0
    my_python_env  3.11.5               0
```

**Key Details**:
- Current environment marked with `*` prefix
- Python column shows version or `-` if no Python environment
- Packages column shows count of installed packages

**Exercise:**
Initialize a Python environment inside `my_first_env`. Try both initializing without `hatch_mcp_server` wrapper and adding it afterwards. Hint: Use `hatch env python --help` to explore available Python subcommands and flags.

<details>
<summary>Solution</summary>

```bash

# Initialize a Python environment inside my_first_env
hatch env python init --hatch_env my_first_env --no-hatch-mcp-server

# Verify Python environment
hatch env python info --hatch_env my_first_env # hatch_mcp_server should not appear in the list of packages

# Add hatch_mcp_server wrapper
hatch env python add-hatch-mcp --hatch_env my_first_env

# Verify again
hatch env python info --hatch_env my_first_env # hatch_mcp_server should now appear in the list of packages
```
</details>

In most use cases, you'll want to create environments with Python integration and the hatch_mcp_server wrapper. However, Hatch provides flexibility to customize your environments as needed.

> Previous: [Installation](01-installation.md)
> Next: [Install Package](03-install-package.md)
