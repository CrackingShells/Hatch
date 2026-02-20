"""Data-driven host configuration integration tests.

Tests individual host configuration for all 8 hosts using a single generic
test function. Verifies that each host's canonical config serializes correctly
per fields.py contracts.

Architecture:
    - ONE test function handles ALL 8 hosts
    - Assertions verify against fields.py (not hardcoded expectations)
    - Adding a host: update fields.py + add fixture entry → tests auto-generated
"""

from pathlib import Path

import pytest

from tests.test_data.mcp_adapters.assertions import (
    assert_excluded_fields_absent,
    assert_field_mappings_applied,
    assert_only_supported_fields,
    assert_transport_present,
)
from tests.test_data.mcp_adapters.host_registry import HostRegistry

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
ALL_HOSTS = REGISTRY.all_hosts()


class TestHostConfiguration:
    """Host configuration tests for all hosts.

    Verifies that each host's canonical config serializes correctly,
    producing output that satisfies all fields.py contracts.
    """

    @pytest.mark.parametrize("host", ALL_HOSTS, ids=lambda h: h.host_name)
    @integration_test(scope="component")
    def test_configure_host(self, host):
        """Generic configuration test that works for ANY host.

        Flow:
            1. Load canonical config from fixtures
            2. Serialize with host adapter
            3. Verify output against fields.py contracts
        """
        # Load canonical config from fixtures
        config = host.load_config()

        # Serialize
        adapter = host.get_adapter()
        result = adapter.serialize(config)

        # Property-based assertions (verify against fields.py)
        assert_only_supported_fields(result, host)
        assert_excluded_fields_absent(result, host)
        assert_transport_present(result, host)
        assert_field_mappings_applied(result, host)
