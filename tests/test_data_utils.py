"""Test data utilities for Hatch test suite.

This module provides utilities for loading test data from static test packages.
All dynamic package generation has been removed in favor of static packages.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


class TestDataLoader:
    """Utility class for loading test data from standardized locations."""
    
    def __init__(self):
        """Initialize the test data loader."""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.configs_dir = self.test_data_dir / "configs"
        self.responses_dir = self.test_data_dir / "responses"
        self.packages_dir = self.test_data_dir / "packages"
        
        # Ensure directories exist
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a test configuration file.
        
        Args:
            config_name: Name of the config file (without .json extension)
            
        Returns:
            Loaded configuration as a dictionary
        """
        config_path = self.configs_dir / f"{config_name}.json"
        if not config_path.exists():
            # Create default config if it doesn't exist
            self._create_default_config(config_name)
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_response(self, response_name: str) -> Dict[str, Any]:
        """Load a mock response file.
        
        Args:
            response_name: Name of the response file (without .json extension)
            
        Returns:
            Loaded response as a dictionary
        """
        response_path = self.responses_dir / f"{response_name}.json"
        if not response_path.exists():
            # Create default response if it doesn't exist
            self._create_default_response(response_name)
        
        with open(response_path, 'r') as f:
            return json.load(f)
    
    def setup(self):
        """Set up test data (placeholder for future setup logic)."""
        # Currently no setup needed as test packages are static
        pass
    
    def cleanup(self):
        """Clean up test data (placeholder for future cleanup logic)."""
        # Currently no cleanup needed as test packages are persistent
        pass
    
    def get_test_packages_dir(self) -> Path:
        """Get the test packages directory path.
        
        Returns:
            Path to the test packages directory
        """
        return self.packages_dir
    
    def _create_default_config(self, config_name: str):
        """Create a default configuration file."""
        default_configs = {
            "test_settings": {
                "test_timeout": 30,
                "temp_dir_prefix": "hatch_test_",
                "cleanup_temp_dirs": True,
                "mock_external_services": True
            },
            "installer_configs": {
                "python_installer": {
                    "pip_timeout": 60,
                    "use_cache": False
                },
                "docker_installer": {
                    "timeout": 120,
                    "cleanup_containers": True
                }
            }
        }
        
        config = default_configs.get(config_name, {})
        config_path = self.configs_dir / f"{config_name}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _create_default_response(self, response_name: str):
        """Create a default response file."""
        default_responses = {
            "registry_responses": {
                "success": {
                    "status": "success",
                    "data": {"packages": []}
                },
                "error": {
                    "status": "error",
                    "message": "Registry not available"
                }
            }
        }
        
        response = default_responses.get(response_name, {})
        response_path = self.responses_dir / f"{response_name}.json"
        with open(response_path, 'w') as f:
            json.dump(response, f, indent=2)

    def load_fixture(self, fixture_name: str) -> Dict[str, Any]:
        """Load a test fixture file.

        Args:
            fixture_name: Name of the fixture file (without .json extension)

        Returns:
            Loaded fixture as a dictionary
        """
        fixtures_dir = self.test_data_dir / "fixtures"
        fixture_path = fixtures_dir / f"{fixture_name}.json"
        with open(fixture_path, 'r') as f:
            return json.load(f)


class NonTTYTestDataLoader(TestDataLoader):
    """Specialized test data loader for non-TTY handling tests."""

    def get_installation_plan(self, plan_name: str) -> Dict[str, Any]:
        """Load standardized installation plan data.

        Args:
            plan_name: Name of the installation plan to load

        Returns:
            Installation plan dictionary
        """
        plans = self.load_fixture("installation_plans")
        return plans.get(plan_name, plans["basic_python_plan"])

    def get_non_tty_config(self) -> Dict[str, Any]:
        """Load non-TTY test configuration.

        Returns:
            Non-TTY test configuration dictionary
        """
        return self.load_config("non_tty_test_config")

    def get_environment_variable_scenarios(self) -> List[Dict[str, Any]]:
        """Get environment variable test scenarios.

        Returns:
            List of environment variable test scenarios
        """
        config = self.get_non_tty_config()
        return config["environment_variables"]["test_scenarios"]

    def get_user_input_scenarios(self) -> Dict[str, List[str]]:
        """Get user input test scenarios.

        Returns:
            Dictionary of user input scenarios
        """
        config = self.get_non_tty_config()
        return config["user_input_scenarios"]

    def get_logging_messages(self) -> Dict[str, str]:
        """Get expected logging messages.

        Returns:
            Dictionary of expected logging messages
        """
        config = self.get_non_tty_config()
        return config["logging_messages"]

class MCPBackupTestDataLoader(TestDataLoader):
    """Specialized test data loader for MCP backup system tests."""

    def __init__(self):
        super().__init__()
        self.mcp_backup_configs_dir = self.configs_dir / "mcp_backup_test_configs"
        self.mcp_backup_configs_dir.mkdir(exist_ok=True)

    def load_host_agnostic_config(self, config_type: str) -> Dict[str, Any]:
        """Load host-agnostic test configuration.

        Args:
            config_type: Type of configuration to load

        Returns:
            Host-agnostic configuration dictionary
        """
        config_path = self.mcp_backup_configs_dir / f"{config_type}.json"
        if not config_path.exists():
            self._create_default_mcp_config(config_type)

        with open(config_path, 'r') as f:
            return json.load(f)

    def _create_default_mcp_config(self, config_type: str):
        """Create default host-agnostic MCP configuration."""
        default_configs = {
            "simple_server": {
                "servers": {
                    "test_server": {
                        "command": "python",
                        "args": ["server.py"]
                    }
                }
            },
            "complex_server": {
                "servers": {
                    "server1": {"command": "python", "args": ["server1.py"]},
                    "server2": {"command": "node", "args": ["server2.js"]},
                    "server3": {"command": "python", "args": ["server3.py"], "env": {"API_KEY": "test"}}
                }
            },
            "empty_config": {"servers": {}}
        }

        config = default_configs.get(config_type, {"servers": {}})
        config_path = self.mcp_backup_configs_dir / f"{config_type}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)


# Global instance for easy access
test_data = TestDataLoader()

# Convenience functions
def load_test_config(config_name: str) -> Dict[str, Any]:
    """Load test configuration."""
    return test_data.load_config(config_name)


def load_mock_response(response_name: str) -> Dict[str, Any]:
    """Load mock response."""
    return test_data.load_response(response_name)


def get_test_packages_dir() -> Path:
    """Get test packages directory."""
    return test_data.get_test_packages_dir()


class MCPHostConfigTestDataLoader(TestDataLoader):
    """Specialized test data loader for MCP host configuration tests v2."""

    def __init__(self):
        super().__init__()
        self.mcp_host_configs_dir = self.configs_dir / "mcp_host_test_configs"
        self.mcp_host_configs_dir.mkdir(exist_ok=True)

    def load_host_config_template(self, host_type: str, config_type: str = "simple") -> Dict[str, Any]:
        """Load host-specific configuration template."""
        config_path = self.mcp_host_configs_dir / f"{host_type}_{config_type}.json"
        if not config_path.exists():
            self._create_host_config_template(host_type, config_type)

        with open(config_path, 'r') as f:
            return json.load(f)

    def load_corrected_environment_data(self, data_type: str = "simple") -> Dict[str, Any]:
        """Load corrected environment data structure (v2)."""
        config_path = self.mcp_host_configs_dir / f"environment_v2_{data_type}.json"
        if not config_path.exists():
            self._create_corrected_environment_data(data_type)

        with open(config_path, 'r') as f:
            return json.load(f)

    def load_mcp_server_config(self, server_type: str = "local") -> Dict[str, Any]:
        """Load consolidated MCPServerConfig templates."""
        config_path = self.mcp_host_configs_dir / f"mcp_server_{server_type}.json"
        if not config_path.exists():
            self._create_mcp_server_config(server_type)

        with open(config_path, 'r') as f:
            return json.load(f)

    def load_kiro_mcp_config(self, config_type: str = "empty") -> Dict[str, Any]:
        """Load Kiro-specific MCP configuration templates.
        
        Args:
            config_type: Type of Kiro configuration to load
                - "empty": Empty mcpServers configuration
                - "with_server": Single server with all Kiro fields
                - "complex": Multi-server with mixed configurations
        
        Returns:
            Kiro MCP configuration dictionary
        """
        config_path = self.mcp_host_configs_dir / f"kiro_mcp_{config_type}.json"
        if not config_path.exists():
            self._create_kiro_mcp_config(config_type)

        with open(config_path, 'r') as f:
            return json.load(f)

    def _create_host_config_template(self, host_type: str, config_type: str):
        """Create host-specific configuration templates with inheritance patterns."""
        templates = {
            # Claude family templates
            "claude-desktop_simple": {
                "mcpServers": {
                    "test_server": {
                        "command": "/usr/local/bin/python",  # Absolute path required
                        "args": ["server.py"],
                        "env": {"API_KEY": "test"}
                    }
                },
                "theme": "dark",  # Claude-specific settings
                "auto_update": True
            },
            "claude-code_simple": {
                "mcpServers": {
                    "test_server": {
                        "command": "/usr/local/bin/python",  # Absolute path required
                        "args": ["server.py"],
                        "env": {}
                    }
                },
                "workspace_settings": {"mcp_enabled": True}  # Claude Code specific
            },

            # Cursor family templates
            "cursor_simple": {
                "mcpServers": {
                    "test_server": {
                        "command": "python",  # Flexible path handling
                        "args": ["server.py"],
                        "env": {"API_KEY": "test"}
                    }
                }
            },
            "cursor_remote": {
                "mcpServers": {
                    "remote_server": {
                        "url": "https://api.example.com/mcp",
                        "headers": {"Authorization": "Bearer token"}
                    }
                }
            },
            "lmstudio_simple": {
                "mcpServers": {
                    "test_server": {
                        "command": "python",  # Inherits Cursor format
                        "args": ["server.py"],
                        "env": {}
                    }
                }
            },

            # Independent strategy templates
            "vscode_simple": {
                "mcp": {
                    "servers": {
                        "test_server": {
                            "command": "python",
                            "args": ["server.py"]
                        }
                    }
                }
            },
            "gemini_simple": {
                "mcpServers": {
                    "test_server": {
                        "command": "python",
                        "args": ["server.py"]
                    }
                }
            },

            # Kiro family templates
            "kiro_simple": {
                "mcpServers": {
                    "test_server": {
                        "command": "auggie",
                        "args": ["--mcp"],
                        "disabled": False,
                        "autoApprove": ["codebase-retrieval"]
                    }
                }
            },
            "kiro_with_server": {
                "mcpServers": {
                    "existing-server": {
                        "command": "auggie",
                        "args": ["--mcp", "-m", "default", "-w", "."],
                        "env": {"DEBUG": "true"},
                        "disabled": False,
                        "autoApprove": ["codebase-retrieval", "fetch"],
                        "disabledTools": ["dangerous-tool"]
                    }
                }
            },
            "kiro_complex": {
                "mcpServers": {
                    "local-server": {
                        "command": "auggie",
                        "args": ["--mcp"],
                        "disabled": False,
                        "autoApprove": ["codebase-retrieval"]
                    },
                    "remote-server": {
                        "url": "https://api.example.com/mcp",
                        "headers": {"Authorization": "Bearer token"},
                        "disabled": True,
                        "disabledTools": ["risky-tool"]
                    }
                },
                "otherSettings": {
                    "theme": "dark",
                    "fontSize": 14
                }
            }
        }

        template_key = f"{host_type}_{config_type}"
        config = templates.get(template_key, {"mcpServers": {}})
        config_path = self.mcp_host_configs_dir / f"{template_key}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _create_corrected_environment_data(self, data_type: str):
        """Create corrected environment data templates (v2 structure)."""
        templates = {
            "simple": {
                "name": "test_environment",
                "description": "Test environment with corrected MCP structure",
                "created_at": "2025-09-21T10:00:00.000000",
                "packages": [
                    {
                        "name": "weather-toolkit",
                        "version": "1.0.0",
                        "type": "hatch",
                        "source": "github:user/weather-toolkit",
                        "installed_at": "2025-09-21T10:00:00.000000",
                        "configured_hosts": {
                            "claude-desktop": {
                                "config_path": "~/Library/Application Support/Claude/claude_desktop_config.json",
                                "configured_at": "2025-09-21T10:00:00.000000",
                                "last_synced": "2025-09-21T10:00:00.000000",
                                "server_config": {
                                    "command": "/usr/local/bin/python",
                                    "args": ["weather.py"],
                                    "env": {"API_KEY": "weather_key"}
                                }
                            }
                        }
                    }
                ]
            },
            "multi_host": {
                "name": "multi_host_environment",
                "description": "Environment with single server configured across multiple hosts",
                "created_at": "2025-09-21T10:00:00.000000",
                "packages": [
                    {
                        "name": "file-manager",
                        "version": "2.0.0",
                        "type": "hatch",
                        "source": "github:user/file-manager",
                        "installed_at": "2025-09-21T10:00:00.000000",
                        "configured_hosts": {
                            "claude-desktop": {
                                "config_path": "~/Library/Application Support/Claude/claude_desktop_config.json",
                                "configured_at": "2025-09-21T10:00:00.000000",
                                "last_synced": "2025-09-21T10:00:00.000000",
                                "server_config": {
                                    "command": "/usr/local/bin/python",
                                    "args": ["file_manager.py"],
                                    "env": {"DEBUG": "true"}
                                }
                            },
                            "cursor": {
                                "config_path": "~/.cursor/mcp.json",
                                "configured_at": "2025-09-21T10:00:00.000000",
                                "last_synced": "2025-09-21T10:00:00.000000",
                                "server_config": {
                                    "command": "python",
                                    "args": ["file_manager.py"],
                                    "env": {"DEBUG": "true"}
                                }
                            }
                        }
                    }
                ]
            }
        }

        config = templates.get(data_type, {"packages": []})
        config_path = self.mcp_host_configs_dir / f"environment_v2_{data_type}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _create_mcp_server_config(self, server_type: str):
        """Create consolidated MCPServerConfig templates."""
        templates = {
            "local": {
                "command": "python",
                "args": ["server.py", "--port", "8080"],
                "env": {"API_KEY": "test", "DEBUG": "true"}
            },
            "remote": {
                "url": "https://api.example.com/mcp",
                "headers": {"Authorization": "Bearer token", "Content-Type": "application/json"}
            },
            "local_minimal": {
                "command": "python",
                "args": ["minimal_server.py"]
            },
            "remote_minimal": {
                "url": "https://minimal.example.com/mcp"
            }
        }

        config = templates.get(server_type, {})
        config_path = self.mcp_host_configs_dir / f"mcp_server_{server_type}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _create_kiro_mcp_config(self, config_type: str):
        """Create Kiro-specific MCP configuration templates."""
        templates = {
            "empty": {
                "mcpServers": {}
            },
            "with_server": {
                "mcpServers": {
                    "existing-server": {
                        "command": "auggie",
                        "args": ["--mcp", "-m", "default", "-w", "."],
                        "env": {"DEBUG": "true"},
                        "disabled": False,
                        "autoApprove": ["codebase-retrieval", "fetch"],
                        "disabledTools": ["dangerous-tool"]
                    }
                }
            },
            "complex": {
                "mcpServers": {
                    "local-server": {
                        "command": "auggie",
                        "args": ["--mcp"],
                        "disabled": False,
                        "autoApprove": ["codebase-retrieval"]
                    },
                    "remote-server": {
                        "url": "https://api.example.com/mcp",
                        "headers": {"Authorization": "Bearer token"},
                        "disabled": True,
                        "disabledTools": ["risky-tool"]
                    }
                },
                "otherSettings": {
                    "theme": "dark",
                    "fontSize": 14
                }
            }
        }
        
        config = templates.get(config_type, {"mcpServers": {}})
        config_path = self.mcp_host_configs_dir / f"kiro_mcp_{config_type}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
