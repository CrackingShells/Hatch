"""
Tests for host-specific CLI arguments in MCP configure command.

This module tests the new host-specific CLI arguments added in Phase 2:
- --timeout (Gemini)
- --trust (Gemini)
- --cwd (Gemini)
- --env-file (Cursor, VS Code)
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from hatch.cli_hatch import handle_mcp_configure
from hatch.mcp_host_config import MCPHostType
from hatch.mcp_host_config.models import MCPServerConfigGemini, MCPServerConfigCursor, MCPServerConfigVSCode


class TestGeminiHostSpecificArguments(unittest.TestCase):
    """Test Gemini-specific CLI arguments."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_gemini_timeout_argument(self, mock_manager_class):
        """Test --timeout argument for Gemini host."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object with success attribute
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            timeout=30000,  # 30 seconds
            auto_approve=True
        )

        self.assertEqual(result, 0)
        self.assertTrue(mock_manager.configure_server.called)

        # Verify timeout was passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.timeout, 30000)

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_gemini_trust_argument(self, mock_manager_class):
        """Test --trust argument for Gemini host."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            trust=True,
            auto_approve=True
        )

        self.assertEqual(result, 0)

        # Verify trust was passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.trust, True)

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_gemini_cwd_argument(self, mock_manager_class):
        """Test --cwd argument for Gemini host."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            cwd='/path/to/working/dir',
            auto_approve=True
        )

        self.assertEqual(result, 0)

        # Verify cwd was passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.cwd, '/path/to/working/dir')

    def test_configure_timeout_non_gemini_host_fails(self):
        """Test --timeout argument fails for non-Gemini hosts."""
        result = handle_mcp_configure(
            host='claude-desktop',
            server_name='test-server',
            command='python',
            args=['server.py'],
            timeout=30000,
            auto_approve=True
        )

        self.assertEqual(result, 1)  # Should fail

    def test_configure_trust_non_gemini_host_fails(self):
        """Test --trust argument fails for non-Gemini hosts."""
        result = handle_mcp_configure(
            host='cursor',
            server_name='test-server',
            command='python',
            args=['server.py'],
            trust=True,
            auto_approve=True
        )

        self.assertEqual(result, 1)  # Should fail

    def test_configure_cwd_non_gemini_host_fails(self):
        """Test --cwd argument fails for non-Gemini hosts."""
        result = handle_mcp_configure(
            host='vscode',
            server_name='test-server',
            command='python',
            args=['server.py'],
            cwd='/path/to/dir',
            auto_approve=True
        )

        self.assertEqual(result, 1)  # Should fail


class TestCursorVSCodeHostSpecificArguments(unittest.TestCase):
    """Test Cursor and VS Code-specific CLI arguments."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_cursor_envFile_argument(self, mock_manager_class):
        """Test --env-file argument for Cursor host."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='cursor',
            server_name='test-server',
            command='python',
            args=['server.py'],
            env_file='.env',
            auto_approve=True
        )

        self.assertEqual(result, 0)

        # Verify envFile was passed to Cursor model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigCursor)
        self.assertEqual(server_config.envFile, '.env')

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_vscode_envFile_argument(self, mock_manager_class):
        """Test --env-file argument for VS Code host."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='vscode',
            server_name='test-server',
            command='python',
            args=['server.py'],
            env_file='${workspaceFolder}/.env',
            auto_approve=True
        )

        self.assertEqual(result, 0)

        # Verify envFile was passed to VS Code model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigVSCode)
        self.assertEqual(server_config.envFile, '${workspaceFolder}/.env')

    def test_configure_envFile_non_supported_host_fails(self):
        """Test --env-file argument fails for non-supported hosts."""
        result = handle_mcp_configure(
            host='claude-desktop',
            server_name='test-server',
            command='python',
            args=['server.py'],
            env_file='.env',
            auto_approve=True
        )

        self.assertEqual(result, 1)  # Should fail

    def test_configure_envFile_gemini_host_fails(self):
        """Test --env-file argument fails for Gemini host."""
        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            env_file='.env',
            auto_approve=True
        )

        self.assertEqual(result, 1)  # Should fail


class TestHostSpecificArgumentsCombinations(unittest.TestCase):
    """Test combinations of host-specific arguments."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_gemini_multiple_host_specific_args(self, mock_manager_class):
        """Test multiple Gemini-specific arguments together."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            timeout=15000,
            trust=True,
            cwd='/workspace',
            auto_approve=True
        )

        self.assertEqual(result, 0)

        # Verify all fields were passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.timeout, 15000)
        self.assertEqual(server_config.trust, True)
        self.assertEqual(server_config.cwd, '/workspace')

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_configure_host_specific_args_with_universal_fields(self, mock_manager_class):
        """Test host-specific arguments combined with universal fields."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        # Mock the result object
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py', '--port', '8080'],
            env=['API_KEY=secret', 'DEBUG=true'],
            timeout=30000,
            trust=True,
            auto_approve=True
        )

        self.assertEqual(result, 0)

        # Verify both universal and host-specific fields
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.command, 'python')
        self.assertEqual(server_config.args, ['server.py', '--port', '8080'])
        self.assertEqual(server_config.env, {'API_KEY': 'secret', 'DEBUG': 'true'})
        self.assertEqual(server_config.timeout, 30000)
        self.assertEqual(server_config.trust, True)


if __name__ == '__main__':
    unittest.main()

