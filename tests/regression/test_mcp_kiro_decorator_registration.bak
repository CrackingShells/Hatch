"""
Kiro MCP Decorator Registration Tests

Tests for automatic strategy registration via @register_host_strategy decorator.
"""

import unittest

from wobble.decorators import regression_test

from hatch.mcp_host_config.host_management import MCPHostRegistry
from hatch.mcp_host_config.models import MCPHostType


class TestKiroDecoratorRegistration(unittest.TestCase):
    """Test suite for Kiro decorator registration."""
    
    @regression_test
    def test_kiro_strategy_registration(self):
        """Test that KiroHostStrategy is properly registered."""
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        
        # Verify Kiro is registered
        self.assertIn(MCPHostType.KIRO, MCPHostRegistry._strategies)
        
        # Verify correct strategy class
        strategy_class = MCPHostRegistry._strategies[MCPHostType.KIRO]
        self.assertEqual(strategy_class.__name__, "KiroHostStrategy")
    
    @regression_test
    def test_kiro_strategy_instantiation(self):
        """Test that Kiro strategy can be instantiated."""
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        
        strategy = MCPHostRegistry.get_strategy(MCPHostType.KIRO)
        
        # Verify strategy instance
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy.__class__.__name__, "KiroHostStrategy")
    
    @regression_test
    def test_kiro_in_host_detection(self):
        """Test that Kiro appears in host detection."""
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        
        # Get all registered host types
        registered_hosts = list(MCPHostRegistry._strategies.keys())
        
        # Verify Kiro is included
        self.assertIn(MCPHostType.KIRO, registered_hosts)
    
    @regression_test
    def test_kiro_registry_consistency(self):
        """Test that Kiro registration is consistent across calls."""
        # Import strategies to trigger registration
        import hatch.mcp_host_config.strategies
        
        # Get strategy multiple times
        strategy1 = MCPHostRegistry.get_strategy(MCPHostType.KIRO)
        strategy2 = MCPHostRegistry.get_strategy(MCPHostType.KIRO)
        
        # Verify same class (not necessarily same instance)
        self.assertEqual(strategy1.__class__, strategy2.__class__)
        self.assertEqual(strategy1.__class__.__name__, "KiroHostStrategy")


if __name__ == '__main__':
    unittest.main()