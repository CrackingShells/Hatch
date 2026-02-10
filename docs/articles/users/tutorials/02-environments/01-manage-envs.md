# 01: Manage Environments

---
**Concepts covered:**

- Environment lifecycle management
- Environment switching and current environment tracking
- Environment metadata and descriptions

**Skills you will practice:**

- Listing and inspecting environments
- Switching between environments
- Removing environments when no longer needed

---

## Understanding Hatch Environments

Hatch environments provide isolated workspaces for different MCP server collections. Each environment can have:

- Its own package installations
- Optional Python environment (via conda/mamba)
- Independent configuration and state

**Limitation Note**: Multiple `hatch` instances modifying environments simultaneously may cause conflicts. Use one instance per workspace for reliability.

## Step 1: List All Environments

View all available environments with their details:

```bash
hatch env list
```

Example output:

```txt
Environments:
  Name             Python        Packages
  ───────────────────────────────────────
  * my_python_env  3.11.9               0
    my_first_env   3.13.5               0
```

**Key Details**:
- The `*` indicates the current active environment
- Python column shows version number (or `-` if no Python environment)
- Packages column shows count of installed packages

## Step 2: Switch Between Environments

Change your current working environment:

```bash
hatch env use my_first_env
```

Expected output:

```txt
[SET] Current environment → 'my_first_env'
```

Verify the switch:

```bash
hatch env current
```

This command shows:

```
Current environment: my_first_env
```

## Step 3: Remove Environments

Remove an environment you no longer need:

```bash
hatch env remove my_first_env
```

Expected output:

```txt
[REMOVE] Environment 'my_first_env'

Proceed? [y/N]: y
[REMOVED] Environment 'my_first_env'
```

**Important:** This removes both the Hatch environment and any associated Python environment. Make sure to back up any important data first.

**Note**: The command will prompt for confirmation unless you use `--auto-approve`.

## Step 4: Understanding Environment Information

The `env list` command displays environments in a table format with:

- **Name column** - Environment name with `*` marker for current environment
- **Python column** - Python version (or `-` if no Python environment)
- **Packages column** - Count of installed packages

For detailed information about a specific environment, including descriptions and full package details, use:

```bash
hatch env show <environment_name>
```

This will display:
- Environment description and creation date
- Python environment details (version, executable path, conda environment name)
- Complete list of installed packages with versions and deployment status

## Step 5: Managing Multiple Environments

You can maintain multiple environments for different projects:

```bash
# Project-specific environments
hatch env create project_a --description "Environment for Project A" --python-version 3.11
hatch env create project_b --description "Environment for Project B" --python-version 3.12

# Switch between them as needed
hatch env use project_a
# Work on project A...

hatch env use project_b
# Work on project B...
```

**Exercise:**
Create three environments with different Python versions, switch between them, and observe how the current environment changes. Then remove one of the environments.

<details>
<summary>Solution</summary>

```bash
# Create environments
hatch env create env_311 --python-version 3.11 --description "Python 3.11 environment"
hatch env create env_312 --python-version 3.12 --description "Python 3.12 environment"
hatch env create env_313 --python-version 3.13 --description "Python 3.13 environment"

# Switch between them
hatch env use env_311
hatch env current  # Should show env_311

hatch env use env_312
hatch env current  # Should show env_312

# List to see all three
hatch env list

# Remove one
hatch env remove env_313
```

</details>

> Previous: [Getting Started Checkpoint](../01-getting-started/04-checkpoint.md)
> Next: [Python Environment Management](02-python-env.md)
