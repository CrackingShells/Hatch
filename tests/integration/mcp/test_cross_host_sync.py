"""Data-driven cross-host sync integration tests.

Tests all host pair combinations (8×8 = 64) using a single generic test
function. Test cases are generated from canonical_configs.json fixture
with metadata derived from fields.py.

Architecture:
    - ONE test function handles ALL 64 combinations
    - Assertions verify against fields.py (not hardcoded expectations)
    - Adding a host: update fields.py + add fixture entry → tests auto-generated
"""

from pathlib import Path

import pytest

from hatch.mcp_host_config.models import MCPServerConfig
from tests.test_data.mcp_adapters.assertions import (
    assert_excluded_fields_absent,
    assert_only_supported_fields,
    assert_transport_present,
)
from tests.test_data.mcp_adapters.host_registry import (
    HostRegistry,
    generate_sync_test_cases,
)

try:
    from wobble.decorators import integration_test
except ImportError:

    def integration_test(scope="component"):
        def decorator(func):
            return func

        return decorator


# Registry loads fixtures and derives metadata from fields.py
FIXTURES_PATH = (
    Path(__file__).resolve().parents[2]
    / "test_data"
    / "mcp_adapters"
    / "canonical_configs.json"
)
REGISTRY = HostRegistry(FIXTURES_PATH)
SYNC_TEST_CASES = generate_sync_test_cases(REGISTRY)


class TestCrossHostSync:
    """Cross-host sync tests for all host pair combinations.

    Verifies that serializing a config from one host and re-serializing
    it for another host produces valid output per fields.py contracts.
    """

    @pytest.mark.parametrize(
        "test_case",
        SYNC_TEST_CASES,
        ids=lambda tc: tc.test_id,
    )
    @integration_test(scope="service")
    def test_sync_between_hosts(self, test_case):
        """Generic sync test that works for ANY host pair.

        Flow:
            1. Load source config from fixtures
            2. Serialize with source adapter (filter → validate → transform)
            3. Create intermediate MCPServerConfig from serialized output
            4. Serialize with target adapter
            5. Verify output against fields.py contracts
        """
        # Load source config from fixtures
        source_config = test_case.from_host.load_config()

        # Serialize with source adapter
        from_adapter = test_case.from_host.get_adapter()
        serialized = from_adapter.serialize(source_config)

        # Create intermediate config from serialized output
        intermediate = MCPServerConfig(name="sync-test", **serialized)

        # Serialize with target adapter
        to_adapter = test_case.to_host.get_adapter()
        result = to_adapter.serialize(intermediate)

        # Property-based assertions (verify against fields.py)
        assert_only_supported_fields(result, test_case.to_host)
        assert_excluded_fields_absent(result, test_case.to_host)
        assert_transport_present(result, test_case.to_host)
