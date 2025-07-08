"""Core PDF navigation functionality."""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import fitz  # PyMuPDF
from .config import Config


class PDFNavigator:
    """Core PDF navigation and search functionality."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize PDF navigator.
        
        Args:
            config: Configuration object. Creates default if None.
        """
        self.config = config or Config()
    
    def open_pdf_page(self, file_path: str, page_number: int) -> str:
        """Open PDF to specific page using configured reader.
        
        Args:
            file_path: Path to PDF file
            page_number: Page number (1-indexed)
            
        Returns:
            Status message
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            return f"Error: PDF file not found: {file_path}"
        
        if not pdf_path.suffix.lower() == '.pdf':
            return f"Error: File is not a PDF: {file_path}"
        
        # Validate page number
        try:
            doc = fitz.open(str(pdf_path))
            if page_number < 1 or page_number > len(doc):
                doc.close()
                return f"Error: Page {page_number} out of range (1-{len(doc)})"
            doc.close()
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
        
        # Open with configured reader
        reader = self.config.pdf_reader.lower()
        try:
            if reader == "skim":
                self._open_with_skim(pdf_path, page_number)
            elif reader == "zathura":
                self._open_with_zathura(pdf_path, page_number)
            elif reader == "evince":
                self._open_with_evince(pdf_path, page_number)
            elif reader == "sumatrapdf":
                self._open_with_sumatra(pdf_path, page_number)
            elif reader == "acrobat":
                self._open_with_acrobat(pdf_path, page_number)
            else:
                return f"Error: Unsupported PDF reader: {reader}"
            
            return f"Opened {pdf_path.name} to page {page_number}"
        except Exception as e:
            return f"Error opening PDF: {str(e)}"
    
    def search_pdf_text(self, file_path: str, query: str) -> str:
        """Search for text in PDF and return results with page numbers.
        
        Args:
            file_path: Path to PDF file
            query: Search query
            
        Returns:
            Search results with page numbers and context
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            return f"Error: PDF file not found: {file_path}"
        
        try:
            doc = fitz.open(str(pdf_path))
            results = []
            context_chars = self.config.search_context_chars
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Find all occurrences of query (case-insensitive)
                query_lower = query.lower()
                text_lower = text.lower()
                
                start = 0
                while True:
                    pos = text_lower.find(query_lower, start)
                    if pos == -1:
                        break
                    
                    # Extract context around match
                    context_start = max(0, pos - context_chars // 2)
                    context_end = min(len(text), pos + len(query) + context_chars // 2)
                    context = text[context_start:context_end].strip()
                    
                    # Clean up context (remove excessive whitespace)
                    context = ' '.join(context.split())
                    
                    results.append({
                        'page': page_num + 1,  # 1-indexed
                        'context': context,
                        'position': pos
                    })
                    
                    start = pos + 1
                    
                    # Limit results per page
                    if len([r for r in results if r['page'] == page_num + 1]) >= 3:
                        break
                
                # Stop if we have enough results
                if len(results) >= self.config.max_search_results:
                    break
            
            doc.close()
            
            if not results:
                return f"No results found for '{query}' in {pdf_path.name}"
            
            # Format results
            result_lines = [f"Found {len(results)} results for '{query}' in {pdf_path.name}:\\n"]
            for i, result in enumerate(results, 1):
                result_lines.append(f"{i}. Page {result['page']}: ...{result['context']}...")
            
            return "\\n".join(result_lines)
            
        except Exception as e:
            return f"Error searching PDF: {str(e)}"
    
    def read_pdf_text(self, file_path: str, start_page: int = 1, end_page: Optional[int] = None) -> str:
        """Read text content from PDF pages.
        
        Args:
            file_path: Path to PDF file
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed, inclusive). If None, reads to end.
            
        Returns:
            Extracted text content
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            return f"Error: PDF file not found: {file_path}"
        
        try:
            doc = fitz.open(str(pdf_path))
            total_pages = len(doc)
            
            # Validate page range
            if start_page < 1 or start_page > total_pages:
                doc.close()
                return f"Error: Start page {start_page} out of range (1-{total_pages})"
            
            if end_page is None:
                end_page = total_pages
            elif end_page < 1 or end_page > total_pages:
                doc.close()
                return f"Error: End page {end_page} out of range (1-{total_pages})"
            
            if start_page > end_page:
                doc.close()
                return f"Error: Start page {start_page} cannot be greater than end page {end_page}"
            
            # Extract text from specified pages
            text_parts = []
            for page_num in range(start_page - 1, end_page):  # Convert to 0-indexed
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():  # Only add non-empty pages
                    text_parts.append(f"--- Page {page_num + 1} ---\\n{page_text}")
            
            doc.close()
            
            if not text_parts:
                return f"No text found in pages {start_page}-{end_page} of {pdf_path.name}"
            
            return "\\n\\n".join(text_parts)
            
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def read_pdf_page(self, file_path: str, page_number: int) -> str:
        """Read text content from a specific PDF page.
        
        Args:
            file_path: Path to PDF file
            page_number: Page number to read (1-indexed)
            
        Returns:
            Text content of the specified page
        """
        return self.read_pdf_text(file_path, page_number, page_number)
    
    def get_pdf_structure(self, file_path: str) -> str:
        """Get PDF structure including table of contents and page summaries.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            PDF structure information
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            return f"Error: PDF file not found: {file_path}"
        
        try:
            doc = fitz.open(str(pdf_path))
            
            # Get table of contents
            toc = doc.get_toc()
            
            # Get page summaries (first few lines of each page)
            page_summaries = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Get first few lines as summary
                lines = text.split('\\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                summary = ' '.join(non_empty_lines[:3])  # First 3 non-empty lines
                
                if summary:
                    page_summaries.append(f"Page {page_num + 1}: {summary[:100]}...")
            
            doc.close()
            
            # Format output
            result = [f"PDF Structure: {pdf_path.name}"]
            result.append(f"Total Pages: {len(doc)}")
            
            if toc:
                result.append("\\nTable of Contents:")
                for level, title, page in toc:
                    indent = "  " * (level - 1)
                    result.append(f"{indent}• {title} (Page {page})")
            
            if page_summaries:
                result.append("\\nPage Summaries:")
                result.extend(page_summaries)
            
            return "\\n".join(result)
            
        except Exception as e:
            return f"Error reading PDF structure: {str(e)}"

    def get_pdf_info(self, file_path: str) -> str:
        """Get PDF metadata and basic information.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            PDF information
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            return f"Error: PDF file not found: {file_path}"
        
        try:
            doc = fitz.open(str(pdf_path))
            metadata = doc.metadata
            
            info = {
                'filename': pdf_path.name,
                'pages': len(doc),
                'title': metadata.get('title', 'Unknown'),
                'author': metadata.get('author', 'Unknown'),
                'subject': metadata.get('subject', 'Unknown'),
                'creator': metadata.get('creator', 'Unknown'),
                'producer': metadata.get('producer', 'Unknown'),
                'creation_date': metadata.get('creationDate', 'Unknown'),
                'modification_date': metadata.get('modDate', 'Unknown'),
            }
            
            doc.close()
            
            lines = [f"PDF Information: {info['filename']}"]
            lines.append(f"Pages: {info['pages']}")
            if info['title'] != 'Unknown':
                lines.append(f"Title: {info['title']}")
            if info['author'] != 'Unknown':
                lines.append(f"Author: {info['author']}")
            if info['subject'] != 'Unknown':
                lines.append(f"Subject: {info['subject']}")
            
            return "\\n".join(lines)
            
        except Exception as e:
            return f"Error reading PDF info: {str(e)}"
    
    def _open_with_skim(self, pdf_path: Path, page_number: int) -> None:
        """Open PDF with Skim (macOS)."""
        url = f"skim://{pdf_path.resolve()}#{page_number}"
        subprocess.run(["open", url], check=True)
    
    def _open_with_zathura(self, pdf_path: Path, page_number: int) -> None:
        """Open PDF with Zathura (Linux)."""
        cmd = ["zathura", "--page", str(page_number), str(pdf_path)]
        if self.config.reader_path:
            cmd[0] = self.config.reader_path
        subprocess.run(cmd, check=True)
    
    def _open_with_evince(self, pdf_path: Path, page_number: int) -> None:
        """Open PDF with Evince (Linux)."""
        cmd = ["evince", "--page-index", str(page_number - 1), str(pdf_path)]
        if self.config.reader_path:
            cmd[0] = self.config.reader_path
        subprocess.run(cmd, check=True)
    
    def _open_with_sumatra(self, pdf_path: Path, page_number: int) -> None:
        """Open PDF with SumatraPDF (Windows)."""
        cmd = ["SumatraPDF", "-page", str(page_number), str(pdf_path)]
        if self.config.reader_path:
            cmd[0] = self.config.reader_path
        subprocess.run(cmd, check=True)
    
    def _open_with_acrobat(self, pdf_path: Path, page_number: int) -> None:
        """Open PDF with Adobe Acrobat."""
        if platform.system() == "Darwin":
            # macOS
            cmd = ["open", "-a", "Adobe Acrobat Reader DC", str(pdf_path)]
        elif platform.system() == "Windows":
            # Windows
            cmd = ["AcroRd32.exe", f"/A page={page_number}", str(pdf_path)]
        else:
            # Linux
            cmd = ["acroread", f"/A page={page_number}", str(pdf_path)]
        
        if self.config.reader_path:
            if platform.system() == "Darwin":
                cmd[2] = self.config.reader_path
            else:
                cmd[0] = self.config.reader_path
        
        subprocess.run(cmd, check=True)