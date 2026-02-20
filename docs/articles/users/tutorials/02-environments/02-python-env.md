# 02: Python Environment Management

---
**Concepts covered:**

- Advanced Python environment operations
- Python environment initialization and configuration
- Environment diagnostics and troubleshooting
- Hatch MCP server wrapper management

**Skills you will practice:**

- Initializing Python environments in existing Hatch environments
- Viewing detailed Python environment information
- Managing the hatch_mcp_server wrapper
- Launching Python shells within environments

---

This article covers advanced Python environment management within Hatch environments.

## Step 1: Initialize Python Environment

Add a Python environment to an existing Hatch environment:

```bash
# Initialize in current environment
hatch env python init --python-version 3.11

# Initialize in specific environment
hatch env python init --hatch_env my_env --python-version 3.12 --force
```

### Python Initialization Options

- `--hatch_env` - Target Hatch environment (defaults to current)
- `--python-version` - Python version (e.g., 3.11, 3.12)
- `--force` - Force recreation if Python environment exists
- `--no-hatch-mcp-server` - Skip hatch_mcp_server wrapper installation
- `--hatch_mcp_server_tag` - Git tag/branch for wrapper (e.g., 'dev', 'v0.1.0')

## Step 2: View Python Environment Information

Get detailed information about a Python environment:

```bash
# Basic info for current environment
hatch env python info

# Detailed info for specific environment
hatch env python info --hatch_env my_env --detailed
```

Example output:
```
Python environment info for 'my_env':
  Status: Active
  Python executable: /path/to/conda/envs/my_env/bin/python
  Python version: 3.11.9
  Conda environment: my_env
  Environment path: /path/to/conda/envs/my_env
  Created: 2025-08-24T10:30:00
  Package count: 25
  Packages:
    - fastmcp (1.0.0)
    - mcp (1.0.0)
    - hatch-mcp-server (0.1.0)

Diagnostics:
  conda_available: true
  mamba_available: true
  environment_exists: true
  python_executable_valid: true
```

## Step 3: Manage Hatch MCP Server Wrapper

The hatch_mcp_server wrapper provides integration between Hatch packages and MCP servers.

Add the wrapper to an environment:
```bash
hatch env python add-hatch-mcp --hatch_env my_env --tag v0.1.0
```

The wrapper is typically installed automatically when creating Python environments, but you can add it manually or update to specific versions.

## Step 4: Launch Python Shell

Access the Python environment directly:

```bash
# Interactive shell
hatch env python shell --hatch_env my_env

# Run specific command
hatch env python shell --hatch_env my_env --cmd "import sys; print(sys.version)"
```

## Step 5: Remove Python Environment

Remove only the Python environment while keeping the Hatch environment:

```bash
# With confirmation prompt
hatch env python remove --hatch_env my_env

# Force removal without prompt
hatch env python remove --hatch_env my_env --force
```

This allows you to remove Python dependencies without affecting Hatch package installations.

## Step 6: Troubleshooting Python Environments

Use the `--detailed` flag to diagnose issues:

```bash
hatch env python info --detailed
```

Common diagnostic information includes:

- **conda_available** - Whether conda is installed and accessible
- **manager_executable** - The path to conda/mamba executable that will be used
- **environment_path** - The path to the conda environment
- **python_executable** - The path to the Python executable used to run the MCP servers in the Hatch! packages.

**Exercise:**

- Create a Hatch environment without Python, then add Python support afterwards. View the detailed information before and after Python initialization.
- Remove the Python environment and verify it's cleanly removed while keeping the Hatch environment intact.
- Remove the Hatch environment and verify it's cleanly removed.

<details>
<summary>Solution</summary>

```bash
# Create environment without Python
hatch env create test_python --no-python --description "Test Python addition"

# Check info (should show no Python)
hatch env python info --hatch_env test_python --detailed

# Add Python environment
hatch env python init --hatch_env test_python --python-version 3.11

# Check info again (should show Python details)
hatch env python info --hatch_env test_python --detailed

# Remove Python environment
hatch env python remove --hatch_env test_python --force

# Check info (should show no Python again)
hatch env python info --hatch_env test_python --detailed

# Remove Hatch environment
hatch env remove test_python

# Verify removal
hatch env list
```

</details>

> Previous: [Manage Environments](01-manage-envs.md)
> Next: [Checkpoint](03-checkpoint.md)
