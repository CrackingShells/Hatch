# Architecture Overview

This article is about:
- Hatch's internal architecture
- Core components and their responsibilities

You will learn about:
- The main layers and modules in Hatch
- Key design decisions and component roles

This article provides a concise overview of Hatch's modular architecture and core components.

Hatch uses a modular architecture with clear separation of concerns across several layers:

## High-Level Architecture

See the PlantUML diagram in [resources/diagrams/architecture_overview.puml](../../resources/diagrams/architecture_overview.puml) for a visual overview of the system architecture.

# Core Components

## Environment Manager
- File: `environment_manager.py`
- Central coordinator for environment operations
- Manages lifecycle, current environment, package installation, Python integration, and state
- Key: Single source of truth, lazy registry loading, file-based persistence

## Package Loader
- File: `package_loader.py`
- Handles package downloading, caching, and installation
- Supports registry/local packages, atomic operations, cache management

## Registry Retriever
- File: `registry_retriever.py`
- Manages access to the Hatch package registry
- Handles data fetching, caching, simulation mode, fallback

## Dependency Orchestrator
- File: `dependency_installation_orchestrator.py`
- Coordinates dependency installation workflows
- Resolves graphs, manages order, user consent, error handling

## Python Environment Manager
- File: `python_environment_manager.py`
- Integrates Conda/mamba, manages Python executables, cross-platform support

Refer to code docstrings for implementation details. Use diagrams above for a high-level view.