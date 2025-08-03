# PDF Navigator MCP

A comprehensive Model Context Protocol (MCP) server for PDF reading, navigation, and text search with cross-platform PDF viewer integration. Eliminates PyMuPDF dependency issues by providing PDF functionality through MCP.

## Features

- **PDF text extraction** - Read full PDFs or specific pages/ranges
- **PDF structure analysis** - Extract table of contents and page summaries
- **Text search with location** - Find text and jump to results
- **Direct PDF navigation** - Open PDFs to specific pages
- **PDF form filling** - Extract form fields to markdown, edit, and fill PDFs
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
- **"Extract form fields from application.pdf"** → Creates markdown file with form fields
- **"Fill the PDF form with my data"** → Fills PDF using edited markdown data

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

### Form Filling Tools
- `extract_form_to_markdown(file_path, output_md_path)` - Extract form fields to markdown with multi-line detection
- `fill_form_from_markdown(pdf_path, markdown_path, output_pdf_path, distribute_text=True, max_chars_per_field=50, respect_line_breaks=True)` - Fill PDF from markdown with intelligent text distribution

## PDF Form Filling Workflow

The PDF form filling feature uses a markdown-based workflow:

1. **Extract form fields** - Analyze the PDF and create a markdown file with all detected fields
2. **Edit the markdown** - Fill in values using any text editor
3. **Fill the PDF** - Apply the markdown data back to create a filled PDF

### Example Workflow

```bash
# Step 1: Extract form fields to markdown
# Creates a markdown file with placeholders for each field
extract_form_to_markdown("application.pdf", "application_form.md")

# Step 2: Edit application_form.md in your editor
# Fill in values after each arrow (→)

# Step 3: Fill the PDF with your data
fill_form_from_markdown("application.pdf", "application_form.md", "application_filled.pdf")
```

### Markdown Format

The extracted markdown looks like:

```markdown
# PDF Form: application.pdf
Type: Interactive Form
Generated: 2025-08-03

## Form Fields

### Page 1
- Full Name → John Smith
- Email → john@example.com
- Phone → 555-0123
- [ ] Subscribe to newsletter → true
```

### Form Types Supported

- **Interactive Forms** - PDFs with actual form fields (fillable PDFs)
- **Static Forms** - PDFs with underlines/boxes (creates moveable text annotations)

### Enhanced Multi-line Form Detection

The PDF Navigator now includes advanced multi-line form detection and intelligent text distribution:

#### Features
- **Multi-line Section Detection** - Automatically detects when multiple consecutive blank lines follow a section header (e.g., "I love..." followed by several underscores)
- **Smart Text Distribution** - Distributes long text across multiple related fields using natural break points
- **Natural Break Points** - Respects sentences, commas, conjunctions, and explicit line breaks
- **Configurable Parameters** - Control text distribution behavior

#### Text Distribution Strategies
1. **Sentence splitting** - "I love reading. Playing games is fun." → separate fields
2. **Comma/semicolon splitting** - "Reading books, playing games, going to parks" → separate fields  
3. **Conjunction splitting** - "Reading and playing and going" → separate fields
4. **Word boundary splitting** - Intelligent length-based splitting while preserving whole words

#### Configuration Options
- `distribute_text: bool` - Enable/disable multi-line text distribution (default: True)
- `max_chars_per_field: int` - Target character limit per field (default: 50)
- `respect_line_breaks: bool` - Honor newlines in input text (default: True)

#### Example
Instead of cramming "Reading books with my parents, doing puzzles and addition, going on trips, anything with my big sister" into one tiny field, it automatically distributes as:
- Field 1: "Reading books with my parents"
- Field 2: "doing puzzles and addition" 
- Field 3: "going on trips"
- Field 4: "anything with my big sister"

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