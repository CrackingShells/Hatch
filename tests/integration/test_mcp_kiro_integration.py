"""
Kiro MCP Integration Tests

End-to-end integration tests combining CLI, model conversion, and strategy operations.
"""

import unittest
from unittest.mock import patch, MagicMock

from wobble.decorators import integration_test

from hatch.cli_hatch import handle_mcp_configure
from hatch.mcp_host_config.models import (
    HOST_MODEL_REGISTRY,
    MCPHostType,
    MCPServerConfigKiro
)


class TestKiroIntegration(unittest.TestCase):
    """Test suite for end-to-end Kiro integration."""
    
    @integration_test(scope="component")
    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_kiro_end_to_end_configuration(self, mock_manager_class):
        """Test complete Kiro configuration workflow."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_manager.configure_server.return_value = mock_result
        
        # Execute CLI command with Kiro-specific arguments
        result = handle_mcp_configure(
            host='kiro',
            server_name='augment-server',
            command='auggie',
            args=['--mcp', '-m', 'default'],
            disabled=False,
            auto_approve_tools=['codebase-retrieval', 'fetch'],
            disable_tools=['dangerous-tool'],
            auto_approve=True
        )
        
        # Verify success
        self.assertEqual(result, 0)
        
        # Verify configuration manager was called
        mock_manager.configure_server.assert_called_once()
        
        # Verify server configuration
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        
        # Verify all Kiro-specific fields
        self.assertFalse(server_config.disabled)
        self.assertEqual(len(server_config.autoApprove), 2)
        self.assertEqual(len(server_config.disabledTools), 1)
        self.assertIn('codebase-retrieval', server_config.autoApprove)
        self.assertIn('dangerous-tool', server_config.disabledTools)
    
    @integration_test(scope="system")
    def test_kiro_host_model_registry_integration(self):
        """Test Kiro integration with HOST_MODEL_REGISTRY."""
        # Verify Kiro is in registry
        self.assertIn(MCPHostType.KIRO, HOST_MODEL_REGISTRY)
        
        # Verify correct model class
        model_class = HOST_MODEL_REGISTRY[MCPHostType.KIRO]
        self.assertEqual(model_class.__name__, "MCPServerConfigKiro")
        
        # Test model instantiation
        model_instance = model_class(
            name="test-server",
            command="auggie",
            disabled=True
        )
        self.assertTrue(model_instance.disabled)
    
    @integration_test(scope="component")
    def test_kiro_model_to_strategy_workflow(self):
        """Test workflow from model creation to strategy operations."""
        # Import to trigger registration
        import hatch.mcp_host_config.strategies
        from hatch.mcp_host_config.host_management import MCPHostRegistry
        
        # Create Kiro model
        kiro_model = MCPServerConfigKiro(
            name="workflow-test",
            command="auggie",
            args=["--mcp"],
            disabled=False,
            autoApprove=["codebase-retrieval"]
        )
        
        # Get Kiro strategy
        strategy = MCPHostRegistry.get_strategy(MCPHostType.KIRO)
        
        # Verify strategy can validate the model
        self.assertTrue(strategy.validate_server_config(kiro_model))
        
        # Verify model fields are accessible
        self.assertEqual(kiro_model.command, "auggie")
        self.assertFalse(kiro_model.disabled)
        self.assertIn("codebase-retrieval", kiro_model.autoApprove)
    
    @integration_test(scope="end_to_end")
    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_kiro_complete_lifecycle(self, mock_manager_class):
        """Test complete Kiro server lifecycle: create, configure, validate."""
        # Setup mocks
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_manager.configure_server.return_value = mock_result
        
        # Step 1: Configure server via CLI
        result = handle_mcp_configure(
            host='kiro',
            server_name='lifecycle-test',
            command='auggie',
            args=['--mcp', '-w', '.'],
            disabled=False,
            auto_approve_tools=['codebase-retrieval'],
            auto_approve=True
        )
        
        # Verify CLI success
        self.assertEqual(result, 0)
        
        # Step 2: Verify configuration manager interaction
        mock_manager.configure_server.assert_called_once()
        call_args = mock_manager.configure_server.call_args
        
        # Step 3: Verify server configuration structure
        server_config = call_args.kwargs['server_config']
        self.assertEqual(server_config.name, 'lifecycle-test')
        self.assertEqual(server_config.command, 'auggie')
        self.assertIn('--mcp', server_config.args)
        self.assertIn('-w', server_config.args)
        self.assertFalse(server_config.disabled)
        self.assertIn('codebase-retrieval', server_config.autoApprove)
        
        # Step 4: Verify model type
        self.assertIsInstance(server_config, MCPServerConfigKiro)


if __name__ == '__main__':
    unittest.main()