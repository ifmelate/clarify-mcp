# Clarify MCP Server

A minimal Model Context Protocol (MCP) server that enables AI agents to ask clarification questions and receive structured user input through a simple Human-in-the-Loop interface.

## Overview

This MCP server exposes a single tool `ask_clarification` that allows AI agents to ask structured questions and receive user input via MCP elicitation. It's compatible with MCP clients like Cursor, VS Code, Claude Desktop, and other MCP-enabled tools.

# DEMO VIDEO:
[![Watch the video](https://github.com/user-attachments/assets/d4a4bf64-091e-4ac1-a52c-5fa20fcd48d6)](https://youtu.be/LmDIg50aGk4?si=n_X9oLd781thRUCo)

## Features

- **Simple Question-Answer Interface**: Ask clarification questions and get concise answers
- **Multiple Choice Support**: Optionally provide predefined choices for users to select from
- **Cross-Client Compatibility**: Works with various MCP clients through adaptive elicitation strategies
- **Pydantic Integration**: Uses Pydantic models for structured data validation

## Installation

### Prerequisites

- Python 3.8 or higher
- `uv` package manager (recommended) or `pip`

### Using uv (Recommended)

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install fastmcp pydantic
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install fastmcp pydantic
```

## Usage

### Running the Server

The server runs using stdio transport for local MCP client integration:

```bash
python hitl_server.py
```

### Client Configuration

Register this server in your MCP-enabled client configuration. The exact configuration varies by client:

#### Cursor

Add to your Cursor MCP configuration (typically in settings):

```json
{
  "mcpServers": {
    "mcp-clarify": {
      "command": "python",
      "args": ["/absolute/path/to/hitl_server.py"],
      "transport": "stdio"
    }
  }
}
```

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent on other platforms:

```json
{
  "mcpServers": {
    "mcp-clarify": {
      "command": "python",
      "args": ["/absolute/path/to/hitl_server.py"]
    }
  }
}
```

#### VS Code with MCP Extension

Configure through the MCP extension settings, pointing to the server executable.

## Tool Reference

### `ask_clarification`

Ask a single clarification question and capture a concise answer.

**Parameters:**

- `prompt` (string, required): The human-visible question to ask
- `choices` (list of strings, optional): Suggested answers for selection

**Returns:**

JSON object with fields:
```json
{
  "question": "The original question text",
  "answer": "User's answer"
}
```

**Example Usage in AI Agent:**

```python
# Simple question
result = await ask_clarification(
    prompt="What is the target latency SLA for this API?"
)

# Multiple choice question
result = await ask_clarification(
    prompt="Which environment should we deploy to?",
    choices=["development", "staging", "production"]
)
```

## How It Works

1. **Question Elicitation**: The server uses FastMCP's elicitation capabilities to present questions to the user
2. **Schema Generation**: When choices are provided, generates JSON schemas with enums for client-side rendering
3. **Answer Parsing**: Handles various response formats including numeric selection ("1", "2") and text matching
4. **Cross-SDK Compatibility**: Tries multiple elicitation signatures to work across different FastMCP versions

## Development

### Project Structure

```
mcp-clarify/
├── hitl_server.py       # Main server implementation
├── README.md            # This file
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Python project metadata
├── LICENSE              # MIT License
├── CONTRIBUTING.md      # Contribution guidelines
├── CODE_OF_CONDUCT.md   # Code of conduct
├── SECURITY.md          # Security policy
└── .github/             # GitHub-specific files
    ├── workflows/       # CI/CD workflows
    ├── ISSUE_TEMPLATE/  # Issue templates
    └── PULL_REQUEST_TEMPLATE.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests (if implemented)
pytest
```

### Contributing

Contributions are welcome! Please ensure your code:

- Follows PEP 8 style guidelines
- Includes appropriate error handling
- Works across different MCP client implementations
- Maintains backward compatibility with existing integrations

## Compatibility

- **Python**: 3.8+
- **MCP SDK**: Compatible with various FastMCP versions through adaptive signatures
- **Pydantic**: Supports both v1 and v2 with compatibility shims
- **Clients**: Tested with Cursor, Claude Desktop, and VS Code MCP extension

## Troubleshooting

### Server Not Starting

- Ensure all dependencies are installed: `pip install fastmcp pydantic`
- Check Python version: `python --version` (should be 3.8+)
- Verify the virtual environment is activated

### Client Can't Connect

- Ensure the path in client configuration points to the correct `hitl_server.py` location
- Use absolute paths in configuration files
- Check that Python is available in the PATH when the client launches the server

### Elicitation Not Working

- Verify your MCP client supports elicitation (check client documentation)
- Try with a simpler question first (no choices parameter)
- Check client logs for error messages

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Open an [issue on GitHub](https://github.com/ifmelate/mcp-clarify/issues)
- Check [existing issues](https://github.com/ifmelate/mcp-clarify/issues) for similar problems
- Review the [MCP specification](https://modelcontextprotocol.io/) for protocol details

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting pull requests.

