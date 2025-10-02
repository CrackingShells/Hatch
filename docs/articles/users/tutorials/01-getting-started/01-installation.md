# 01: Installation

---
**Concepts covered:**

- How Hatch is distributed and installed
- CLI structure and available commands
- Configuration directories and cache management

**Skills you will practice:**

- Installing Hatch using pip
- Verifying the installation
- Exploring CLI help and available commands

---

This article covers the installation of Hatch, a package manager for Model Context Protocol (MCP) servers.

## Step 1: Install Hatch

1. Ensure you have Python 3.12 or later installed on your system.
2. Install Hatch using pip:

   ```bash
   git clone https://github.com/CrackingShells/Hatch.git
   cd Hatch
   pip install -e .
   ```

3. Verify the installation by checking the version:

   ```bash
   hatch --version
   ```

   You should see output like `hatch 0.6.1`. You can also view available commands:

   ```bash
   hatch --help
   ```

## Step 2: Understand the CLI Structure

Hatch provides several command groups:

- `hatch create` - Create new package templates
- `hatch validate` - Validate package structures
- `hatch env` - Environment management commands
- `hatch package` - Package management commands

### Global Configuration Options

The CLI accepts the following global configuration options:

- `--envs-dir` - Directory to store environments (default: `~/.hatch/envs`)
- `--cache-ttl` - Cache TTL in seconds (default: 86400 seconds = 1 day)
- `--cache-dir` - Directory to store cached packages (default: `~/.hatch/cache`)

## Step 3: Explore Available Commands

View detailed help for specific command groups:

```bash
# Environment management
hatch env --help

# Package management  
hatch package --help
```

**Exercise:**
Explore the help output for the `create` command. What options are available for each?

<details>
<summary>Solution</summary>

```bash
# positional arguments:
#   name                  Package name
# 
# options:
#   -h, --help            show this help message and exit
#   --dir DIR, -d DIR     Target directory (default: current directory)
#   --description DESCRIPTION, -D DESCRIPTION
#                         Package description
```
</details>

> Next: [Create Environment](02-create-env.md)
