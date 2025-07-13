"""MCP server for PDF navigation."""

import sys
from typing import Optional, Union, List
from fastmcp import FastMCP
from .pdf_navigator import PDFNavigator
from .config import Config


def safe_int(value: Union[int, str], param_name: str = "parameter") -> int:
    """Safely convert a value to an integer with validation.
    
    Args:
        value: The value to convert (int or str)
        param_name: Name of the parameter for error messages
        
    Returns:
        The integer value
        
    Raises:
        ValueError: If the string cannot be converted to a valid integer
    """
    if isinstance(value, int):
        return value
    
    if isinstance(value, str):
        # Check if it's a valid integer string
        value = value.strip()
        if not value:
            raise ValueError(f"{param_name} cannot be empty")
        
        # Check for valid integer format (optional minus sign + digits)
        if not (value.isdigit() or (value.startswith('-') and value[1:].isdigit())):
            raise ValueError(f"{param_name} must be a valid integer, got: '{value}'")
        
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"{param_name} must be a valid integer, got: '{value}'")
    
    raise ValueError(f"{param_name} must be an integer or string, got: {type(value)}")


# Initialize MCP server
mcp = FastMCP("PDF Navigator")

# Initialize PDF navigator
config = Config()
navigator = PDFNavigator(config)


@mcp.tool()
def open_pdf_page(file_path: str, page_number: Union[int, str]) -> str:
    """Open a PDF file to a specific page.
    
    Args:
        file_path: Path to the PDF file
        page_number: Page number to open (1-indexed)
        
    Returns:
        Status message indicating success or error
    """
    # Convert string parameter to integer if needed
    page_number = safe_int(page_number, "page_number")
    
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
def read_pdf_text(file_path: str, start_page: Union[int, str] = 1, end_page: Optional[Union[int, str]] = None) -> str:
    """Read text content from PDF pages.
    
    Args:
        file_path: Path to the PDF file
        start_page: Starting page number (1-indexed, default: 1)
        end_page: Ending page number (1-indexed, inclusive). If None, reads to end.
        
    Returns:
        Extracted text content with page markers
    """
    # Convert string parameters to integers if needed
    start_page = safe_int(start_page, "start_page")
    if end_page is not None:
        end_page = safe_int(end_page, "end_page")
    
    return navigator.read_pdf_text(file_path, start_page, end_page)


@mcp.tool()
def read_pdf_page(file_path: str, page_number: Union[int, str]) -> str:
    """Read text content from a specific PDF page.
    
    Args:
        file_path: Path to the PDF file
        page_number: Page number to read (1-indexed)
        
    Returns:
        Text content of the specified page
    """
    # Convert string parameter to integer if needed
    page_number = safe_int(page_number, "page_number")
    
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
def search_and_open(file_path: str, query: str, result_index: Union[int, str] = 1) -> str:
    """Search for text in PDF and open to the specified result.
    
    Args:
        file_path: Path to the PDF file
        query: Text to search for
        result_index: Which search result to open (1-indexed, default: 1)
        
    Returns:
        Status message indicating success or error
    """
    # Convert string parameter to integer if needed
    result_index = safe_int(result_index, "result_index")
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


# Research Analysis Prompts
@mcp.prompt()
def analyze_paper_structure(file_path: str) -> str:
    """Guide analysis of a paper's structure and content"""
    return f"""Please analyze the structure and content of {file_path}:

1. First, get the PDF structure to understand sections
2. Read the abstract (usually page 1-2)
3. Identify the main contributions stated in the introduction
4. Find the methodology section and note the approach
5. Locate the results/evaluation section
6. Summarize the conclusions

Provide a structured summary with page references for each section."""


@mcp.prompt()
def find_definitions(file_path: str, terms: List[str]) -> str:
    """Find where key terms are defined in a paper"""
    terms_list = ', '.join(f'"{term}"' for term in terms)
    return f"""Search for definitions of these terms in {file_path}: {terms_list}

For each term:
1. Search for the first occurrence
2. Read the surrounding context (few sentences before/after)
3. Determine if this is where the term is defined
4. If not, search for phrases like "we define", "is defined as", "refers to"
5. Extract the definition and note the page number"""


# Literature Review Prompts
@mcp.prompt()
def extract_citations(file_path: str, topic: str) -> str:
    """Extract relevant citations on a specific topic"""
    return f"""Help me find citations related to '{topic}' in {file_path}:

1. Search for mentions of '{topic}' throughout the paper
2. For each mention, check if it's near a citation (look for [N] or (Author, Year) patterns)
3. Read the sentence containing the citation
4. Try to find the bibliography/references section
5. Match the citation numbers/names to full references

Return a list of relevant papers with:
- How they relate to '{topic}'
- Page where cited
- Full citation if found"""


@mcp.prompt()
def compare_approaches(file_paths: List[str], aspect: str) -> str:
    """Compare how multiple papers approach a specific aspect"""
    files_formatted = '\n'.join(f'  - {fp}' for fp in file_paths)
    return f"""Compare how these papers approach '{aspect}':
{files_formatted}

For each paper:
1. Search for '{aspect}' and related terms
2. Read the relevant sections
3. Extract:
   - Their specific approach/method
   - Advantages they claim
   - Limitations they acknowledge
   - Page references

Create a comparison table showing the differences."""


# Study/Learning Prompts
@mcp.prompt()
def create_study_notes(file_path: str, focus_areas: Optional[List[str]] = None) -> str:
    """Create comprehensive study notes from a paper"""
    areas = f"Focus especially on: {', '.join(focus_areas)}" if focus_areas else ""
    return f"""Create study notes for {file_path}. {areas}

Structure the notes as:
1. **Main Concept**: Read abstract and introduction, extract key idea
2. **Background**: What prior knowledge is assumed? (check section 2 usually)
3. **Core Contribution**: What's new? (usually in intro and conclusion)
4. **Technical Details**: Key algorithms, formulas, or methods
5. **Results**: Main findings and their significance
6. **Open Questions**: What future work do they suggest?

Include page numbers for each section."""


@mcp.prompt()
def explain_figure(file_path: str, figure_number: str) -> str:
    """Explain a specific figure in detail"""
    return f"""Explain Figure {figure_number} from {file_path}:

1. Search for "Figure {figure_number}" to find the figure caption
2. Read the caption and surrounding text
3. Find where this figure is referenced in the main text
4. Read those sections to understand context
5. Explain:
   - What the figure shows
   - Why it's important to the paper
   - Key takeaways
   - How to interpret it"""


# Writing Assistant Prompts
@mcp.prompt()
def find_examples(file_path: str, concept: str) -> str:
    """Find concrete examples of a concept"""
    return f"""Find concrete examples of '{concept}' in {file_path}:

1. Search for '{concept}' throughout the document
2. Look for phrases like "for example", "e.g.", "such as", "instance"
3. Search for "Figure" or "Table" references related to {concept}
4. Extract:
   - Each example found
   - Context around it
   - Page number
   - Whether it's a toy example or real-world application"""


@mcp.prompt()
def extract_evaluation_metrics(file_path: str) -> str:
    """Extract evaluation methodology and metrics"""
    return f"""Extract the evaluation methodology from {file_path}:

1. Find the evaluation/experiments/results section
2. Look for:
   - Datasets used
   - Metrics (accuracy, F1, BLEU, etc.)
   - Baselines compared against
   - Statistical significance tests
3. Search for tables with results
4. Note any ablation studies

Organize by: Metrics -> Values -> Conditions -> Page refs"""


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