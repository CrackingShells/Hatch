# 02: Implement Functionality

---
**Concepts covered:**

- Transforming template code into functional MCP server implementation
- Adding Python dependencies and imports to MCP servers
- Implementing multiple tools with proper type hints and documentation
- Error handling and validation in MCP tool functions
- Testing MCP server functionality before packaging

**Skills you will practice:**

- Writing MCP tool functions with FastMCP decorators
- Adding external dependencies like numpy to enhance functionality
- Creating comprehensive docstrings for LLM tool understanding
- Implementing error handling and input validation
- Testing MCP server tools locally before installation

---

This article covers transforming the generated template into a functional MCP server by implementing actual tools, similar to the arithmetic package example.

## Step 1: Plan Your Implementation

Before writing code, plan what your MCP server will do. For this tutorial, we'll implement an arithmetic server that provides:

- Basic arithmetic operations (add, subtract, multiply, divide)
- Advanced operations using numpy (power function)
- Proper error handling (division by zero)
- Clear documentation for LLM understanding

## Step 2: Implement Core MCP Server Logic

Replace the template content in `mcp_server.py` with functional arithmetic tools:

```python
import numpy as np
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ArithmeticTools", log_level="WARNING")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together.

    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: Sum of a and b.
    """
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract second number from first number.

    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: Difference (a - b).
    """
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together.

    Args:
        a (float): First number.
        b (float): Second number.

    Returns:
        float: Product of a and b.
    """
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide first number by second number.

    Args:
        a (float): First number (dividend).
        b (float): Second number (divisor).

    Returns:
        float: Quotient (a / b).
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")

    return a / b

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise a number to the power of another number.

    Args:
        base (float): The base number.
        exponent (float): The exponent (power).

    Returns:
        float: Result of raising base to the power of exponent.
    """
    return np.power(base, exponent)

if __name__ == "__main__":
    mcp.run()
```

## Step 3: Update Entry Point File

Modify `hatch_mcp_server_entry.py` to use proper citations and naming:

```python
from hatch_mcp_server import HatchMCP
from mcp_server import mcp

hatch_mcp = HatchMCP("ArithmeticTools",
                     fast_mcp=mcp,
                     origin_citation="Your Name, \"Origin: Arithmetic MCP Server Tutorial\", 2025",
                     mcp_citation="Your Name, \"MCP: Arithmetic Tools Implementation\", 2025")

if __name__ == "__main__":
    hatch_mcp.server.run()
```

## Step 4: Key Implementation Principles

**Type Hints**: Always use proper type hints for parameters and return values. This helps LLMs understand expected input/output types.

**Docstrings**: Write comprehensive docstrings following the Google style. The docstring is crucial as LLMs use it to understand tool functionality.

**Error Handling**: Implement appropriate error handling for edge cases (like division by zero).

**Output Types**: Be aware that the final consumer of the tools' output is an LLM. Therefore, even if you returns complex types from your tools, the LLM will only see the string representation of that output. Hence, it is often a good idea to:

- return primitive types (strings, numbers, booleans) from your tools
- return JSON-serializable types (dicts, lists) from your tools (see [below](#complex-return-types))
- implement a `__str__` method where possible for complex return types.

## Step 5: Common Implementation Patterns

### Adding More Dependencies

If your implementation requires additional Python packages, add them to your imports:

```python
import numpy as np
import requests  # For HTTP requests
import json      # For JSON processing
from datetime import datetime  # For date/time operations
```

However, if you want your MCP server to work for anyone out of the box, you must leverage the dependency resolution capabilities of Hatch. This is done by editing the `hatch_metadata.json` file as described in the next article.

### Complex Return Types

For tools that return structured data, use appropriate type hints:

```python
from typing import Dict, List

@mcp.tool()
def get_statistics(numbers: List[float]) -> Dict[str, float]:
    """Calculate statistics for a list of numbers.

    Args:
        numbers (List[float]): List of numbers to analyze.

    Returns:
        Dict[str, float]: Dictionary containing mean, median, std deviation.
    """
    if not numbers:
        raise ValueError("Numbers list cannot be empty")

    return {
        "mean": np.mean(numbers),
        "median": np.median(numbers),
        "std_dev": np.std(numbers)
    }
```

### Input Validation Best Practices

Always validate inputs to provide clear error messages:

```python
@mcp.tool()
def safe_divide(a: float, b: float) -> float:
    """Safely divide two numbers with validation.

    Args:
        a (float): Dividend.
        b (float): Divisor.

    Returns:
        float: Result of division.
    """
    # Type validation (FastMCP handles this automatically)
    # Range validation
    if b == 0:
        raise ValueError("Division by zero is not allowed")

    # Additional validation for edge cases
    if abs(b) < 1e-10:
        raise ValueError("Divisor too close to zero for safe division")

    return a / b
```

Errors raised in tool functions are propagated back to the LLM, so it's important to provide clear, actionable error messages. This can help the LLM understand what went wrong in the tool call and maybe how to fix the arguments before retrying the tool call.

**Exercise:**
Implement a different set of tools for a "text processing" MCP server that includes functions for string manipulation (uppercase, lowercase, reverse, word count). Include proper error handling for empty strings.

<details>
<summary>Solution</summary>

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("TextProcessingTools", log_level="WARNING")

@mcp.tool()
def to_uppercase(text: str) -> str:
    """Convert text to uppercase.

    Args:
        text (str): Input text to convert.

    Returns:
        str: Text converted to uppercase.
    """
    if not text:
        raise ValueError("Input text cannot be empty")
    return text.upper()

@mcp.tool()
def to_lowercase(text: str) -> str:
    """Convert text to lowercase.

    Args:
        text (str): Input text to convert.

    Returns:
        str: Text converted to lowercase.
    """
    if not text:
        raise ValueError("Input text cannot be empty")
    return text.lower()

@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse the order of characters in text.

    Args:
        text (str): Input text to reverse.

    Returns:
        str: Text with characters in reverse order.
    """
    if not text:
        raise ValueError("Input text cannot be empty")
    return text[::-1]

@mcp.tool()
def word_count(text: str) -> int:
    """Count the number of words in text.

    Args:
        text (str): Input text to count words in.

    Returns:
        int: Number of words in the text.
    """
    if not text:
        return 0
    return len(text.split())

if __name__ == "__main__":
    mcp.run()
```

</details>

> Previous: [Generate Template](01-generate-template.md)
> Next: [Edit Metadata](03-edit-metadata.md)
