"""Unit tests for adapter registry.

Test IDs: AR-01 to AR-08 (per 02-test_architecture_rebuild_v0.md)
Scope: Registry initialization, adapter lookup, registration.
"""

import unittest

from hatch.mcp_host_config.adapters import (
    AdapterRegistry,
    get_adapter,
    get_default_registry,
    BaseAdapter,
    ClaudeAdapter,
    CodexAdapter,
    CursorAdapter,
    GeminiAdapter,
    KiroAdapter,
    LMStudioAdapter,
    VSCodeAdapter,
)


class TestAdapterRegistry(unittest.TestCase):
    """Tests for AdapterRegistry class (AR-01 to AR-08)."""

    def setUp(self):
        """Create a fresh registry for each test."""
        self.registry = AdapterRegistry()

    def test_AR01_registry_has_all_default_hosts(self):
        """AR-01: Registry initializes with all default host adapters."""
        expected_hosts = {
            "claude-desktop",
            "claude-code",
            "codex",
            "cursor",
            "gemini",
            "kiro",
            "lmstudio",
            "vscode",
        }
        
        actual_hosts = set(self.registry.get_supported_hosts())
        
        self.assertEqual(actual_hosts, expected_hosts)

    def test_AR02_get_adapter_returns_correct_type(self):
        """AR-02: get_adapter() returns adapter with matching host_name."""
        test_cases = [
            ("claude-desktop", ClaudeAdapter),
            ("claude-code", ClaudeAdapter),
            ("codex", CodexAdapter),
            ("cursor", CursorAdapter),
            ("gemini", GeminiAdapter),
            ("kiro", KiroAdapter),
            ("lmstudio", LMStudioAdapter),
            ("vscode", VSCodeAdapter),
        ]
        
        for host_name, expected_cls in test_cases:
            with self.subTest(host=host_name):
                adapter = self.registry.get_adapter(host_name)
                self.assertIsInstance(adapter, expected_cls)
                self.assertEqual(adapter.host_name, host_name)

    def test_AR03_get_adapter_raises_for_unknown_host(self):
        """AR-03: get_adapter() raises KeyError for unknown host."""
        with self.assertRaises(KeyError) as context:
            self.registry.get_adapter("unknown-host")
        
        self.assertIn("unknown-host", str(context.exception))
        self.assertIn("Supported hosts", str(context.exception))

    def test_AR04_has_adapter_returns_true_for_registered(self):
        """AR-04: has_adapter() returns True for registered hosts."""
        for host_name in self.registry.get_supported_hosts():
            with self.subTest(host=host_name):
                self.assertTrue(self.registry.has_adapter(host_name))

    def test_AR05_has_adapter_returns_false_for_unknown(self):
        """AR-05: has_adapter() returns False for unknown hosts."""
        self.assertFalse(self.registry.has_adapter("unknown-host"))

    def test_AR06_register_adds_new_adapter(self):
        """AR-06: register() adds a new adapter to registry."""
        # Create a custom adapter for testing
        class CustomAdapter(BaseAdapter):
            @property
            def host_name(self):
                return "custom-host"
            
            def get_supported_fields(self):
                return frozenset({"command", "args"})
            
            def validate(self, config):
                pass
            
            def serialize(self, config):
                return {"command": config.command}
        
        custom = CustomAdapter()
        self.registry.register(custom)
        
        self.assertTrue(self.registry.has_adapter("custom-host"))
        self.assertIs(self.registry.get_adapter("custom-host"), custom)

    def test_AR07_register_raises_for_duplicate(self):
        """AR-07: register() raises ValueError for duplicate host name."""
        # Try to register another Claude adapter
        duplicate = ClaudeAdapter(variant="desktop")
        
        with self.assertRaises(ValueError) as context:
            self.registry.register(duplicate)
        
        self.assertIn("claude-desktop", str(context.exception))
        self.assertIn("already registered", str(context.exception))

    def test_AR08_unregister_removes_adapter(self):
        """AR-08: unregister() removes adapter from registry."""
        self.assertTrue(self.registry.has_adapter("claude-desktop"))
        
        self.registry.unregister("claude-desktop")
        
        self.assertFalse(self.registry.has_adapter("claude-desktop"))

    def test_unregister_raises_for_unknown(self):
        """unregister() raises KeyError for unknown host."""
        with self.assertRaises(KeyError):
            self.registry.unregister("unknown-host")


class TestGlobalRegistryFunctions(unittest.TestCase):
    """Tests for global registry convenience functions."""

    def test_get_default_registry_returns_singleton(self):
        """get_default_registry() returns same instance on multiple calls."""
        registry1 = get_default_registry()
        registry2 = get_default_registry()
        
        self.assertIs(registry1, registry2)

    def test_get_adapter_uses_default_registry(self):
        """get_adapter() function uses the default registry."""
        adapter = get_adapter("claude-desktop")
        
        self.assertIsInstance(adapter, ClaudeAdapter)
        self.assertEqual(adapter.host_name, "claude-desktop")

    def test_get_adapter_raises_for_unknown(self):
        """get_adapter() function raises KeyError for unknown host."""
        with self.assertRaises(KeyError):
            get_adapter("unknown-host")


if __name__ == "__main__":
    unittest.main()

