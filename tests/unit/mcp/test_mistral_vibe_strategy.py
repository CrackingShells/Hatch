"""Unit tests for Mistral Vibe host strategy."""

import os
import tempfile
import tomllib
import unittest
from pathlib import Path

from hatch.mcp_host_config.models import HostConfiguration, MCPServerConfig
from hatch.mcp_host_config.strategies import MistralVibeHostStrategy


class TestMistralVibeHostStrategy(unittest.TestCase):
    """Verify Mistral Vibe TOML read/write behavior."""

    def test_read_configuration_parses_array_of_tables(self):
        """Reads [[mcp_servers]] entries into HostConfiguration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_dir = Path(tmpdir) / ".vibe"
                config_dir.mkdir()
                (config_dir / "config.toml").write_text(
                    'model = "mistral-medium"\n\n'
                    "[[mcp_servers]]\n"
                    'name = "weather"\n'
                    'transport = "streamable-http"\n'
                    'url = "https://example.com/mcp"\n'
                    'prompt = "Be concise"\n',
                    encoding="utf-8",
                )

                strategy = MistralVibeHostStrategy()
                result = strategy.read_configuration()

                self.assertIn("weather", result.servers)
                server = result.servers["weather"]
                self.assertEqual(server.transport, "streamable-http")
                self.assertEqual(server.type, "http")
                self.assertEqual(server.url, "https://example.com/mcp")
                self.assertEqual(server.prompt, "Be concise")
            finally:
                os.chdir(cwd)

    def test_write_configuration_preserves_other_top_level_keys(self):
        """Writes mcp_servers while preserving unrelated Vibe settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                config_dir = Path(tmpdir) / ".vibe"
                config_dir.mkdir()
                config_path = config_dir / "config.toml"
                config_path.write_text(
                    'model = "mistral-medium"\n' 'theme = "dark"\n',
                    encoding="utf-8",
                )

                strategy = MistralVibeHostStrategy()
                config = HostConfiguration(
                    servers={
                        "weather": MCPServerConfig(
                            name="weather",
                            url="https://example.com/mcp",
                            transport="streamable-http",
                            headers={"Authorization": "Bearer token"},
                        )
                    }
                )

                self.assertTrue(strategy.write_configuration(config, no_backup=True))

                with open(config_path, "rb") as f:
                    written = tomllib.load(f)

                self.assertEqual(written["model"], "mistral-medium")
                self.assertEqual(written["theme"], "dark")
                self.assertEqual(written["mcp_servers"][0]["name"], "weather")
                self.assertEqual(
                    written["mcp_servers"][0]["transport"], "streamable-http"
                )
                self.assertEqual(
                    written["mcp_servers"][0]["url"], "https://example.com/mcp"
                )
            finally:
                os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
