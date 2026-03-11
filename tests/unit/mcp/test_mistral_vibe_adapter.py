"""Unit tests for the Mistral Vibe adapter."""

import unittest

from hatch.mcp_host_config.adapters.mistral_vibe import MistralVibeAdapter
from hatch.mcp_host_config.models import MCPServerConfig


class TestMistralVibeAdapter(unittest.TestCase):
    """Verify Mistral-specific filtering and transport mapping."""

    def test_serialize_filters_type_but_preserves_sse_transport_hint(self):
        """Canonical type hints should map to transport without serializing type."""
        result = MistralVibeAdapter().serialize(
            MCPServerConfig(
                name="weather",
                url="https://example.com/mcp",
                type="sse",
            )
        )

        self.assertEqual(result["url"], "https://example.com/mcp")
        self.assertEqual(result["transport"], "streamable-http")
        self.assertNotIn("type", result)

    def test_serialize_maps_http_url_without_exposing_httpUrl(self):
        """httpUrl input should serialize as Mistral's url+transport format."""
        result = MistralVibeAdapter().serialize(
            MCPServerConfig(
                name="weather",
                httpUrl="https://example.com/http",
            )
        )

        self.assertEqual(result["url"], "https://example.com/http")
        self.assertEqual(result["transport"], "http")
        self.assertNotIn("httpUrl", result)


if __name__ == "__main__":
    unittest.main()
