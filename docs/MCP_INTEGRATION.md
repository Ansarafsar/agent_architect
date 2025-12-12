# Cerina Protocol Foundry - MCP Integration

## Claude Desktop Configuration

Add this to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "cerina-foundry": {
      "command": "python",
      "args": [
        "-m",
        "backend.mcp.server"
      ],
      "cwd": "C:\\Users\\ANSAR\\agent_architect",
      "env": {
        "DATABASE_URL": "postgresql://postgres:agent123@localhost:5432/cerina_foundry",
        "OPENROUTER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Using from Claude Desktop

Once configured, you can ask Claude:

> "Use Cerina Foundry to create a protocol for managing test anxiety"

> "Generate a CBT protocol for sleep hygiene using the cerina tool"

## Tool Details

**Tool Name**: `cerina.generate_protocol`

**Parameters**:
- `query` (required): Description of the protocol needed
- `max_iterations` (optional): Maximum revision cycles (default: 3)

**Returns**: Formatted markdown with:
- Protocol title and description
- Step-by-step interventions
- Safety considerations
- Contraindications
- Quality metrics

## Testing MCP Server Locally

```bash
# From project root
python -m backend.mcp.server
```

Then send JSON-RPC messages via stdin to test the tool.
