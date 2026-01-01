"""
Kiro MCP CLI Integration Tests

Tests for CLI argument parsing and integration with Kiro-specific arguments.

Updated for M1.8: Uses Namespace-based handler calls via create_mcp_configure_args.
"""

import unittest
from unittest.mock import patch, MagicMock

from wobble.decorators import regression_test

from hatch.cli.cli_mcp import handle_mcp_configure
from tests.cli_test_utils import create_mcp_configure_args


class TestKiroCLIIntegration(unittest.TestCase):
    """Test suite for Kiro CLI argument integration."""
    
    @patch('hatch.cli.cli_mcp.MCPHostConfigurationManager')
    @regression_test
    def test_kiro_cli_with_disabled_flag(self, mock_manager_class):
        """Test CLI with --disabled flag for Kiro."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result
        
        args = create_mcp_configure_args(
            host='kiro',
            server_name='test-server',
            server_command='auggie',
            args=['--mcp'],
            disabled=True,
            auto_approve=True,
        )
        
        result = handle_mcp_configure(args)
        self.assertEqual(result, 0)
        
        mock_manager.configure_server.assert_called_once()
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertTrue(server_config.disabled)
    
    @patch('hatch.cli.cli_mcp.MCPHostConfigurationManager')
    @regression_test
    def test_kiro_cli_with_auto_approve_tools(self, mock_manager_class):
        """Test CLI with --auto-approve-tools for Kiro."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_manager.configure_server.return_value = mock_result
        
        args = create_mcp_configure_args(
            host='kiro',
            server_name='test-server',
            server_command='auggie',
            args=['--mcp'],
            auto_approve_tools=['codebase-retrieval', 'fetch'],
            auto_approve=True,
        )
        
        result = handle_mcp_configure(args)
        self.assertEqual(result, 0)
        
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertEqual(len(server_config.autoApprove), 2)
        self.assertIn('codebase-retrieval', server_config.autoApprove)
    
    @patch('hatch.cli.cli_mcp.MCPHostConfigurationManager')
    @regression_test
    def test_kiro_cli_with_disable_tools(self, mock_manager_class):
        """Test CLI with --disable-tools for Kiro."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_manager.configure_server.return_value = mock_result
        
        args = create_mcp_configure_args(
            host='kiro',
            server_name='test-server',
            server_command='python',
            args=['server.py'],
            disable_tools=['dangerous-tool', 'risky-tool'],
            auto_approve=True,
        )
        
        result = handle_mcp_configure(args)
        self.assertEqual(result, 0)
        
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertEqual(len(server_config.disabledTools), 2)
        self.assertIn('dangerous-tool', server_config.disabledTools)
    
    @patch('hatch.cli.cli_mcp.MCPHostConfigurationManager')
    @regression_test
    def test_kiro_cli_combined_arguments(self, mock_manager_class):
        """Test CLI with multiple Kiro-specific arguments combined."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_manager.configure_server.return_value = mock_result
        
        args = create_mcp_configure_args(
            host='kiro',
            server_name='comprehensive-server',
            server_command='auggie',
            args=['--mcp', '-m', 'default'],
            disabled=False,
            auto_approve_tools=['codebase-retrieval'],
            disable_tools=['dangerous-tool'],
            auto_approve=True,
        )
        
        result = handle_mcp_configure(args)
        self.assertEqual(result, 0)
        
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        
        self.assertFalse(server_config.disabled)
        self.assertEqual(len(server_config.autoApprove), 1)
        self.assertEqual(len(server_config.disabledTools), 1)
        self.assertIn('codebase-retrieval', server_config.autoApprove)
        self.assertIn('dangerous-tool', server_config.disabledTools)


if __name__ == '__main__':
    unittest.main()
