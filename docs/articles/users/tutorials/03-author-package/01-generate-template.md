# 01: Generate Template

---
**Concepts covered:**

- Package template structure and generated files
- Template generator functionality and default configurations
- Package naming conventions and directory organization

**Skills you will practice:**

- Creating new package templates using the CLI
- Understanding generated file purposes and structure
- Customizing template generation with descriptions and directories

---

This article covers generating new Hatch package templates to start developing MCP server packages.

## Step 1: Generate Basic Template

Create a new package template with the default settings:

```bash
hatch create my_new_package
```

This generates a package directory `my_new_package/` in the current directory with the following structure:

```txt
my_new_package/
├── __init__.py
├── mcp_server.py
├── hatch_mcp_server_entry.py
├── hatch_metadata.json
└── README.md
```

## Step 2: Customize Template Generation

Generate a template with custom options:

```bash
hatch create advanced-package --dir ./packages --description "An advanced MCP server package"
```

### Template Generation Options

- `--dir` / `-d` - Target directory (default: current directory)
- `--description` / `-D` - Package description (appears in metadata and README)

## Step 3: Understanding Generated Files

Let's examine each generated file:

### `__init__.py`

```python
# Hatch package initialization
```

Standard Python package initialization file. It is empty by default; there is not much of a reason in the case of a hatch package to put anything in this file afterward. Indeed, a hatch package wraps an MCP server which purpose it not to expose any public API but only to provide a set of functionalities for LLMs. Hence, `__init__.py` exists only for python imports within the package.

### `mcp_server.py`

Contains the core MCP server implementation using FastMCP:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my_new_package", log_level="WARNING")

@mcp.tool()
def example_tool(param: str) -> str:
    """Example tool function.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result."""

    return f"Processed: {param}"

if __name__ == "__main__":
    mcp.run()
```

This is where the magic stems from. You can add as many tools as you want by adding more functions decorated with `@mcp.tool()`. The tools are the actual functions that will be called by the LLMs. The tools are defined by the function signature and its docstring. **The docstring is used by the LLMs to understand what the tool does and how to use it, thus it is crucial to write it correctly.**
You will likely spend most of your time in this file.

### `hatch_mcp_server_entry.py`

Wraps the MCP server for Hatch integration:

```python
from hatch_mcp_server import HatchMCP
from mcp_server import mcp

hatch_mcp = HatchMCP("my_new_package",
                     fast_mcp=mcp,
                     origin_citation="Origin citation for my_new_package",
                     mcp_citation="MCP citation for my_new_package")

if __name__ == "__main__":
    hatch_mcp.server.run()
```

`HatchMCP`can be found in another [repository](https://github.com/CrackingShells/hatch-mcp-server) of the __Cracking Shells__ organization. Its purpose is to expose MCP resources by default to provide support for scientific citation of the underlying MCP server and its tools. We believe this is critical for the attribution and transparency in the context of massive tools usage by autonomous systems such as so-called scientific agents.

That being the case, this wrapper is currently only used within the software suite of the __Cracking Shells__ organization (typically [Hatchling](https://github.com/CrackingShells/Hatchling)).

### `hatch_metadata.json`

Contains package metadata following the Hatch schema (see next article for details).

### `README.md`

Basic documentation template with package description and tool listing.

We strongly recommend that you include in this file typical information about the package, its tools, and how to use them. In particular, despite the stochastic nature of the LLMs, what typical prompts triggers tool usage; and what is the typical output given by an LLM.

## Step 4: Package Naming Guidelines

Follow these conventions for package names:

- Use lowercase letters, numbers, and underscores only
- Start with a letter
- Use descriptive, meaningful names
- Avoid conflicts with existing packages

**Exercise:**
Generate three different packages: one with default settings, one in a custom directory, and one with a detailed description. Examine the differences in the generated files.

<details>
<summary>Solution</summary>

```bash
# Default package
hatch create basic_package

# Custom directory
hatch create custom_package --dir ./my-packages

# With description
hatch create described-package --description "A package that demonstrates detailed descriptions"

# Examine the differences
cat basic-package/hatch_metadata.json
cat my-packages/custom_package/hatch_metadata.json
cat described-package/hatch_metadata.json
```

The description should appear in the metadata and README files.
</details>

> Previous: [Environment Management Checkpoint](../02-environments/03-checkpoint.md)
> Next: [Implement Functionality](02-implement-functionality.md)
