"""Host registry for data-driven MCP adapter testing.

This module provides the HostRegistry and HostSpec classes that bridge
minimal fixture data (canonical_configs.json) with complete host metadata
derived from fields.py (the single source of truth).

Architecture:
    - HostSpec: Complete host specification with metadata derived from fields.py
    - HostRegistry: Discovery, loading, and test case generation
    - Generator functions: Create parameterized test cases from registry data

Design Principle:
    fields.py is the ONLY source of metadata. Fixtures contain ONLY config values.
    No metadata duplication. Changes to fields.py automatically reflected in tests.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from hatch.mcp_host_config.adapters.base import BaseAdapter
from hatch.mcp_host_config.adapters.claude import ClaudeAdapter
from hatch.mcp_host_config.adapters.codex import CodexAdapter
from hatch.mcp_host_config.adapters.cursor import CursorAdapter
from hatch.mcp_host_config.adapters.gemini import GeminiAdapter
from hatch.mcp_host_config.adapters.kiro import KiroAdapter
from hatch.mcp_host_config.adapters.lmstudio import LMStudioAdapter
from hatch.mcp_host_config.adapters.opencode import OpenCodeAdapter
from hatch.mcp_host_config.adapters.vscode import VSCodeAdapter
from hatch.mcp_host_config.fields import (
    CLAUDE_FIELDS,
    CODEX_FIELD_MAPPINGS,
    CODEX_FIELDS,
    CURSOR_FIELDS,
    EXCLUDED_ALWAYS,
    GEMINI_FIELDS,
    KIRO_FIELDS,
    LMSTUDIO_FIELDS,
    OPENCODE_FIELDS,
    TYPE_SUPPORTING_HOSTS,
    VSCODE_FIELDS,
)
from hatch.mcp_host_config.models import MCPServerConfig


# ============================================================================
# Field set mapping: host name → field set from fields.py
# ============================================================================

FIELD_SETS: Dict[str, FrozenSet[str]] = {
    "claude-desktop": CLAUDE_FIELDS,
    "claude-code": CLAUDE_FIELDS,
    "vscode": VSCODE_FIELDS,
    "cursor": CURSOR_FIELDS,
    "lmstudio": LMSTUDIO_FIELDS,
    "gemini": GEMINI_FIELDS,
    "kiro": KIRO_FIELDS,
    "codex": CODEX_FIELDS,
    "opencode": OPENCODE_FIELDS,
}

# Reverse mappings for Codex (host-native name → universal name)
CODEX_REVERSE_MAPPINGS: Dict[str, str] = {v: k for k, v in CODEX_FIELD_MAPPINGS.items()}


# ============================================================================
# HostSpec dataclass
# ============================================================================


@dataclass
class HostSpec:
    """Complete host specification with metadata derived from fields.py.

    Attributes:
        host_name: Host identifier (e.g., "claude-desktop", "gemini")
        canonical_config: Raw config values from fixture (host-native field names)
        supported_fields: Fields this host supports (from fields.py)
        field_mappings: Universal→host-specific field name mappings (from fields.py)
    """

    host_name: str
    canonical_config: Dict[str, Any]
    supported_fields: FrozenSet[str] = field(default_factory=frozenset)
    field_mappings: Dict[str, str] = field(default_factory=dict)

    def get_adapter(self) -> BaseAdapter:
        """Instantiate the adapter for this host."""
        adapter_map = {
            "claude-desktop": lambda: ClaudeAdapter(variant="desktop"),
            "claude-code": lambda: ClaudeAdapter(variant="code"),
            "vscode": VSCodeAdapter,
            "cursor": CursorAdapter,
            "lmstudio": LMStudioAdapter,
            "gemini": GeminiAdapter,
            "kiro": KiroAdapter,
            "codex": CodexAdapter,
            "opencode": OpenCodeAdapter,
        }
        factory = adapter_map[self.host_name]
        return factory()

    def load_config(self) -> MCPServerConfig:
        """Load canonical config as MCPServerConfig object.

        Handles reverse field mapping for hosts with non-standard names
        (e.g., Codex 'arguments' → 'args' for MCPServerConfig).

        Returns:
            MCPServerConfig populated with canonical values (None values excluded)
        """
        config_data = {}
        for key, value in self.canonical_config.items():
            if value is None:
                continue
            # Reverse-map host-native names to MCPServerConfig field names
            universal_key = CODEX_REVERSE_MAPPINGS.get(key, key)
            config_data[universal_key] = value

        # Ensure name is set for MCPServerConfig
        if "name" not in config_data:
            config_data["name"] = f"test-{self.host_name}"

        return MCPServerConfig(**config_data)

    def get_transport_fields(self) -> Set[str]:
        """Compute transport fields from supported_fields."""
        return self.supported_fields & {"command", "url", "httpUrl"}

    def supports_type_field(self) -> bool:
        """Check if 'type' field is supported."""
        return self.host_name in TYPE_SUPPORTING_HOSTS

    def get_tool_list_config(self) -> Optional[Dict[str, str]]:
        """Compute tool list configuration from supported_fields.

        Returns:
            Dict with 'allowlist' and 'denylist' keys mapping to field names,
            or None if host doesn't support tool lists.
        """
        if (
            "includeTools" in self.supported_fields
            and "excludeTools" in self.supported_fields
        ):
            return {"allowlist": "includeTools", "denylist": "excludeTools"}
        if (
            "enabled_tools" in self.supported_fields
            and "disabled_tools" in self.supported_fields
        ):
            return {"allowlist": "enabled_tools", "denylist": "disabled_tools"}
        return None

    def compute_expected_fields(self, input_fields: Set[str]) -> Set[str]:
        """Compute which fields should appear after filtering.

        Args:
            input_fields: Set of field names in the input config

        Returns:
            Set of field names expected in the serialized output
        """
        return (input_fields & self.supported_fields) - EXCLUDED_ALWAYS

    def __repr__(self) -> str:
        return f"HostSpec({self.host_name})"


# ============================================================================
# Test case dataclasses
# ============================================================================


@dataclass
class SyncTestCase:
    """Test case for cross-host sync testing."""

    from_host: HostSpec
    to_host: HostSpec
    test_id: str


@dataclass
class ValidationTestCase:
    """Test case for validation property testing."""

    host: HostSpec
    property_name: str
    test_id: str


@dataclass
class FilterTestCase:
    """Test case for field filtering testing."""

    host: HostSpec
    unsupported_field: str
    test_id: str


# ============================================================================
# HostRegistry class
# ============================================================================


class HostRegistry:
    """Discovers hosts from fixtures and derives metadata from fields.py.

    The registry bridges minimal fixture data (canonical config values) with
    complete host metadata derived from fields.py. This ensures fields.py
    remains the single source of truth for all host specifications.

    Usage:
        >>> registry = HostRegistry(Path("tests/test_data/mcp_adapters/canonical_configs.json"))
        >>> hosts = registry.all_hosts()
        >>> pairs = registry.all_pairs()
        >>> codex = registry.get_host("codex")
    """

    def __init__(self, fixtures_path: Path):
        """Load canonical configs and derive metadata from fields.py.

        Args:
            fixtures_path: Path to canonical_configs.json
        """
        with open(fixtures_path) as f:
            raw_configs = json.load(f)

        self._hosts: Dict[str, HostSpec] = {}
        for host_name, config in raw_configs.items():
            supported = FIELD_SETS.get(host_name)
            if supported is None:
                raise ValueError(
                    f"Host '{host_name}' in fixture has no field set in fields.py"
                )

            mappings: Dict[str, str] = {}
            if host_name == "codex":
                mappings = dict(CODEX_FIELD_MAPPINGS)

            self._hosts[host_name] = HostSpec(
                host_name=host_name,
                canonical_config=config,
                supported_fields=supported,
                field_mappings=mappings,
            )

    def all_hosts(self) -> List[HostSpec]:
        """Return all discovered host specifications (sorted by name)."""
        return sorted(self._hosts.values(), key=lambda h: h.host_name)

    def get_host(self, name: str) -> HostSpec:
        """Get specific host by name.

        Args:
            name: Host identifier (e.g., "claude-desktop", "gemini")

        Raises:
            KeyError: If host not found in registry
        """
        if name not in self._hosts:
            available = ", ".join(sorted(self._hosts.keys()))
            raise KeyError(f"Host '{name}' not found. Available: {available}")
        return self._hosts[name]

    def all_pairs(self) -> List[Tuple[HostSpec, HostSpec]]:
        """Generate all (from_host, to_host) combinations for O(n²) testing."""
        hosts = self.all_hosts()
        return [(from_h, to_h) for from_h in hosts for to_h in hosts]

    def hosts_supporting_field(self, field_name: str) -> List[HostSpec]:
        """Find hosts that support a specific field.

        Args:
            field_name: Field name to query (e.g., "httpUrl", "envFile")
        """
        return [h for h in self.all_hosts() if field_name in h.supported_fields]

    def hosts_with_tool_lists(self) -> List[HostSpec]:
        """Find hosts that support tool allowlist/denylist."""
        return [h for h in self.all_hosts() if h.get_tool_list_config() is not None]


# ============================================================================
# Test case generator functions
# ============================================================================


def generate_sync_test_cases(registry: HostRegistry) -> List[SyncTestCase]:
    """Generate all cross-host sync test cases from registry.

    Returns one test case per (from_host, to_host) pair.
    For 8 hosts: 8×8 = 64 combinations.
    """
    return [
        SyncTestCase(
            from_host=from_h,
            to_host=to_h,
            test_id=f"sync_{from_h.host_name}_to_{to_h.host_name}",
        )
        for from_h, to_h in registry.all_pairs()
    ]


def generate_validation_test_cases(
    registry: HostRegistry,
) -> List[ValidationTestCase]:
    """Generate property-based validation test cases from fields.py metadata.

    Generates:
    - tool_lists_coexist: For hosts with tool list support
    - transport_mutual_exclusion: For all hosts
    """
    cases: List[ValidationTestCase] = []

    # Tool list coexistence: hosts with tool lists
    for host in registry.hosts_with_tool_lists():
        cases.append(
            ValidationTestCase(
                host=host,
                property_name="tool_lists_coexist",
                test_id=f"{host.host_name}_tool_lists_coexist",
            )
        )

    # Transport mutual exclusion: all hosts
    for host in registry.all_hosts():
        cases.append(
            ValidationTestCase(
                host=host,
                property_name="transport_mutual_exclusion",
                test_id=f"{host.host_name}_transport_mutual_exclusion",
            )
        )

    return cases


def generate_unsupported_field_test_cases(
    registry: HostRegistry,
) -> List[FilterTestCase]:
    """Generate unsupported field filtering test cases from fields.py.

    For each host, computes the set of fields it does NOT support
    (from the union of all host field sets) and generates a test case
    for each unsupported field.
    """
    # Compute all possible MCP fields from fields.py
    all_possible_fields = (
        CLAUDE_FIELDS
        | VSCODE_FIELDS
        | CURSOR_FIELDS
        | LMSTUDIO_FIELDS
        | GEMINI_FIELDS
        | KIRO_FIELDS
        | CODEX_FIELDS
        | OPENCODE_FIELDS
    )

    cases: List[FilterTestCase] = []
    for host in registry.all_hosts():
        unsupported = all_possible_fields - host.supported_fields
        for field_name in sorted(unsupported):
            cases.append(
                FilterTestCase(
                    host=host,
                    unsupported_field=field_name,
                    test_id=f"{host.host_name}_filters_{field_name}",
                )
            )

    return cases
