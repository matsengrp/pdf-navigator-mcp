# PDF Navigator MCP

A comprehensive Model Context Protocol (MCP) server for PDF reading, navigation, and text search with cross-platform PDF viewer integration. Eliminates PyMuPDF dependency issues by providing PDF functionality through MCP.

## Features

- **PDF text extraction** - Read full PDFs or specific pages/ranges
- **PDF structure analysis** - Extract table of contents and page summaries
- **Text search with location** - Find text and jump to results
- **Direct PDF navigation** - Open PDFs to specific pages
- **Cross-platform PDF viewers** - Supports Skim, Zathura, Evince, and more
- **MCP integration** - Works with Claude Code and other MCP clients
- **No dependency issues** - PyMuPDF isolated in MCP server environment

## Installation

```bash
# Install with pipx (recommended)
pipx install git+https://github.com/matsengrp/pdf-navigator-mcp.git

# Or install in current environment
pip install git+https://github.com/matsengrp/pdf-navigator-mcp.git
```

## Claude Code Integration

Add to your `~/.claude.json`:

```json
{
  "mcpServers": {
    "pdf-navigator": {
      "type": "stdio",
      "command": "pdf-navigator-mcp"
    }
  }
}
```

## Usage

In Claude Code, you can:
- **"Read the abstract from paper.pdf"** → Extracts and shows text content
- **"What's the table of contents for paper.pdf?"** → Shows PDF structure
- **"Read pages 5-10 of paper.pdf"** → Extracts specific page range
- **"Search for 'parameter efficiency' in paper.pdf"** → Finds text and locations
- **"Open paper.pdf to page 5"** → Opens PDF viewer to specific page

## MCP Tools

### Reading Tools
- `read_pdf_text(file_path, start_page, end_page)` - Extract text from page range
- `read_pdf_page(file_path, page_number)` - Extract text from single page
- `get_pdf_structure(file_path)` - Get table of contents and page summaries
- `get_pdf_info(file_path)` - Get document metadata

### Navigation Tools
- `search_pdf_text(file_path, query)` - Search text and return locations
- `open_pdf_page(file_path, page_number)` - Open PDF viewer to specific page
- `search_and_open(file_path, query, result_index)` - Search and open to result

## Supported PDF Readers

- **Skim** (macOS) - `skim://` URL scheme
- **Zathura** (Linux) - `--page` argument
- **Evince** (Linux) - `--page-index` argument
- **SumatraPDF** (Windows) - `-page` argument
- **Adobe Acrobat** (Cross-platform) - `/A page=N` argument

## Configuration

Configure your PDF reader in `~/.pdf-navigator-config.json`:

```json
{
  "pdf_reader": "skim",
  "reader_path": "/Applications/Skim.app"
}
```

## Development

```bash
git clone https://github.com/matsengrp/pdf-navigator-mcp.git
cd pdf-navigator-mcp
pip install -e ".[dev]"
```

## License

MIT License