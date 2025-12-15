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

from hatch.cli_hatch import handle_mcp_configure, parse_input
from hatch.mcp_host_config import MCPHostType
from hatch.mcp_host_config.models import (
    MCPServerConfigGemini, MCPServerConfigCursor, MCPServerConfigVSCode,
    MCPServerConfigClaude, MCPServerConfigCodex
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
            input=['promptString,api-key,API Key,password=true'],  # VS Code-only field
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

    def test_parse_input_basic(self):
        """Test basic input parsing."""
        input_list = ['promptString,api-key,GitHub Personal Access Token']
        result = parse_input(input_list)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'promptString')
        self.assertEqual(result[0]['id'], 'api-key')
        self.assertEqual(result[0]['description'], 'GitHub Personal Access Token')
        self.assertNotIn('password', result[0])

    def test_parse_input_with_password(self):
        """Test input parsing with password flag."""
        input_list = ['promptString,api-key,API Key,password=true']
        result = parse_input(input_list)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['password'], True)

    def test_parse_input_multiple(self):
        """Test parsing multiple inputs."""
        input_list = [
            'promptString,api-key,API Key,password=true',
            'promptString,db-url,Database URL'
        ]
        result = parse_input(input_list)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)

    def test_parse_input_none(self):
        """Test parsing None inputs."""
        result = parse_input(None)
        self.assertIsNone(result)

    def test_parse_input_empty(self):
        """Test parsing empty inputs list."""
        result = parse_input([])
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
            input=['promptString,api-key,API Key,password=true'],
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


class TestAllCodexArguments(unittest.TestCase):
    """Test ALL Codex-specific CLI arguments."""

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_all_codex_arguments_accepted(self, mock_stdout, mock_manager_class):
        """Test that all Codex arguments are accepted and passed to model."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        # Test STDIO server with Codex-specific STDIO fields
        result = handle_mcp_configure(
            host='codex',
            server_name='test-server',
            command='npx',
            args=['-y', '@upstash/context7-mcp'],
            env_vars=['PATH', 'HOME'],
            cwd='/workspace',
            startup_timeout=15,
            tool_timeout=120,
            enabled=True,
            include_tools=['read', 'write'],
            exclude_tools=['delete'],
            auto_approve=True
        )

        # Verify success
        self.assertEqual(result, 0)

        # Verify configure_server was called
        mock_manager.configure_server.assert_called_once()

        # Verify server_config is MCPServerConfigCodex
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertIsInstance(server_config, MCPServerConfigCodex)

        # Verify Codex-specific STDIO fields
        self.assertEqual(server_config.env_vars, ['PATH', 'HOME'])
        self.assertEqual(server_config.cwd, '/workspace')
        self.assertEqual(server_config.startup_timeout_sec, 15)
        self.assertEqual(server_config.tool_timeout_sec, 120)
        self.assertTrue(server_config.enabled)
        self.assertEqual(server_config.enabled_tools, ['read', 'write'])
        self.assertEqual(server_config.disabled_tools, ['delete'])

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_codex_env_vars_list(self, mock_stdout, mock_manager_class):
        """Test that env_vars accepts multiple values as a list."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='codex',
            server_name='test-server',
            command='npx',
            args=['-y', 'package'],
            env_vars=['PATH', 'HOME', 'USER'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertEqual(server_config.env_vars, ['PATH', 'HOME', 'USER'])

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_codex_env_header_parsing(self, mock_stdout, mock_manager_class):
        """Test that env_header parses KEY=ENV_VAR format correctly."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='codex',
            server_name='test-server',
            command='npx',
            args=['-y', 'package'],
            env_header=['X-API-Key=API_KEY', 'Authorization=AUTH_TOKEN'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertEqual(server_config.env_http_headers, {
            'X-API-Key': 'API_KEY',
            'Authorization': 'AUTH_TOKEN'
        })

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_codex_timeout_fields(self, mock_stdout, mock_manager_class):
        """Test that timeout fields are passed as integers."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='codex',
            server_name='test-server',
            command='npx',
            args=['-y', 'package'],
            startup_timeout=30,
            tool_timeout=180,
            auto_approve=True
        )

        self.assertEqual(result, 0)
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertEqual(server_config.startup_timeout_sec, 30)
        self.assertEqual(server_config.tool_timeout_sec, 180)

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_codex_enabled_flag(self, mock_stdout, mock_manager_class):
        """Test that enabled flag works as boolean."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='codex',
            server_name='test-server',
            command='npx',
            args=['-y', 'package'],
            enabled=True,
            auto_approve=True
        )

        self.assertEqual(result, 0)
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']
        self.assertTrue(server_config.enabled)

    @patch('hatch.cli_hatch.MCPHostConfigurationManager')
    @patch('sys.stdout', new_callable=StringIO)
    def test_codex_reuses_shared_arguments(self, mock_stdout, mock_manager_class):
        """Test that Codex reuses shared arguments (cwd, include-tools, exclude-tools)."""
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.backup_path = None
        mock_manager.configure_server.return_value = mock_result

        result = handle_mcp_configure(
            host='codex',
            server_name='test-server',
            command='npx',
            args=['-y', 'package'],
            cwd='/workspace',
            include_tools=['tool1', 'tool2'],
            exclude_tools=['tool3'],
            auto_approve=True
        )

        self.assertEqual(result, 0)
        call_args = mock_manager.configure_server.call_args
        server_config = call_args.kwargs['server_config']

        # Verify shared arguments work for Codex STDIO servers
        self.assertEqual(server_config.cwd, '/workspace')
        self.assertEqual(server_config.enabled_tools, ['tool1', 'tool2'])
        self.assertEqual(server_config.disabled_tools, ['tool3'])


if __name__ == '__main__':
    unittest.main()

