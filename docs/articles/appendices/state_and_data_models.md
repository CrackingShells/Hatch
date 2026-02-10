# State and Data Models

This appendix provides detailed information about data structures and state management in Hatch.

## Package Metadata Schema

The complete package metadata schema is defined in `Hatch-Schemas/package/v1.2.0/hatch_pkg_metadata_schema.json`.

### Required Fields

```json
{
  "package_schema_version": "1.2.0",
  "name": "package_name",
  "version": "1.0.0",
  "entry_point": "hatch_mcp_server_entry.py",
  "description": "Package description",
  "tags": ["tag1", "tag2"],
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  },
  "license": {
    "name": "MIT",
    "uri": "https://opensource.org/licenses/MIT"
  }
}
```

### Optional Fields

```json
{
  "contributors": [
    {
      "name": "Contributor Name",
      "email": "contributor@example.com"
    }
  ],
  "repository": "https://github.com/user/repo",
  "documentation": "https://docs.example.com",
  "dependencies": {
    "hatch": [...],
    "python": [...],
    "system": [...],
    "docker": [...]
  },
  "compatibility": {
    "hatchling": ">=0.1.0",
    "python": ">=3.8"
  },
  "tools": [
    {
      "name": "tool_name",
      "description": "Tool description"
    }
  ],
  "citations": {
    "origin": "Origin citation",
    "mcp": "MCP citation"
  }
}
```

### Dependency Structures

#### Hatch Dependencies

```json
{
  "hatch": [
    {
      "name": "package_name",
      "version_constraint": ">=1.0.0"
    }
  ]
}
```

#### Python Dependencies

```json
{
  "python": [
    {
      "name": "requests",
      "version_constraint": ">=2.28.0",
      "package_manager": "pip"
    }
  ]
}
```

#### System Dependencies

```json
{
  "system": [
    {
      "name": "curl",
      "version_constraint": ">=7.0.0",
      "package_manager": "apt"
    }
  ]
}
```

#### Docker Dependencies

```json
{
  "docker": [
    {
      "name": "redis",
      "version_constraint": ">=7.0.0",
      "registry": "dockerhub"
    }
  ]
}
```

## Environment State

### Environment Metadata

Hatch stores environments as a mapping from environment name to metadata. The `environments.json` file looks like a dictionary where each key is the environment name and the value is the environment metadata. For example:

```json
{
  "default": {
    "name": "default",
    "description": "Default environment",
    "created_at": "2025-07-02T08:15:03.168827",
    "packages": [],
    "python_environment": true,
    "python_env": {
      "enabled": true,
      "conda_env_name": "hatch_default",
         "python_executable": "/home/<user>/miniforge3/envs/hatch_default/bin/python",
      "created_at": "2025-07-07T22:19:33.122291",
      "version": "3.13.5",
      "requested_version": null,
      "manager": "conda"
    }
  },
  "modeling": {
    "name": "modeling",
    "description": "An environment for modeling tools",
    "created_at": "2025-08-08T16:18:29.711024",
    "packages": [
      {
        "name": "arithmetic_pkg",
        "version": "1.2.0",
        "type": "hatch",
         "source": "/path/to/local/packages/arithmetic_pkg",
        "installed_at": "2025-08-08T16:26:42.150821"
      },
      {
        "name": "base_pkg_1",
        "version": "1.0.3",
        "type": "hatch",
         "source": "https://example.com/base_pkg_1-v1.0.3.zip",
        "installed_at": "2025-08-24T12:57:42.431051"
      }
    ],
    "python_environment": true,
    "python_version": "3.12",
    "python_env": {
      "enabled": true,
      "conda_env_name": "hatch_modeling",
       "python_executable": "/home/<user>/miniforge3/envs/hatch_modeling/bin/python",
      "created_at": "2025-08-08T16:18:29.711024",
      "version": "3.12.11",
      "requested_version": "3.12",
      "manager": "conda"
    }
  }
}
```

### Current Environment Tracking

The current environment is tracked in Hatch's cache directory in a file named `current_env`: `~/.hatch/envs/current_env`
It only contains the name of the current environment.

```txt
my_env
```
