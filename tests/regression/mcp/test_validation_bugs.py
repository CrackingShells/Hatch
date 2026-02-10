"""Validation bug regression tests (data-driven).

Property-based tests generated from fields.py metadata to prevent
validation bug regressions. Tests verify:
- Tool list coexistence (allowlist + denylist can both be present)
- Transport mutual exclusion (exactly one transport required)

Architecture:
    - Test cases GENERATED from fields.py metadata
    - Tests verify PROPERTIES, not specific examples
    - Adding a host with tool lists: test case auto-generated
"""

from pathlib import Path

import pytest

from hatch.mcp_host_config.adapters.base import AdapterValidationError
from hatch.mcp_host_config.models import MCPServerConfig
from tests.test_data.mcp_adapters.assertions import assert_tool_lists_coexist
from tests.test_data.mcp_adapters.host_registry import (
    HostRegistry,
    generate_validation_test_cases,
)

try:
    from wobble.decorators import regression_test
except ImportError:

    def regression_test(func):
        return func


# Registry loads fixtures and derives metadata from fields.py
FIXTURES_PATH = (
    Path(__file__).resolve().parents[2]
    / "test_data"
    / "mcp_adapters"
    / "canonical_configs.json"
)
REGISTRY = HostRegistry(FIXTURES_PATH)
VALIDATION_CASES = generate_validation_test_cases(REGISTRY)

# Split cases by property for separate test functions
TOOL_LIST_CASES = [
    c for c in VALIDATION_CASES if c.property_name == "tool_lists_coexist"
]
TRANSPORT_CASES = [
    c for c in VALIDATION_CASES if c.property_name == "transport_mutual_exclusion"
]


class TestToolListCoexistence:
    """Regression tests: allowlist and denylist can coexist.

    Per official docs:
    - Gemini: excludeTools takes precedence over includeTools
    - Codex: disabled_tools applied after enabled_tools
    """

    @pytest.mark.parametrize(
        "test_case",
        TOOL_LIST_CASES,
        ids=lambda tc: tc.test_id,
    )
    @regression_test
    def test_tool_lists_can_coexist(self, test_case):
        """Verify both allowlist and denylist can be present simultaneously."""
        host = test_case.host
        tool_config = host.get_tool_list_config()

        # Create config with both allowlist and denylist
        config_data = {
            "name": "test",
            "command": "python",
            tool_config["allowlist"]: ["tool1"],
            tool_config["denylist"]: ["tool2"],
        }
        config = MCPServerConfig(**config_data)

        # Serialize (should NOT raise)
        adapter = host.get_adapter()
        result = adapter.serialize(config)

        # Assert both fields present in output
        assert_tool_lists_coexist(result, host)


class TestTransportMutualExclusion:
    """Regression tests: exactly one transport required.

    All hosts enforce that only one transport method can be specified.
    Having both command and url should raise AdapterValidationError.
    """

    @pytest.mark.parametrize(
        "test_case",
        TRANSPORT_CASES,
        ids=lambda tc: tc.test_id,
    )
    @regression_test
    def test_transport_mutual_exclusion(self, test_case):
        """Verify multiple transports are rejected."""
        host = test_case.host
        adapter = host.get_adapter()

        # Create config with multiple transports (command + url)
        config = MCPServerConfig(
            name="test",
            command="python",
            url="http://test.example.com/mcp",
        )

        # Should raise validation error
        with pytest.raises(AdapterValidationError):
            adapter.serialize(config)
