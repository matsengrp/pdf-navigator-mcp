# PDF Navigator MCP

A comprehensive Model Context Protocol (MCP) server for PDF reading, navigation, and text search with cross-platform PDF viewer integration. Built on **PyMuPDF (MuPDF)**, exposed through MCP so the dependency stays isolated from your project environment.

## Why this exists

Claude Code's built-in `Read` tool can open PDFs directly, so it's fair to ask whether this server is still needed. It is — but for a narrower reason than it used to be. The built-in reader has two limitations that this server is designed around, and a third tool (poppler's `pdftotext`) doesn't fill the gap either:

**The built-in `Read` tool renders each PDF page as a raster image.** Two consequences for scientific papers:

- *It's token-expensive and doesn't scale.* A figure-heavy 25-page paper is ~25 page-images; reading it whole burns tens of thousands of image tokens and crowds out the rest of the conversation. You *can* cap it with a `pages` range (and recent versions require one past ~10 pages), but only if you already know which pages you want.
- *Image text isn't searchable.* You can't search across pixels. To find where a paper discusses, say, "survivorship bias," you'd read pages as images until you spot it — the exact behavior that fills up context.

**Poppler's `pdftotext` is cheap and searchable but mangles the content scientific papers are made of:**

- *Inline math breaks.* Combining marks detach from their base — e.g. `p̃(x;t)` comes out as a stray `~` on its own line, split from `p(x;t)`.
- *Multi-column layout scrambles.* Default mode drags in running headers and can reorder text; `-layout` glues the two columns horizontally so every line reads `left-column … right-column`, destroying reading order and breaking any phrase search that spans a column.

**This server uses MuPDF's `get_text()`,** which preserves reading order across columns and keeps inline math intact, and exposes it as cheap, *searchable* text plus structure/outline navigation. The intended division of labor:

| Need | Tool |
|------|------|
| Read text, search to the relevant pages, navigate structure | **This server** (MuPDF text + search) — cheap, searchable, correct reading order |
| *See* a figure, panel, rendered equation, or table | **Built-in `Read` with a narrow `pages` range** — use it for the 1–3 pages that hold the visual, not the whole document |

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