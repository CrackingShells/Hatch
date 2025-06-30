This article is about:
- Implementing the MCP server logic in a Hatch package

You will learn about:
- Editing server.py
- Updating package metadata
- Adding Python dependencies
- Writing tools using decorators
- Logging and error handling

This article explains how to implement the `server.py` file for your MCP server, using the `arithmetic_pkg` as an example.

## Overview

The `server.py` file defines the main logic of your MCP server. It uses the `HatchMCP` class from `hatchling` to register tools (functions) that the server exposes.

## Example Structure

```python
from hatchling import HatchMCP

hatch_mcp = HatchMCP("ArithmeticTools",
    origin_citation="Your Name, 'Origin: Example MCP Server for Hatch!', April 2025",
    mcp_citation="Your Name, 'MCP: Example Arithmetic Tools for Hatch!', April 2025"
)

@hatch_mcp.server.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together.
    Args:
        a (float): First number.
        b (float): Second number.
    Returns:
        float: Sum of a and b.
    """
    hatch_mcp.logger.info(f"Adding {a} + {b}")
    return a + b
```

## Key Points

- **Docstrings**: The quality of the docstring is critical as it is used by the LLMs to understand what the tool does.
- **Initialization**: Create a `HatchMCP` instance with a name and citation strings.
- **Tool Registration**: Use `@hatch_mcp.server.tool()` to register a function as a tool.
- **Function Signatures**: Use type annotations for arguments and return values.
- **Logging**: Use `hatch_mcp.logger` for info and error messages.
- **Error Handling**: Raise exceptions (e.g., `ValueError`) for invalid input.

## Example: Division Tool with Error Handling

```python
@hatch_mcp.server.tool()
def divide(a: float, b: float) -> float:
    """Divide first number by second number.
    Args:
        a (float): First number (dividend).
        b (float): Second number (divisor).
    Returns:
        float: Quotient (a / b).
    """
    if b == 0:
        hatch_mcp.logger.error("Division by zero attempted")
        raise ValueError("Cannot divide by zero")
    hatch_mcp.logger.info(f"Dividing {a} / {b}")
    return a / b
```

- Always check for invalid input and log errors.

## Adding Python Dependencies

To add a Python dependency, such as `numpy`, update the `hatch_metadata.json` file in your package directory. Add a section like this under `dependencies`:

```json
"dependencies": {
  "python": [
    {
      "name": "numpy",
      "version_constraint": ">=1.24.0",
      "package_manager": "pip"
    }
  ]
}
```

This follows the [Hatch package metadata schema](https://github.com/CrackingShells/Hatch-Schemas/tree/main/package/v1.2.0).

## Next Steps

- Add more tools as needed, following the same pattern.
- Document each tool with clear docstrings.
- Test your server by running it locally and verifying its behavior.
- Follow deployment instructions in your package documentation.
