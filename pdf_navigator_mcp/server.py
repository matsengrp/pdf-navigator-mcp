"""MCP server for PDF navigation."""

import sys
from typing import Optional
from fastmcp import FastMCP
from .pdf_navigator import PDFNavigator
from .config import Config


# Initialize MCP server
mcp = FastMCP("PDF Navigator")

# Initialize PDF navigator
config = Config()
navigator = PDFNavigator(config)


@mcp.tool()
def open_pdf_page(file_path: str, page_number: int) -> str:
    """Open a PDF file to a specific page.
    
    Args:
        file_path: Path to the PDF file
        page_number: Page number to open (1-indexed)
        
    Returns:
        Status message indicating success or error
    """
    return navigator.open_pdf_page(file_path, page_number)


@mcp.tool()
def search_pdf_text(file_path: str, query: str) -> str:
    """Search for text in a PDF file and return results with page numbers.
    
    Args:
        file_path: Path to the PDF file
        query: Text to search for
        
    Returns:
        Search results with page numbers and context
    """
    return navigator.search_pdf_text(file_path, query)


@mcp.tool()
def get_pdf_info(file_path: str) -> str:
    """Get metadata and basic information about a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        PDF information including title, author, page count, etc.
    """
    return navigator.get_pdf_info(file_path)


@mcp.tool()
def read_pdf_text(file_path: str, start_page: int = 1, end_page: Optional[int] = None) -> str:
    """Read text content from PDF pages.
    
    Args:
        file_path: Path to the PDF file
        start_page: Starting page number (1-indexed, default: 1)
        end_page: Ending page number (1-indexed, inclusive). If None, reads to end.
        
    Returns:
        Extracted text content with page markers
    """
    return navigator.read_pdf_text(file_path, start_page, end_page)


@mcp.tool()
def read_pdf_page(file_path: str, page_number: int) -> str:
    """Read text content from a specific PDF page.
    
    Args:
        file_path: Path to the PDF file
        page_number: Page number to read (1-indexed)
        
    Returns:
        Text content of the specified page
    """
    return navigator.read_pdf_page(file_path, page_number)


@mcp.tool()
def get_pdf_structure(file_path: str) -> str:
    """Get PDF structure including table of contents and page summaries.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        PDF structure with TOC and page summaries
    """
    return navigator.get_pdf_structure(file_path)


@mcp.tool()
def search_and_open(file_path: str, query: str, result_index: int = 1) -> str:
    """Search for text in PDF and open to the specified result.
    
    Args:
        file_path: Path to the PDF file
        query: Text to search for
        result_index: Which search result to open (1-indexed, default: 1)
        
    Returns:
        Status message indicating success or error
    """
    # First search for the text
    search_result = navigator.search_pdf_text(file_path, query)
    
    if "No results found" in search_result or "Error" in search_result:
        return search_result
    
    # Parse search results to find the page for the specified result
    lines = search_result.split('\\n')
    result_lines = [line for line in lines if line.strip().startswith(f"{result_index}.")]
    
    if not result_lines:
        return f"Result {result_index} not found. Check search results first."
    
    # Extract page number from result line
    result_line = result_lines[0]
    try:
        # Format: "1. Page 5: ...context..."
        page_part = result_line.split("Page ")[1].split(":")[0]
        page_number = int(page_part)
        
        # Open PDF to that page
        open_result = navigator.open_pdf_page(file_path, page_number)
        
        return f"Search result {result_index}: {open_result}"
    except (IndexError, ValueError):
        return f"Error parsing search result {result_index}"


def main():
    """Main entry point for the MCP server."""
    # Handle command line arguments
    if len(sys.argv) > 1:
        transport = sys.argv[1]
    else:
        transport = "stdio"
    
    if transport not in ["stdio", "sse", "http"]:
        print(f"Error: Unknown transport: {transport}", file=sys.stderr)
        sys.exit(1)
    
    # Run the server
    mcp.run(transport)


if __name__ == "__main__":
    main()