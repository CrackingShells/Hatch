"""Property-based assertion library for MCP adapter testing.

All assertions verify adapter contracts using fields.py as the reference
through HostSpec metadata. No hardcoded field names — everything is derived.

Usage:
    >>> from tests.test_data.mcp_adapters.assertions import assert_only_supported_fields
    >>> assert_only_supported_fields(result, host_spec)
"""

from typing import Any, Dict

from hatch.mcp_host_config.fields import EXCLUDED_ALWAYS

# Import locally to avoid circular; HostSpec is used as type hint only
from tests.test_data.mcp_adapters.host_registry import HostSpec


def assert_only_supported_fields(result: Dict[str, Any], host: HostSpec) -> None:
    """Verify result contains only fields from fields.py for this host.

    After field mapping, the result may contain host-native names (e.g.,
    Codex 'arguments' instead of 'args'). We account for this by also
    accepting mapped field names.

    Args:
        result: Serialized adapter output
        host: HostSpec with metadata derived from fields.py
    """
    result_fields = set(result.keys())
    # Build the set of allowed field names: supported + mapped target names
    allowed = set(host.supported_fields)
    for _universal, host_specific in host.field_mappings.items():
        allowed.add(host_specific)

    unsupported = result_fields - allowed
    assert not unsupported, (
        f"[{host.host_name}] Unsupported fields in result: {sorted(unsupported)}. "
        f"Allowed: {sorted(allowed)}"
    )


def assert_excluded_fields_absent(result: Dict[str, Any], host: HostSpec) -> None:
    """Verify EXCLUDED_ALWAYS fields are not in result.

    Args:
        result: Serialized adapter output
        host: HostSpec (used for error context)
    """
    excluded_present = set(result.keys()) & EXCLUDED_ALWAYS
    assert (
        not excluded_present
    ), f"[{host.host_name}] Excluded fields found in result: {sorted(excluded_present)}"


def assert_transport_present(result: Dict[str, Any], host: HostSpec) -> None:
    """Verify at least one transport field is present in result.

    Args:
        result: Serialized adapter output
        host: HostSpec with transport fields derived from fields.py
    """
    transport_fields = host.get_transport_fields()
    present = set(result.keys()) & transport_fields
    assert present, (
        f"[{host.host_name}] No transport field present in result. "
        f"Expected one of: {sorted(transport_fields)}"
    )


def assert_transport_mutual_exclusion(result: Dict[str, Any], host: HostSpec) -> None:
    """Verify exactly one transport field is present in result.

    Args:
        result: Serialized adapter output
        host: HostSpec with transport fields derived from fields.py
    """
    transport_fields = host.get_transport_fields()
    present = set(result.keys()) & transport_fields
    assert len(present) == 1, (
        f"[{host.host_name}] Expected exactly 1 transport, "
        f"got {len(present)}: {sorted(present)}"
    )


def assert_field_mappings_applied(result: Dict[str, Any], host: HostSpec) -> None:
    """Verify field mappings from fields.py were applied.

    For hosts with field mappings (e.g., Codex), universal field names
    should NOT appear in the result — only the mapped names should.

    Args:
        result: Serialized adapter output
        host: HostSpec with field_mappings derived from fields.py
    """
    for universal, host_specific in host.field_mappings.items():
        if universal in result:
            assert False, (
                f"[{host.host_name}] Universal field '{universal}' should have been "
                f"mapped to '{host_specific}'"
            )


def assert_tool_lists_coexist(result: Dict[str, Any], host: HostSpec) -> None:
    """Verify both allowlist and denylist fields are present in result.

    Only meaningful for hosts that support tool lists. Skips silently
    if the host has no tool list configuration.

    Args:
        result: Serialized adapter output
        host: HostSpec with tool list config derived from fields.py
    """
    tool_config = host.get_tool_list_config()
    if not tool_config:
        return

    allowlist = tool_config["allowlist"]
    denylist = tool_config["denylist"]

    assert (
        allowlist in result
    ), f"[{host.host_name}] Allowlist field '{allowlist}' missing from result"
    assert (
        denylist in result
    ), f"[{host.host_name}] Denylist field '{denylist}' missing from result"


def assert_unsupported_field_absent(
    result: Dict[str, Any], host: HostSpec, field_name: str
) -> None:
    """Verify a specific unsupported field is not in result.

    Args:
        result: Serialized adapter output
        host: HostSpec (used for error context)
        field_name: The unsupported field that should have been filtered
    """
    assert field_name not in result, (
        f"[{host.host_name}] Unsupported field '{field_name}' should have been "
        f"filtered but is present in result"
    )
