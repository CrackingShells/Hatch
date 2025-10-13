"""
Tests for ALL host-specific CLI arguments in MCP configure command.

This module tests that:
1. All host-specific arguments are accepted for all hosts
2. Unsupported fields are reported as "UNSUPPORTED" in conversion reports
3. All new arguments (httpUrl, includeTools, excludeTools, inputs) work correctly
"""

import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

from hatch.cli_hatch import handle_mcp_configure, parse_inputs
from hatch.mcp_host_config import MCPHostType
from hatch.mcp_host_config.models import (
    MCPServerConfigGemini, MCPServerConfigCursor, MCPServerConfigVSCode,
    MCPServerConfigClaude
)


class TestAllGeminiArguments(unittest.TestCase):
    """Test ALL Gemini-specific CLI arguments."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_all_gemini_arguments_accepted(self, mock_stdout, mock_manager_class):
        """Test that all Gemini arguments are accepted and passed to model."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            timeout=30000,
            trust=True,
            cwd='/workspace',
            http_url='https://api.example.com/mcp',
            include_tools=['tool1', 'tool2'],
            exclude_tools=['dangerous_tool'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        
        # Verify all fields were passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.timeout, 30000)
        self.assertEqual(server_config.trust, True)
        self.assertEqual(server_config.cwd, '/workspace')
        self.assertEqual(server_config.httpUrl, 'https://api.example.com/mcp')
        self.assertEqual(server_config.includeTools, ['tool1', 'tool2'])
        self.assertEqual(server_config.excludeTools, ['dangerous_tool'])


class TestUnsupportedFieldReporting(unittest.TestCase):
    """Test that unsupported fields are reported correctly, not rejected."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_gemini_args_on_vscode_show_unsupported(self, mock_stdout, mock_manager_class):
        """Test that Gemini-specific args on VS Code show as UNSUPPORTED."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='vscode',
            server_name='test-server',
            command='python',
            args=['server.py'],
            timeout=30000,  # Gemini-only field
            trust=True,     # Gemini-only field
            auto_approve=True
        )

        # Should succeed (not return error code 1)
        self.assertEqual(result, 0)
        
        # Check that output contains "UNSUPPORTED" for Gemini fields
        output = mock_stdout.getvalue()
        self.assertIn('UNSUPPORTED', output)
        self.assertIn('timeout', output)
        self.assertIn('trust', output)

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_vscode_inputs_on_gemini_show_unsupported(self, mock_stdout, mock_manager_class):
        """Test that VS Code inputs on Gemini show as UNSUPPORTED."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            inputs=['promptString,api-key,API Key,password=true'],  # VS Code-only field
            auto_approve=True
        )

        # Should succeed (not return error code 1)
        self.assertEqual(result, 0)
        
        # Check that output contains "UNSUPPORTED" for inputs field
        output = mock_stdout.getvalue()
        self.assertIn('UNSUPPORTED', output)
        self.assertIn('inputs', output)


class TestVSCodeInputsParsing(unittest.TestCase):
    """Test VS Code inputs parsing."""

    def test_parse_inputs_basic(self):
        """Test basic input parsing."""
        inputs_list = ['promptString,api-key,GitHub Personal Access Token']
        result = parse_inputs(inputs_list)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'promptString')
        self.assertEqual(result[0]['id'], 'api-key')
        self.assertEqual(result[0]['description'], 'GitHub Personal Access Token')
        self.assertNotIn('password', result[0])

    def test_parse_inputs_with_password(self):
        """Test input parsing with password flag."""
        inputs_list = ['promptString,api-key,API Key,password=true']
        result = parse_inputs(inputs_list)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['password'], True)

    def test_parse_inputs_multiple(self):
        """Test parsing multiple inputs."""
        inputs_list = [
            'promptString,api-key,API Key,password=true',
            'promptString,db-url,Database URL'
        ]
        result = parse_inputs(inputs_list)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)

    def test_parse_inputs_none(self):
        """Test parsing None inputs."""
        result = parse_inputs(None)
        self.assertIsNone(result)

    def test_parse_inputs_empty(self):
        """Test parsing empty inputs list."""
        result = parse_inputs([])
        self.assertIsNone(result)


class TestVSCodeInputsIntegration(unittest.TestCase):
    """Test VS Code inputs integration with configure command."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_vscode_inputs_passed_to_model(self, mock_manager_class):
        """Test that parsed inputs are passed to VS Code model."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='vscode',
            server_name='test-server',
            command='python',
            args=['server.py'],
            inputs=['promptString,api-key,API Key,password=true'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        
        # Verify inputs were passed to VS Code model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigVSCode)
        self.assertIsNotNone(server_config.inputs)
        self.assertEqual(len(server_config.inputs), 1)
        self.assertEqual(server_config.inputs[0]['id'], 'api-key')


class TestHttpUrlArgument(unittest.TestCase):
    """Test --http-url argument for Gemini."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_http_url_passed_to_gemini(self, mock_manager_class):
        """Test that httpUrl is passed to Gemini model."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            http_url='https://api.example.com/mcp',
            auto_approve=True
        )

        self.assertEqual(result, 0)
        
        # Verify httpUrl was passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.httpUrl, 'https://api.example.com/mcp')


class TestToolFilteringArguments(unittest.TestCase):
    """Test --include-tools and --exclude-tools arguments for Gemini."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_include_tools_passed_to_gemini(self, mock_manager_class):
        """Test that includeTools is passed to Gemini model."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            include_tools=['tool1', 'tool2', 'tool3'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        
        # Verify includeTools was passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.includeTools, ['tool1', 'tool2', 'tool3'])

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    def test_exclude_tools_passed_to_gemini(self, mock_manager_class):
        """Test that excludeTools is passed to Gemini model."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='gemini',
            server_name='test-server',
            command='python',
            args=['server.py'],
            exclude_tools=['dangerous_tool'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        
        # Verify excludeTools was passed to Gemini model
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigGemini)
        self.assertEqual(server_config.excludeTools, ['dangerous_tool'])


if __name__ == '__main__':
    unittest.main()

