"""Integration tests for adapter serialization.

Test IDs: AS-01 to AS-10 (per 02-test_architecture_rebuild_v0.md)
Scope: Full serialization flow for each adapter with realistic configs.
"""

import unittest

from hatch.mcp_host_config.models import MCPServerConfig
from hatch.mcp_host_config.adapters import (
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    GeminiAdapter,
    KiroAdapter,
    LMStudioAdapter,
    VSCodeAdapter,
)


class TestClaudeAdapterSerialization(unittest.TestCase):
    """Integration tests for Claude adapter serialization."""

    def test_AS01_claude_stdio_serialization(self):
        """AS-01: Claude stdio config serializes correctly."""
        config = MCPServerConfig(
            name="my-server",
            command="python",
            args=["-m", "mcp_server"],
            env={"API_KEY": "secret"},
            type="stdio",
        )
        
        adapter = ClaudeAdapter()
        result = adapter.serialize(config)
        
        self.assertEqual(result["command"], "python")
        self.assertEqual(result["args"], ["-m", "mcp_server"])
        self.assertEqual(result["env"], {"API_KEY": "secret"})
        self.assertEqual(result["type"], "stdio")
        self.assertNotIn("name", result)

    def test_AS02_claude_sse_serialization(self):
        """AS-02: Claude SSE config serializes correctly."""
        config = MCPServerConfig(
            name="remote-server",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"},
            type="sse",
        )
        
        adapter = ClaudeAdapter()
        result = adapter.serialize(config)
        
        self.assertEqual(result["url"], "https://api.example.com/mcp")
        self.assertEqual(result["headers"], {"Authorization": "Bearer token"})
        self.assertEqual(result["type"], "sse")
        self.assertNotIn("name", result)
        self.assertNotIn("command", result)


class TestGeminiAdapterSerialization(unittest.TestCase):
    """Integration tests for Gemini adapter serialization."""

    def test_AS03_gemini_stdio_serialization(self):
        """AS-03: Gemini stdio config serializes correctly."""
        config = MCPServerConfig(
            name="gemini-server",
            command="npx",
            args=["mcp-server"],
            cwd="/workspace",
            timeout=30000,
        )
        
        adapter = GeminiAdapter()
        result = adapter.serialize(config)
        
        self.assertEqual(result["command"], "npx")
        self.assertEqual(result["args"], ["mcp-server"])
        self.assertEqual(result["cwd"], "/workspace")
        self.assertEqual(result["timeout"], 30000)
        self.assertNotIn("name", result)
        self.assertNotIn("type", result)

    def test_AS04_gemini_http_serialization(self):
        """AS-04: Gemini HTTP config serializes correctly."""
        config = MCPServerConfig(
            name="gemini-http",
            httpUrl="https://api.example.com/http",
            trust=True,
        )
        
        adapter = GeminiAdapter()
        result = adapter.serialize(config)
        
        self.assertEqual(result["httpUrl"], "https://api.example.com/http")
        self.assertEqual(result["trust"], True)
        self.assertNotIn("name", result)
        self.assertNotIn("type", result)


class TestVSCodeAdapterSerialization(unittest.TestCase):
    """Integration tests for VS Code adapter serialization."""

    def test_AS05_vscode_with_envfile(self):
        """AS-05: VS Code config with envFile serializes correctly."""
        config = MCPServerConfig(
            name="vscode-server",
            command="node",
            args=["server.js"],
            envFile=".env",
            type="stdio",
        )
        
        adapter = VSCodeAdapter()
        result = adapter.serialize(config)
        
        self.assertEqual(result["command"], "node")
        self.assertEqual(result["envFile"], ".env")
        self.assertEqual(result["type"], "stdio")
        self.assertNotIn("name", result)


class TestCodexAdapterSerialization(unittest.TestCase):
    """Integration tests for Codex adapter serialization."""

    def test_AS06_codex_stdio_serialization(self):
        """AS-06: Codex stdio config serializes correctly (no type field).

        Note: Codex maps 'args' to 'arguments' and 'headers' to 'http_headers'.
        """
        config = MCPServerConfig(
            name="codex-server",
            command="python",
            args=["server.py"],
            env={"DEBUG": "true"},
        )

        adapter = CodexAdapter()
        result = adapter.serialize(config)

        self.assertEqual(result["command"], "python")
        # Codex uses 'arguments' instead of 'args'
        self.assertEqual(result["arguments"], ["server.py"])
        self.assertNotIn("args", result)  # Original name should not be present
        self.assertEqual(result["env"], {"DEBUG": "true"})
        self.assertNotIn("name", result)
        self.assertNotIn("type", result)


class TestKiroAdapterSerialization(unittest.TestCase):
    """Integration tests for Kiro adapter serialization."""

    def test_AS07_kiro_stdio_serialization(self):
        """AS-07: Kiro stdio config serializes correctly."""
        config = MCPServerConfig(
            name="kiro-server",
            command="npx",
            args=["@modelcontextprotocol/server"],
        )
        
        adapter = KiroAdapter()
        result = adapter.serialize(config)
        
        self.assertEqual(result["command"], "npx")
        self.assertEqual(result["args"], ["@modelcontextprotocol/server"])
        self.assertNotIn("name", result)
        self.assertNotIn("type", result)


if __name__ == "__main__":
    unittest.main()

