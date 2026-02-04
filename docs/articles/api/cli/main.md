# Entry Point Module

The entry point module (`__main__.py`) serves as the routing layer for the Hatch CLI, handling argument parsing and command delegation.

## Overview

This module provides:

- Command-line argument parsing using `argparse`
- Custom `HatchArgumentParser` with formatted error messages
- Manager initialization (HatchEnvironmentManager, MCPHostConfigurationManager)
- Command routing to appropriate handler modules

## Module Reference

::: hatch.cli.__main__
    options:
      show_source: true
      show_root_heading: true
      heading_level: 2
