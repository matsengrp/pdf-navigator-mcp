# PDF Navigator MCP Project Instructions

## IMPORTANT: Virtual Environment

**ALWAYS use the virtual environment for this project!**

Before running any Python commands, ensure the virtual environment is activated:
```bash
source /Users/matsen/re/pdf-navigator-mcp/.venv/bin/activate
```

Or use the virtual environment's executables directly:
- Python: `.venv/bin/python3`
- Pip: `.venv/bin/pip`
- Pytest: `.venv/bin/pytest`

## Project Structure

This is a Model Context Protocol (MCP) server for PDF reading and navigation.

Key files:
- `pdf_navigator_mcp/pdf_navigator.py` - Core PDF functionality
- `pdf_navigator_mcp/server.py` - MCP server implementation
- `tests/` - Test files

## Testing

Run tests using:
```bash
.venv/bin/pytest tests/
```

## Development Workflow

1. Always ensure changes work with the existing tests
2. Add tests for new functionality
3. Use type hints for better code clarity
4. Follow the existing code style