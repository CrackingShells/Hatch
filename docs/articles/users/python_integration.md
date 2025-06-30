# Python Integration

This article is about:
- Using Python dependencies in Hatch packages

You will learn about:
- Integrating Python libraries into MCP server packages

See the [Quick Start Guide](../users/quick_start.md) for setup steps.

## Add Python Support

```bash
hatch env create <env-name> --description "Python environment"
hatch env use <env-name>
```

## Install Python Dependencies

Add your package with Python dependencies:

```bash
hatch package add ./my-python-tool
```

For troubleshooting, see the [Error Handling Guide](error_handling.md).
