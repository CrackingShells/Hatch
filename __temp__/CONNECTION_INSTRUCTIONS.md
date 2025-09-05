# MCP Server Connection Instructions

## For Claude Desktop

1. **Locate your Claude Desktop config file**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add the server configuration** to your config file:
   ```json
   {
     "mcpServers": {
       "first_mcp_pkg": {
         "command": "/opt/homebrew/opt/python@3.10/bin/python3.10",
         "args": ["/Users/rahul/Softwares/hatchling/Hatchling-0.4.3/Hatch_Pkg_Dev/first_mcp_pkg/standalone_mcp_server.py"],
         "env": {}
       }
     }
   }
   ```