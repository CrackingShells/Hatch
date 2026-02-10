# 03: Edit Metadata

---
**Concepts covered:**

- Hatch package metadata schema structure and validation
- Required and optional metadata fields
- Dependency specification and compatibility constraints
- Package versioning and licensing

**Skills you will practice:**

- Editing the hatch_metadata.json file
- Understanding schema validation requirements
- Configuring dependencies and compatibility settings
- Setting up proper package metadata for distribution

---

This article covers editing the `hatch_metadata.json` file that defines your package's metadata and dependencies. Now that you have implemented your MCP server functionality, you need to configure the metadata to properly describe your package and its dependencies.

## Understanding the Metadata Schema

The `hatch_metadata.json` file follows the schema defined in [Hatch-Schemas/packag](https://github.com/CrackingShells/Hatch-Schemas/blob/main/package/). The schemas are not well-defined yet and are subject to change. However, at the time of writing, the latest version is `v1.2.1`.

The package's metadata are not critical to the package's functionality but are critical to its distribution (submission to the online registry) and installation by the Hatch ecosystem. For example, [dependencies](#step-3-define-dependencies) information are leveraged during the package's installation to automatically resolve and install any required dependencies. The list of [tools](#step-5-define-tools-and-citations) your package provides is used during package submission to the online registry to confirm the content of your mcp server. Except these, the metadata are not used at runtime simply helps providing information to users and transparency to the community.

## Step 1: Required Fields

Every package must include these fields:

```json
{
  "package_schema_version": "1.2.1",
  "name": "package_name",
  "version": "0.1.0",
  "entry_point": "hatch_mcp_server_entry.py",
  "description": "Package description",
  "tags": [],
  "author": {
    "name": "Author Name"
  },
  "license": {
    "name": "MIT"
  }
}
```

## Step 2: Configure Package Information

Edit the basic package information:

```json
{
  "package_schema_version": "1.2.1",
  "name": "my_awesome_package",
  "version": "1.0.0",
  "description": "An awesome MCP server package that does amazing things",
  "tags": ["mcp", "server", "automation", "productivity"],
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "contributors": [
    {
      "name": "Contributor Name",
      "email": "contributor@example.com"
    }
  ],
  "license": {
    "name": "MIT",
    "uri": "https://opensource.org/licenses/MIT"
  },
  "repository": "https://github.com/yourusername/my-awesome-package",
  "documentation": "https://your-docs-site.com",
  "entry_point": "hatch_mcp_server_entry.py"
}
```

## Step 3: Define Dependencies

Configure dependencies based on your implementation. For our arithmetic server that uses numpy:

```json
{
  "dependencies": {
    "hatch": [],
    "python": [
      {
        "name": "numpy",
        "version_constraint": ">=2.2.0",
        "package_manager": "pip"
      }
    ],
    "system": [],
    "docker": []
  }
}
```

### Dependency Types Explained

**Hatch dependencies**: Other Hatch packages your server depends on

```json
"hatch": [
  {
    "name": "another_hatch_package",
    "version_constraint": ">=1.0.0"
  }
]
```

**Python dependencies**: Python packages installed via pip

```json
"python": [
  {
    "name": "requests",
    "version_constraint": ">=2.28.0",
    "package_manager": "pip"
  }
]
```

**System dependencies**: OS-level packages (Linux only currently)

```json
"system": [
  {
    "name": "curl",
    "version_constraint": ">=7.0.0",
    "package_manager": "apt"
  }
]
```

**Docker dependencies**: Container images for services

```json
"docker": [
  {
    "name": "redis",
    "version_constraint": ">=7.0.0",
    "registry": "dockerhub"
  }
]
```

### Version Constraint Patterns

- `==1.0.0` - Exact version
- `>=1.0.0` - Minimum version
- `<=2.0.0` - Maximum version
- `!=1.5.0` - Exclude specific version

## Step 4: Set Compatibility Requirements

Define compatibility constraints:

```json
{
  "compatibility": {
    "hatchling": ">=0.1.0",
    "python": ">=3.8"
  }
}
```

## Step 5: Define Tools and Citations

Document the tools your package provides. For our arithmetic server:

```json
{
  "tools": [
    {
      "name": "add",
      "description": "Add two numbers together."
    },
    {
      "name": "subtract",
      "description": "Subtract one number from another."
    },
    {
      "name": "multiply",
      "description": "Multiply two numbers together."
    },
    {
      "name": "divide",
      "description": "Divide one number by another."
    },
    {
      "name": "power",
      "description": "Raise a number to the power of another number."
    }
  ],
  "citations": {
    "origin": "Your Name, \"Origin: Arithmetic MCP Server Tutorial\", 2025",
    "mcp": "Your Name, \"MCP: Arithmetic Tools Implementation\", 2025"
  }
}
```

**Important**: The tools list should match exactly the functions you decorated with `@mcp.tool()` in your implementation.

## Step 6: Complete Example

Here's a complete `hatch_metadata.json` file for our arithmetic package:

```json
{
  "package_schema_version": "1.2.1",
  "name": "arithmetic_tutorial_pkg",
  "version": "1.0.0",
  "description": "A tutorial package demonstrating arithmetic operations with MCP",
  "tags": ["tutorial", "math", "arithmetic", "mcp"],
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "license": {
    "name": "MIT"
  },
  "entry_point": "hatch_mcp_server_entry.py",
  "dependencies": {
    "hatch": [],
    "python": [
      {
        "name": "numpy",
        "version_constraint": ">=2.2.0",
        "package_manager": "pip"
      }
    ],
    "system": [],
    "docker": []
  },
  "compatibility": {
    "python": ">=3.8"
  },
  "tools": [
    {"name": "add", "description": "Add two numbers together."},
    {"name": "subtract", "description": "Subtract one number from another."},
    {"name": "multiply", "description": "Multiply two numbers together."},
    {"name": "divide", "description": "Divide one number by another."},
    {"name": "power", "description": "Raise a number to the power of another number."}
  ],
  "citations": {
    "origin": "Your Name, \"Origin: Arithmetic MCP Server Tutorial\", 2025",
    "mcp": "Your Name, \"MCP: Arithmetic Tools Implementation\", 2025"
  }
}
```

## Step 7: Validate Metadata Structure

The schema enforces several validation rules:

- **Package names** must match pattern `^[a-z0-9_]+$` (lowercase alphanumeric + underscore)
- **Versions** must follow semantic versioning `^\d+(\.\d+)*$`
- **Email addresses** must be valid email format
- **URIs** must be valid URI format
- **Version constraints** must match pattern `^\s*(==|>=|<=|!=)\s*\d+(\.\d+)*$`

**Exercise:**
Create a complete metadata file for a hypothetical "weather-service" package that depends on the requests library and provides weather-related tools.

<details>
<summary>Solution</summary>
Yours might differ, but here's one example:

```json
{
  "package_schema_version": "1.2.1",
  "name": "weather_service",
  "version": "1.0.0",
  "description": "MCP server for weather information and forecasting",
  "tags": ["weather", "forecast", "api", "mcp"],
  "author": {
    "name": "Weather Developer",
    "email": "dev@weather-service.com"
  },
  "license": {
    "name": "MIT",
    "uri": "https://opensource.org/licenses/MIT"
  },
  "repository": "https://github.com/weather/weather-service",
  "entry_point": "hatch_mcp_server_entry.py",
  "dependencies": {
    "python": [
      {
        "name": "requests",
        "version_constraint": ">=2.28.0",
        "package_manager": "pip"
      }
    ]
  },
  "compatibility": {
    "python": ">=3.8"
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get current weather for a location"
    },
    {
      "name": "get_forecast",
      "description": "Get weather forecast for a location"
    }
  ],
  "citations": {
    "origin": "Weather data provided by OpenWeather API",
    "mcp": "Implements MCP specification for weather services"
  }
}
```

</details>

> Previous: [Implement Functionality](02-implement-functionality.md)
> Next: [Validate and Install](04-validate-and-install.md)
