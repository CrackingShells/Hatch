"""
Test suite for decorator-based host registry.

This module tests the decorator-based strategy registration system
following Hatchling patterns with inheritance validation.
"""

import unittest
import sys
from pathlib import Path

# Add the parent directory to the path to import wobble
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from wobble.decorators import regression_test, integration_test
except ImportError:
    # Fallback decorators if wobble is not available
    def regression_test(func):
        return func
    
    def integration_test(scope="component"):
        def decorator(func):
            return func
        return decorator

from hatch.mcp_host_config.host_management import MCPHostRegistry, register_host_strategy, MCPHostStrategy
from hatch.mcp_host_config.models import MCPHostType, MCPServerConfig, HostConfiguration
from pathlib import Path


class TestMCPHostRegistryDecorator(unittest.TestCase):
    """Test suite for decorator-based host registry."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear registry before each test
        MCPHostRegistry._strategies.clear()
        MCPHostRegistry._instances.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        # Clear registry after each test
        MCPHostRegistry._strategies.clear()
        MCPHostRegistry._instances.clear()
    
    @regression_test
    def test_decorator_registration_functionality(self):
        """Test that decorator registration works correctly."""
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class TestClaudeStrategy(MCPHostStrategy):
            def get_config_path(self): 
                return Path("/test/path")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        # Verify registration
        self.assertIn(MCPHostType.CLAUDE_DESKTOP, MCPHostRegistry._strategies)
        self.assertEqual(
            MCPHostRegistry._strategies[MCPHostType.CLAUDE_DESKTOP],
            TestClaudeStrategy
        )
        
        # Verify instance creation
        strategy = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        self.assertIsInstance(strategy, TestClaudeStrategy)
    
    @regression_test
    def test_decorator_registration_with_inheritance(self):
        """Test decorator registration with inheritance patterns."""
        
        class TestClaudeBase(MCPHostStrategy):
            def __init__(self):
                self.company_origin = "Anthropic"
                self.config_format = "claude_format"
            
            def get_config_key(self):
                return "mcpServers"
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class TestClaudeDesktop(TestClaudeBase):
            def get_config_path(self): 
                return Path("/test/claude")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        strategy = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        
        # Verify inheritance properties
        self.assertEqual(strategy.company_origin, "Anthropic")
        self.assertEqual(strategy.config_format, "claude_format")
        self.assertEqual(strategy.get_config_key(), "mcpServers")
        self.assertIsInstance(strategy, TestClaudeBase)
    
    @regression_test
    def test_decorator_registration_duplicate_warning(self):
        """Test warning on duplicate strategy registration."""
        import logging
        
        class BaseTestStrategy(MCPHostStrategy):
            def get_config_path(self): 
                return Path("/test")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class FirstStrategy(BaseTestStrategy):
            pass
        
        # Register second strategy for same host type - should log warning
        with self.assertLogs('hatch.mcp_host_config.host_management', level='WARNING') as log:
            @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
            class SecondStrategy(BaseTestStrategy):
                pass
        
        # Verify warning was logged
        self.assertTrue(any("Overriding existing strategy" in message for message in log.output))
        
        # Verify second strategy is now registered
        strategy = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        self.assertIsInstance(strategy, SecondStrategy)
    
    @regression_test
    def test_decorator_registration_inheritance_validation(self):
        """Test that decorator validates inheritance from MCPHostStrategy."""
        
        # Should raise ValueError for non-MCPHostStrategy class
        with self.assertRaises(ValueError) as context:
            @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
            class InvalidStrategy:  # Does not inherit from MCPHostStrategy
                pass
        
        self.assertIn("must inherit from MCPHostStrategy", str(context.exception))
    
    @regression_test
    def test_registry_get_strategy_unknown_host_type(self):
        """Test error handling for unknown host type."""
        # Clear registry to ensure no strategies are registered
        MCPHostRegistry._strategies.clear()
        
        with self.assertRaises(ValueError) as context:
            MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        
        self.assertIn("Unknown host type", str(context.exception))
        self.assertIn("Available: []", str(context.exception))
    
    @regression_test
    def test_registry_singleton_instance_behavior(self):
        """Test that registry returns singleton instances."""
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class TestStrategy(MCPHostStrategy):
            def __init__(self):
                self.instance_id = id(self)
            
            def get_config_path(self): 
                return Path("/test")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        # Get strategy multiple times
        strategy1 = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        strategy2 = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        
        # Should be the same instance
        self.assertIs(strategy1, strategy2)
        self.assertEqual(strategy1.instance_id, strategy2.instance_id)
    
    @regression_test
    def test_registry_detect_available_hosts(self):
        """Test host detection functionality."""
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class AvailableStrategy(MCPHostStrategy):
            def get_config_path(self): 
                return Path("/test")
            def is_host_available(self): 
                return True  # Available
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        @register_host_strategy(MCPHostType.CURSOR)
        class UnavailableStrategy(MCPHostStrategy):
            def get_config_path(self): 
                return Path("/test")
            def is_host_available(self): 
                return False  # Not available
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        @register_host_strategy(MCPHostType.VSCODE)
        class ErrorStrategy(MCPHostStrategy):
            def get_config_path(self): 
                return Path("/test")
            def is_host_available(self): 
                raise Exception("Detection error")  # Error during detection
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        available_hosts = MCPHostRegistry.detect_available_hosts()
        
        # Only the available strategy should be detected
        self.assertIn(MCPHostType.CLAUDE_DESKTOP, available_hosts)
        self.assertNotIn(MCPHostType.CURSOR, available_hosts)
        self.assertNotIn(MCPHostType.VSCODE, available_hosts)
    
    @regression_test
    def test_registry_family_mappings(self):
        """Test family host mappings."""
        claude_family = MCPHostRegistry.get_family_hosts("claude")
        cursor_family = MCPHostRegistry.get_family_hosts("cursor")
        unknown_family = MCPHostRegistry.get_family_hosts("unknown")
        
        # Verify family mappings
        self.assertIn(MCPHostType.CLAUDE_DESKTOP, claude_family)
        self.assertIn(MCPHostType.CLAUDE_CODE, claude_family)
        self.assertIn(MCPHostType.CURSOR, cursor_family)
        self.assertIn(MCPHostType.LMSTUDIO, cursor_family)
        self.assertEqual(unknown_family, [])
    
    @regression_test
    def test_registry_get_host_config_path(self):
        """Test getting host configuration path through registry."""
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class TestStrategy(MCPHostStrategy):
            def get_config_path(self): 
                return Path("/test/claude/config.json")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
            def validate_server_config(self, server_config): 
                return True
        
        config_path = MCPHostRegistry.get_host_config_path(MCPHostType.CLAUDE_DESKTOP)
        self.assertEqual(config_path, Path("/test/claude/config.json"))


class TestFamilyBasedStrategyRegistration(unittest.TestCase):
    """Test suite for family-based strategy registration with decorators."""
    
    def setUp(self):
        """Set up test environment."""
        # Clear registry before each test
        MCPHostRegistry._strategies.clear()
        MCPHostRegistry._instances.clear()
    
    def tearDown(self):
        """Clean up test environment."""
        # Clear registry after each test
        MCPHostRegistry._strategies.clear()
        MCPHostRegistry._instances.clear()
    
    @regression_test
    def test_claude_family_decorator_registration(self):
        """Test Claude family strategies register with decorators."""
        
        class TestClaudeBase(MCPHostStrategy):
            def __init__(self):
                self.company_origin = "Anthropic"
                self.config_format = "claude_format"
            
            def validate_server_config(self, server_config):
                # Claude family accepts any valid command or URL
                if server_config.command or server_config.url:
                    return True
                return False
        
        @register_host_strategy(MCPHostType.CLAUDE_DESKTOP)
        class TestClaudeDesktop(TestClaudeBase):
            def get_config_path(self): 
                return Path("/test/claude_desktop")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
        
        @register_host_strategy(MCPHostType.CLAUDE_CODE)
        class TestClaudeCode(TestClaudeBase):
            def get_config_path(self): 
                return Path("/test/claude_code")
            def is_host_available(self): 
                return True
            def read_configuration(self): 
                return HostConfiguration()
            def write_configuration(self, config, no_backup=False): 
                return True
        
        # Verify both strategies are registered
        claude_desktop = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_DESKTOP)
        claude_code = MCPHostRegistry.get_strategy(MCPHostType.CLAUDE_CODE)
        
        # Verify inheritance properties
        self.assertEqual(claude_desktop.company_origin, "Anthropic")
        self.assertEqual(claude_code.company_origin, "Anthropic")
        self.assertIsInstance(claude_desktop, TestClaudeBase)
        self.assertIsInstance(claude_code, TestClaudeBase)
        
        # Verify family mappings
        claude_family = MCPHostRegistry.get_family_hosts("claude")
        self.assertIn(MCPHostType.CLAUDE_DESKTOP, claude_family)
        self.assertIn(MCPHostType.CLAUDE_CODE, claude_family)


if __name__ == '__main__':
    unittest.main()
