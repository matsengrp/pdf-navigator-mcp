"""Core PDF navigation functionality."""

import os
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote
from datetime import datetime
import re
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
        abs_path = pdf_path.resolve()
        skim_url = f"skim://{abs_path}#page={page_number}"
        
        subprocess.run(["open", skim_url], check=True)
    
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
    
    def extract_form_to_markdown(self, file_path: str, output_md_path: str) -> str:
        """Extract form fields from PDF to a markdown file for editing.
        
        Args:
            file_path: Path to PDF file
            output_md_path: Path where markdown file will be created
            
        Returns:
            Status message
        """
        pdf_path = Path(file_path)
        if not pdf_path.exists():
            return f"Error: PDF file not found: {file_path}"
        
        try:
            doc = fitz.open(str(pdf_path))
            md_path = Path(output_md_path)
            
            # Analyze form type and extract fields
            form_fields = []
            form_type = "static"  # Default to static
            
            # Check for interactive form fields
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = list(page.widgets())
                
                if widgets:
                    form_type = "interactive"
                    # Get page text for context analysis
                    page_text = page.get_text()
                    
                    # Enhance interactive widgets with context
                    enhanced_widgets = self._enhance_interactive_widgets_with_context(
                        widgets, page_text, page_num + 1
                    )
                    form_fields.extend(enhanced_widgets)
            
            # If no interactive fields, try to detect static form patterns
            if form_type == "static":
                form_fields = self._detect_static_form_fields(doc)
            
            # Generate markdown content with field mapping
            md_content = self._generate_form_markdown(pdf_path.name, form_type, len(doc), form_fields)
            
            # Write to file
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_content)
            
            doc.close()
            
            return f"Extracted {len(form_fields)} form fields from {pdf_path.name} to {md_path.name}"
            
        except Exception as e:
            return f"Error extracting form: {str(e)}"
    
    def _detect_static_form_fields(self, doc) -> List[Dict]:
        """Detect form fields in static PDFs with context-aware structure preservation."""
        fields = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            # Enhanced context-aware detection
            sections = self._detect_form_sections_with_context(lines, page_num + 1)
            
            # Convert sections to fields list
            for section in sections:
                fields.extend(section['fields'])
        
        return fields
    
    def _enhance_interactive_widgets_with_context(self, widgets: List, page_text: str, page_num: int) -> List[Dict]:
        """Enhance interactive form widgets with sophisticated contextual mapping."""
        lines = page_text.split('\n')
        
        # Create precise widget-to-context mapping using position and content analysis
        enhanced_fields = []
        
        # Build comprehensive context map from text structure
        context_map = self._build_comprehensive_context_map(lines, page_text)
        
        # Process each widget with sophisticated matching
        for widget in widgets:
            widget_name = widget.field_name or f"field_{len(enhanced_fields) + 1}"
            
            # Find best context match using multiple strategies
            context_info = self._find_best_widget_context(widget, widget_name, context_map, lines)
            
            field_info = {
                'page': page_num,
                'name': context_info['enhanced_name'],
                'prompt': context_info.get('prompt', 'Unknown'),
                'section': context_info.get('section', 'General'),
                'type': widget.field_type_string,
                'value': widget.field_value or '',
                'flags': widget.field_flags,
                'rect': widget.rect,
                'original_name': widget_name,
                'context_confidence': context_info.get('confidence', 0)
            }
            
            enhanced_fields.append(field_info)
        
        return enhanced_fields
    
    def _build_comprehensive_context_map(self, lines: List[str], full_text: str) -> Dict:
        """Build a comprehensive map of all form contexts and sections."""
        context_map = {
            'sections': {},
            'prompts': {},
            'field_areas': []
        }
        
        # Define the known structure from the specific form
        known_sections = [
            {
                'prompts': ['I love'],
                'section': 'Personal Interests',
                'field_count': 4,
                'text_pattern': r'I love.*?_{20,}'
            },
            {
                'prompts': ['I also really like'],
                'section': 'Additional Interests', 
                'field_count': 4,
                'text_pattern': r'I also really like.*?_{20,}'
            },
            {
                'prompts': ['Did you know I can'],
                'section': 'Abilities',
                'field_count': 5,
                'text_pattern': r'Did you know I can.*?_{20,}'
            },
            {
                'prompts': ['My favorite activities are'],
                'section': 'Favorite Activities',
                'field_count': 6,
                'text_pattern': r'My favorite activities are.*?_{20,}'
            },
            {
                'prompts': ["I'm a fan of", "Im a fan of"],
                'section': 'Fandoms',
                'field_count': 4,
                'text_pattern': r'I.?m a fan of.*?_{20,}'
            },
            {
                'prompts': ['I am'],
                'section': 'My Strengths',
                'field_count': 4,
                'text_pattern': r'My Strengths:.*?I am'
            },
            {
                'prompts': ['What I am working on'],
                'section': 'Working On',
                'field_count': 1,
                'text_pattern': r'What I am working on:'
            },
            {
                'prompts': ['I might need help with'],
                'section': 'Need Help',
                'field_count': 1,
                'text_pattern': r'I might need help with:'
            },
            {
                'prompts': ['Something you should know about me is'],
                'section': 'About Me',
                'field_count': 1,
                'text_pattern': r'Something you should know.*?about me is'
            },
            {
                'prompts': ['I use other strategies, like'],
                'section': 'Helpful Strategies',
                'field_count': 1,
                'text_pattern': r'I use other strategies.*?like'
            },
            {
                'prompts': ["HI! I'M", "HI IM"],
                'section': 'Introduction',
                'field_count': 1,
                'text_pattern': r'HI!?\s*I.?M'
            }
        ]
        
        # Map each section's prompts to section info
        for section_info in known_sections:
            for prompt in section_info['prompts']:
                context_map['prompts'][prompt.lower()] = {
                    'section': section_info['section'],
                    'field_count': section_info['field_count'],
                    'main_prompt': section_info['prompts'][0]
                }
                
        context_map['sections'] = {info['section']: info for info in known_sections}
        
        return context_map
    
    def _find_best_widget_context(self, widget, widget_name: str, context_map: Dict, lines: List[str]) -> Dict:
        """Find the best context match for a widget using multiple strategies."""
        widget_lower = widget_name.lower()
        
        # Strategy 1: Direct name matching with known prompts
        for prompt, section_info in context_map['prompts'].items():
            # Check if widget name matches the prompt pattern
            prompt_words = prompt.split()[:2]  # First 2 words for matching
            if len(prompt_words) >= 2:
                if all(word in widget_lower for word in prompt_words):
                    return {
                        'enhanced_name': self._generate_enhanced_widget_name(
                            section_info['section'], 
                            section_info['main_prompt'], 
                            widget_name
                        ),
                        'prompt': section_info['main_prompt'],
                        'section': section_info['section'],
                        'confidence': 0.9
                    }
        
        # Strategy 2: Pattern-based matching for Text fields
        if widget_name.startswith('Text'):
            # Text1-Text4 likely map to "I am..." in My Strengths
            text_num = re.search(r'(\d+)', widget_name)
            if text_num:
                num = int(text_num.group(1))
                if 1 <= num <= 4:
                    return {
                        'enhanced_name': f"my_strengths_strength_{num} (I am...)",
                        'prompt': 'I am',
                        'section': 'My Strengths',
                        'confidence': 0.8
                    }
                elif 5 <= num <= 6:
                    return {
                        'enhanced_name': f"working_on_field_{num-4} (What I am working on...)",
                        'prompt': 'What I am working on',
                        'section': 'Working On', 
                        'confidence': 0.7
                    }
                else:
                    return {
                        'enhanced_name': f"additional_field_{num} (Additional info...)",
                        'prompt': 'Additional info',
                        'section': 'Additional Information',
                        'confidence': 0.6
                    }
        
        # Strategy 3: Fuzzy matching for known field patterns  
        pattern_mappings = {
            'hi': ('HI! I\'M', 'Introduction'),
            'love': ('I love', 'Personal Interests'),
            'like': ('I also really like', 'Additional Interests'),
            'can': ('Did you know I can', 'Abilities'),
            'activities': ('My favorite activities are', 'Favorite Activities'),
            'fan': ('I\'m a fan of', 'Fandoms'),
            'know': ('Something you should know about me is', 'About Me'),
            'strategies': ('I use other strategies, like', 'Helpful Strategies'),
        }
        
        for pattern, (prompt, section) in pattern_mappings.items():
            if pattern in widget_lower:
                return {
                    'enhanced_name': self._generate_enhanced_widget_name(section, prompt, widget_name),
                    'prompt': prompt,
                    'section': section,
                    'confidence': 0.7
                }
        
        # Strategy 4: Fallback with generic naming
        return {
            'enhanced_name': f"general_field ({widget_name})",
            'prompt': 'General field',
            'section': 'General',
            'confidence': 0.3
        }
    
    def _find_widget_context(self, widget_name: str, prompt_to_section: Dict, lines: List[str]) -> Optional[Dict]:
        """Find contextual information for a widget based on its name and surrounding text."""
        widget_lower = widget_name.lower()
        
        # Direct prompt matching
        for prompt, section_info in prompt_to_section.items():
            # Check if widget name contains prompt keywords
            prompt_words = prompt.split()
            if len(prompt_words) > 1 and all(word in widget_lower for word in prompt_words[:2]):
                return {
                    'enhanced_name': self._generate_enhanced_widget_name(
                        section_info['section'], 
                        prompt, 
                        widget_name
                    ),
                    'prompt': prompt,
                    'section': section_info['section']
                }
        
        # Fuzzy matching based on common patterns
        pattern_mappings = {
            'hi': ('HI! I\'M', 'General'),
            'love': ('I love', 'General'),
            'like': ('I like', 'General'), 
            'really like': ('I also really like', 'General'),
            'can': ('Did you know I can', 'General'),
            'activities': ('My favorite activities are', 'General'),
            'fan': ('I\'m a fan of', 'General'),
            'know': ('Something you should know about me is', 'General'),
            'strategies': ('I use other strategies, like', 'Helpful Strategies'),
            'text': ('Unknown', 'My Strengths')  # Many Text fields are likely strengths
        }
        
        for pattern, (prompt, section) in pattern_mappings.items():
            if pattern in widget_lower:
                return {
                    'enhanced_name': self._generate_enhanced_widget_name(section, prompt, widget_name),
                    'prompt': prompt,
                    'section': section
                }
        
        return None
    
    def _generate_enhanced_widget_name(self, section: str, prompt: str, original_name: str) -> str:
        """Generate enhanced widget name with context."""
        section_normalized = re.sub(r'\s+', '_', section.lower())
        
        # Extract number from original name if present
        number_match = re.search(r'(\d+)', original_name)
        number_suffix = f"_{number_match.group(1)}" if number_match else ""
        
        prompt_map = {
            'I am': 'strength',
            'I love': 'love',
            'I like': 'like', 
            'I also really like': 'also_like',
            'Did you know I can': 'can_do',
            'My favorite activities are': 'favorite_activity',
            "I'm a fan of": 'fan_of',
            'I might need help with': 'need_help',
            'I use other strategies, like': 'other_strategy',
            'Something you should know about me is': 'about_me',
            "HI! I'M": 'name',
            'Unknown': 'field'
        }
        
        prompt_key = prompt_map.get(prompt, 'field')
        
        return f"{section_normalized}_{prompt_key}{number_suffix} ({prompt}...)"
    
    def _detect_form_sections_with_context(self, lines: List[str], page_num: int) -> List[Dict]:
        """Detect form sections with full context preservation."""
        sections = []
        current_section = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check if this is a section header
            section_info = self._identify_section_header(line, lines, i)
            if section_info:
                # Save previous section if exists
                if current_section and current_section.get('fields'):
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'title': section_info['title'],
                    'normalized_title': section_info['normalized_title'],
                    'page': page_num,
                    'start_line': i,
                    'fields': []
                }
                i += 1
                continue
            
            # Check if this is a field prompt (like "I am...", "I love...")
            field_prompt = self._identify_field_prompt(line, lines, i)
            if field_prompt:
                # Look for blank lines after this prompt
                blanks_info = self._analyze_blanks_after_prompt(lines, i + 1)
                
                if blanks_info['count'] > 0:
                    # Create fields for this prompt
                    for field_idx in range(blanks_info['count']):
                        field_name = self._generate_contextual_field_name(
                            current_section, field_prompt, field_idx + 1, blanks_info['count']
                        )
                        
                        field_info = {
                            'page': page_num,
                            'name': field_name,
                            'prompt': field_prompt,
                            'section': current_section['title'] if current_section else None,
                            'type': 'text',
                            'value': '',
                            'field_index': field_idx + 1,
                            'total_fields': blanks_info['count'],
                            'is_multiline_part': blanks_info['count'] > 1
                        }
                        
                        if current_section:
                            current_section['fields'].append(field_info)
                        else:
                            # Create ad-hoc section for orphaned fields
                            if not sections or sections[-1]['title'] != 'General':
                                sections.append({
                                    'title': 'General',
                                    'normalized_title': 'general',
                                    'page': page_num,
                                    'fields': []
                                })
                            sections[-1]['fields'].append(field_info)
                    
                    # Skip the processed blank lines
                    i += blanks_info['lines_to_skip']
                else:
                    i += 1
            else:
                i += 1
        
        # Add final section if exists
        if current_section and current_section.get('fields'):
            sections.append(current_section)
        
        return sections
    
    def _identify_section_header(self, line: str, lines: List[str], line_idx: int) -> Optional[Dict]:
        """Identify if a line is a section header."""
        # Section header patterns
        header_patterns = [
            r'^(My\s+Strengths?):?\s*$',
            r'^(What\s+I\s+am\s+working\s+on):?\s*$',
            r'^(Helpful\s+Strategies?):?\s*$',
            r'^(About\s+Me):?\s*$',
            r'^(My\s+Interests?):?\s*$',
            r'^(Favorites?):?\s*$',
            r'^(Challenges?):?\s*$',
            r'^(Goals?):?\s*$',
        ]
        
        for pattern in header_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                title = match.group(1)
                normalized = re.sub(r'\s+', '_', title.lower().strip(':'))
                return {
                    'title': title,
                    'normalized_title': normalized
                }
        
        # Check if line ends with colon and next lines contain prompts/blanks
        if line.endswith(':') and len(line) > 5:
            # Look ahead to see if this looks like a section
            next_lines = lines[line_idx + 1:line_idx + 5]
            has_prompts_or_blanks = any(
                re.search(r'(I\s+am|I\s+love|I\s+like|I\s+can|I\s+might|_{5,})', nl, re.IGNORECASE)
                for nl in next_lines if nl.strip()
            )
            
            if has_prompts_or_blanks:
                title = line.rstrip(':').strip()
                normalized = re.sub(r'\s+', '_', title.lower())
                return {
                    'title': title,
                    'normalized_title': normalized
                }
        
        return None
    
    def _identify_field_prompt(self, line: str, lines: List[str], line_idx: int) -> Optional[str]:
        """Identify if a line is a field prompt."""
        # Common field prompt patterns
        prompt_patterns = [
            r'^(I\s+am)\.{0,3}\s*$',
            r'^(I\s+love)\.{0,3}\s*$',
            r'^(I\s+like)\.{0,3}\s*$',
            r'^(I\s+also\s+really\s+like)\.{0,3}\s*$',
            r'^(Did\s+you\s+know\s+I\s+can)\.{0,3}\s*$',
            r'^(My\s+favorite\s+activities\s+are)\.{0,3}\s*$',
            r'^(I\'?m\s+a\s+fan\s+of)\.{0,3}\s*$',
            r'^(I\s+might\s+need\s+help\s+with)\.{0,3}\s*$',
            r'^(I\s+use\s+other\s+strategies\s*,?\s*like)\.{0,3}\s*$',
            r'^(Something\s+you\s+should\s+know\s+about\s+me\s+is)\.{0,3}\s*$',
            r'^(HI!?\s+I\'?M)\.{0,3}\s*$',
            r'^(When\s+I\s+am\s+upset).*$',
            r'^(These\s+things\s+can\s+be\s+helpful).*$',
        ]
        
        for pattern in prompt_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _analyze_blanks_after_prompt(self, lines: List[str], start_idx: int) -> Dict:
        """Analyze blank lines following a prompt."""
        count = 0
        lines_to_skip = 0
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            
            # Check if it's a blank line pattern
            if re.match(r'^_{5,}$', line):  # Underscores
                count += 1
                lines_to_skip += 1
            elif re.match(r'^-{5,}$', line):  # Dashes
                count += 1
                lines_to_skip += 1
            elif re.match(r'^\s*$', line):  # Empty line
                lines_to_skip += 1
                # Don't count pure empty lines as fields, just skip them
            else:
                # Hit non-blank content, stop
                break
        
        return {
            'count': count,
            'lines_to_skip': lines_to_skip
        }
    
    def _generate_contextual_field_name(self, section: Optional[Dict], prompt: str, 
                                      field_idx: int, total_fields: int) -> str:
        """Generate meaningful field names with context."""
        # Create base name from section and prompt
        if section:
            section_prefix = section['normalized_title']
        else:
            section_prefix = 'general'
        
        # Create prompt-based suffix
        prompt_map = {
            'I am': 'strength',
            'I love': 'love',
            'I like': 'like', 
            'I also really like': 'also_like',
            'Did you know I can': 'can_do',
            'My favorite activities are': 'favorite_activity',
            "I'm a fan of": 'fan_of',
            'I might need help with': 'need_help',
            'I use other strategies, like': 'other_strategy',
            'Something you should know about me is': 'about_me',
            "HI! I'M": 'name',
            'When I am upset': 'when_upset',
            'These things can be helpful': 'helpful_thing'
        }
        
        prompt_key = prompt_map.get(prompt, 'field')
        
        if total_fields > 1:
            return f"{section_prefix}_{prompt_key}_{field_idx} ({prompt}...)"
        else:
            return f"{section_prefix}_{prompt_key} ({prompt}...)"
    
    def _detect_multiline_sections(self, lines: List[str], page_num: int) -> List[Dict]:
        """Detect multi-line form sections with consecutive blank lines."""
        sections = []
        current_section = None
        consecutive_blanks = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check if this line looks like a section header
            if self._is_section_header(line, lines, i):
                # If we have consecutive blanks after this, it's a multi-line section
                consecutive_blanks = self._count_consecutive_blanks(lines, i + 1)
                
                if consecutive_blanks >= 2:  # At least 2 blank lines = multi-line section
                    # Limit to maximum 5 fields per section for reasonable forms
                    actual_field_count = min(consecutive_blanks, 5)
                    
                    current_section = {
                        'page': page_num,
                        'section_header': line,
                        'field_count': actual_field_count,
                        'type': 'multiline_section',
                        'start_line': i + 1,
                        'fields': []
                    }
                    
                    # Create individual fields for this section
                    for field_idx in range(actual_field_count):
                        field_name = f"{line} (part {field_idx + 1})"
                        current_section['fields'].append({
                            'page': page_num,
                            'name': field_name,
                            'type': 'text',
                            'value': '',
                            'section_id': len(sections),
                            'field_index': field_idx,
                            'is_multiline_part': True
                        })
                    
                    sections.append(current_section)
        
        # Flatten the fields from all sections
        all_fields = []
        for section in sections:
            all_fields.extend(section['fields'])
        
        return all_fields
    
    def _is_section_header(self, line: str, lines: List[str], line_idx: int) -> bool:
        """Check if a line looks like a section header."""
        if not line or len(line) < 5:
            return False
        
        # Look for common section header patterns
        header_patterns = [
            r'^(I\s+)?(love|like|enjoy|prefer)',  # "I love...", "I like..."
            r'^(My\s+)?(favorite|best|worst)',    # "My favorite...", "Best..."
            r'^(Tell us|Describe|Explain|Write about)',  # Question starters
            r'^(What|How|Why|When|Where)',        # Question words
            r'[.!?:]$',  # Ends with punctuation (likely a question/statement)
        ]
        
        for pattern in header_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        
        return False
    
    def _count_consecutive_blanks(self, lines: List[str], start_idx: int) -> int:
        """Count consecutive blank lines (underscores, dashes, or actual blanks)."""
        count = 0
        blank_patterns = [
            r'^_{5,}$',      # Underscores
            r'^-{5,}$',      # Dashes
            r'^\s*$',        # Empty lines
            r'^\.{5,}$',     # Dots
        ]
        
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            is_blank_line = False
            
            for pattern in blank_patterns:
                if re.match(pattern, line):
                    is_blank_line = True
                    break
            
            if is_blank_line:
                count += 1
            else:
                # Stop counting if we hit non-blank content
                if line and not re.match(r'^[_\-.\s]*$', line):
                    break
        
        return count
    
    def _detect_individual_fields(self, text: str, page_num: int, existing_fields: List[Dict]) -> List[Dict]:
        """Detect individual form fields that aren't part of multi-line sections."""
        fields = []
        
        # Get list of existing field names to avoid duplicates
        existing_names = set()
        for field in existing_fields:
            name = field['name'].lower()
            # Extract base name for multiline fields
            if ' (part ' in name:
                base_name = name.split(' (part ')[0]
                existing_names.add(base_name)
            existing_names.add(name)
        
        # Common individual field patterns
        patterns = [
            r'Name:?\s*_{10,}',
            r'Email:?\s*_{10,}',
            r'Phone:?\s*_{10,}',
            r'Address:?\s*_{10,}',
            r'Date:?\s*_{10,}',
            r'Signature:?\s*_{10,}',
            r'(\w+):?\s*_{10,}',  # Generic pattern
            r'(\w+\s*\w*):?\s*\[?\s*\]',  # Checkbox pattern
            r'(\w+\s*\w*):?\s*\(\s*\)',  # Radio button pattern
        ]
        
        # Split text into lines to avoid matching across multi-line sections
        lines = text.split('\n')
        processed_text = ""
        skip_next_lines = 0
        
        for i, line in enumerate(lines):
            if skip_next_lines > 0:
                skip_next_lines -= 1
                continue
                
            # If this line has consecutive blanks after it, skip those lines to avoid duplicate detection
            consecutive_blanks = self._count_consecutive_blanks(lines, i + 1)
            if consecutive_blanks >= 2:
                skip_next_lines = consecutive_blanks
            
            processed_text += line + "\n"
        
        for pattern in patterns:
            matches = re.finditer(pattern, processed_text, re.IGNORECASE)
            for match in matches:
                field_name = match.group(1) if match.groups() else match.group(0).split(':')[0].strip()
                
                # Skip if this is just underscores without a clear label
                if re.match(r'^_+$', field_name.strip()):
                    continue
                
                # Skip if we already have this field
                if field_name.lower() in existing_names:
                    continue
                
                # Skip if this field name is part of an existing multiline section
                if any(field_name.lower() in existing_name for existing_name in existing_names):
                    continue
                
                fields.append({
                    'page': page_num,
                    'name': field_name,
                    'type': 'text',
                    'value': '',
                    'pattern': match.group(0),
                    'is_multiline_part': False
                })
                
                # Add to existing names to prevent duplicates within this detection
                existing_names.add(field_name.lower())
        
        return fields
    
    def _generate_form_markdown(self, pdf_name: str, form_type: str, page_count: int, fields: List[Dict]) -> str:
        """Generate enhanced markdown content with section structure preserved."""
        lines = [
            f"# PDF Form: {pdf_name}",
            f"Type: {form_type.title()} Form",
            f"Pages: {page_count}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Instructions",
            "Fill in the values after each arrow (→). Leave blank if not applicable.",
            "For checkboxes, use 'true' or 'false' after the arrow.",
            "Field names show both section context and prompt for easy verification.",
            "",
            "## Field Mapping",
            "<!-- This section maps semantic field names to PDF internal field names -->",
            "<!-- Format: semantic_name|pdf_field_name -->",
        ]
        
        # Add field mapping metadata
        for field in fields:
            semantic_name = field['name']  # This is our enhanced semantic name
            pdf_field_name = field.get('original_name', field.get('field_name', semantic_name))
            lines.append(f"<!-- {semantic_name}|{pdf_field_name} -->")
        
        lines.extend([
            "",
            "## Form Fields",
            ""
        ])
        
        # Group fields by section and page
        sections_by_page = {}
        
        for field in fields:
            page = field.get('page', 1)
            section = field.get('section', 'General')
            
            if page not in sections_by_page:
                sections_by_page[page] = {}
            if section not in sections_by_page[page]:
                sections_by_page[page][section] = []
            
            sections_by_page[page][section].append(field)
        
        # Generate markdown for each page with section grouping
        for page in sorted(sections_by_page.keys()):
            lines.append(f"### Page {page}")
            lines.append("")
            
            for section_name, section_fields in sections_by_page[page].items():
                # Add section header
                lines.append(f"#### {section_name}")
                lines.append("")
                
                # Group fields by prompt within section
                prompts = {}
                for field in section_fields:
                    prompt = field.get('prompt', 'Unknown')
                    if prompt not in prompts:
                        prompts[prompt] = []
                    prompts[prompt].append(field)
                
                # Generate fields grouped by prompt
                for prompt, prompt_fields in prompts.items():
                    if len(prompt_fields) > 1:
                        lines.append(f"**{prompt}** (multiple fields):")
                    
                    for field in prompt_fields:
                        field_type = field.get('type', 'text').lower()
                        field_name = field['name']
                        
                        if 'checkbox' in field_type or 'button' in field_type:
                            lines.append(f"- [ ] {field_name} → false")
                        else:
                            lines.append(f"- {field_name} → ")
                
                lines.append("")
        
        return "\n".join(lines)
    
    def fill_form_from_markdown(self, pdf_path: str, markdown_path: str, output_pdf_path: str,
                              distribute_text: bool = True, max_chars_per_field: int = 50, 
                              respect_line_breaks: bool = True) -> str:
        """Fill PDF form using data from markdown file.
        
        Args:
            pdf_path: Path to source PDF file
            markdown_path: Path to markdown file with form data
            output_pdf_path: Path where filled PDF will be saved
            distribute_text: Enable/disable multi-line text distribution
            max_chars_per_field: Target character limit per field
            respect_line_breaks: Honor newlines in input text
            
        Returns:
            Status message
        """
        pdf_input = Path(pdf_path)
        md_path = Path(markdown_path)
        pdf_output = Path(output_pdf_path)
        
        if not pdf_input.exists():
            return f"Error: PDF file not found: {pdf_path}"
        
        if not md_path.exists():
            return f"Error: Markdown file not found: {markdown_path}"
        
        try:
            # Parse markdown to extract form data with text distribution and field mapping
            form_data, field_mapping = self._parse_form_markdown(md_path, distribute_text, 
                                                max_chars_per_field, respect_line_breaks)
            
            # Ensure field mapping is available (should always be present in new format)
            if not field_mapping:
                return f"Error: No field mapping found in {markdown_path}. Please re-extract the form using extract_form_to_markdown to generate field mapping metadata."
            
            # Open PDF
            doc = fitz.open(str(pdf_input))
            
            # Check if it's an interactive form
            has_widgets = any(list(doc[i].widgets()) for i in range(len(doc)))
            
            if has_widgets:
                # Fill interactive form using field mapping
                filled_count = self._fill_interactive_form(doc, form_data, field_mapping)
            else:
                # Create annotations for static form using field mapping
                filled_count = self._fill_static_form(doc, form_data, field_mapping)
            
            # Save the filled PDF
            pdf_output.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(pdf_output))
            doc.close()
            
            return f"Successfully filled {filled_count} fields and saved to {pdf_output.name}"
            
        except Exception as e:
            return f"Error filling form: {str(e)}"
    
    def _parse_form_markdown(self, md_path: Path, distribute_text: bool = True, 
                           max_chars_per_field: int = 50, respect_line_breaks: bool = True) -> tuple[Dict[str, str], Dict[str, str]]:
        """Parse markdown file to extract form field values with text distribution.
        
        Returns:
            tuple: (form_data, field_mapping) where field_mapping maps semantic names to PDF field names
        """
        content = md_path.read_text()
        raw_form_data = {}
        field_mapping = {}
        
        # Extract field mapping from comments
        mapping_pattern = r'<!--\s*(.+?)\|(.+?)\s*-->'
        for line in content.split('\n'):
            mapping_match = re.match(mapping_pattern, line.strip())
            if mapping_match:
                semantic_name = mapping_match.group(1).strip()
                pdf_field_name = mapping_match.group(2).strip()
                field_mapping[semantic_name] = pdf_field_name
        
        # Pattern to match field lines: "- Field Name → value" or "- [ ] Field Name → true/false"
        field_pattern = r'^-\s*(?:\[\s*\]\s*)?(.+?)\s*→\s*(.*)$'
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(field_pattern, line.strip())
            if match:
                field_name = match.group(1).strip()
                field_value = match.group(2).strip()
                
                # Check if the field value continues on subsequent lines (for multiline values)
                if field_value and not field_value.endswith('.') and i + 1 < len(lines):
                    # Look ahead for continuation lines that don't start with '-'
                    continuation_lines = []
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if (next_line and 
                            not next_line.startswith('-') and 
                            not next_line.startswith('#') and
                            not re.match(field_pattern, next_line)):
                            continuation_lines.append(next_line)
                            j += 1
                        else:
                            break
                    
                    if continuation_lines:
                        field_value = field_value + '\n' + '\n'.join(continuation_lines)
                        i = j - 1  # Skip the processed continuation lines
                
                # Convert boolean strings
                if field_value.lower() in ['true', 'yes', 'checked']:
                    field_value = True
                elif field_value.lower() in ['false', 'no', 'unchecked']:
                    field_value = False
                elif field_value == '':
                    field_value = ""  # Keep empty strings as strings, not False
                
                raw_form_data[field_name] = field_value
            
            i += 1
        
        # Apply text distribution if enabled
        if distribute_text:
            distributed_data = self._distribute_text_across_fields(raw_form_data, max_chars_per_field, respect_line_breaks)
            return distributed_data, field_mapping
        else:
            return raw_form_data, field_mapping
    
    def _distribute_text_across_fields(self, form_data: Dict[str, str], 
                                     max_chars_per_field: int, respect_line_breaks: bool) -> Dict[str, str]:
        """Distribute long text across multiple related fields."""
        distributed_data = {}
        
        # Group fields by their base section
        field_groups = self._group_multiline_fields(form_data)
        
        for base_name, fields in field_groups.items():
            if len(fields) == 1:
                # Single field, no distribution needed
                field_name, field_value = fields[0]
                distributed_data[field_name] = field_value
            else:
                # Multi-line section, distribute text
                # Find the field with content (usually the first one will have all text)
                source_text = ""
                for field_name, field_value in fields:
                    if field_value and isinstance(field_value, str) and len(field_value) > 10:
                        source_text = field_value
                        break
                
                if source_text:
                    distributed_parts = self._split_text_intelligently(
                        source_text, len(fields), max_chars_per_field, respect_line_breaks
                    )
                    
                    # Assign distributed parts to fields
                    for i, (field_name, _) in enumerate(fields):
                        if i < len(distributed_parts):
                            distributed_data[field_name] = distributed_parts[i]
                        else:
                            distributed_data[field_name] = ""
                else:
                    # No significant content, keep original values
                    for field_name, field_value in fields:
                        distributed_data[field_name] = field_value
        
        return distributed_data
    
    def _group_multiline_fields(self, form_data: Dict[str, str]) -> Dict[str, List[tuple]]:
        """Group fields that belong to the same multi-line section."""
        groups = {}
        
        for field_name, field_value in form_data.items():
            # Check if this is a multi-line field (has "part N" pattern)
            if " (part " in field_name:
                base_name = field_name.split(" (part ")[0]
                if base_name not in groups:
                    groups[base_name] = []
                groups[base_name].append((field_name, field_value))
            else:
                # Individual field
                groups[field_name] = [(field_name, field_value)]
        
        # Sort multi-line groups by part number
        for base_name, fields in groups.items():
            if len(fields) > 1:
                groups[base_name] = sorted(fields, key=lambda x: self._extract_part_number(x[0]))
        
        return groups
    
    def _extract_part_number(self, field_name: str) -> int:
        """Extract part number from field name like 'I love... (part 2)'."""
        match = re.search(r'\(part (\d+)\)', field_name)
        return int(match.group(1)) if match else 0
    
    def _split_text_intelligently(self, text: str, num_fields: int, max_chars_per_field: int, 
                                respect_line_breaks: bool) -> List[str]:
        """Split text intelligently across multiple fields."""
        if not text or num_fields <= 1:
            return [text] if text else [""]
        
        # First, respect explicit line breaks if enabled
        if respect_line_breaks and '\n' in text:
            parts = [part.strip() for part in text.split('\n') if part.strip()]
            if len(parts) >= num_fields:
                return parts[:num_fields]
            # If we have fewer line-break parts than fields, continue with other methods
        
        # Split by natural break points
        parts = self._split_by_natural_breaks(text, num_fields, max_chars_per_field)
        
        # Ensure we have exactly num_fields parts
        while len(parts) < num_fields:
            parts.append("")
        
        return parts[:num_fields]
    
    def _split_by_natural_breaks(self, text: str, num_fields: int, max_chars_per_field: int) -> List[str]:
        """Split text by natural break points like sentences, commas, etc."""
        # Try different split strategies in order of preference
        
        # Strategy 1: Split by sentences
        sentences = re.split(r'[.!?]+\s+', text)
        if len(sentences) >= num_fields and all(len(s) <= max_chars_per_field * 1.2 for s in sentences):
            return [s.strip() for s in sentences if s.strip()][:num_fields]
        
        # Strategy 2: Split by commas or semicolons
        comma_parts = re.split(r'[,;]\s+', text)
        if len(comma_parts) >= num_fields:
            return [part.strip() for part in comma_parts if part.strip()][:num_fields]
        
        # Strategy 3: Split by conjunctions (and, or, but)
        conjunction_parts = re.split(r'\s+(and|or|but)\s+', text, flags=re.IGNORECASE)
        # Remove the conjunctions from the split
        clean_parts = [part.strip() for i, part in enumerate(conjunction_parts) 
                      if i % 2 == 0 and part.strip()]
        if len(clean_parts) >= num_fields:
            return clean_parts[:num_fields]
        
        # Strategy 4: Split by length, trying to break at word boundaries
        return self._split_by_length_with_word_boundaries(text, num_fields, max_chars_per_field)
    
    def _split_by_length_with_word_boundaries(self, text: str, num_fields: int, max_chars_per_field: int) -> List[str]:
        """Split text by length while respecting word boundaries."""
        words = text.split()
        if not words:
            return [""]
        
        parts = []
        current_part = []
        current_length = 0
        target_length = len(text) // num_fields
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            # If adding this word would exceed target length and we have content, start new part
            if (current_length + word_length > target_length and 
                current_part and len(parts) < num_fields - 1):
                parts.append(' '.join(current_part))
                current_part = [word]
                current_length = len(word)
            else:
                current_part.append(word)
                current_length += word_length
        
        # Add the last part
        if current_part:
            parts.append(' '.join(current_part))
        
        return parts
    
    def _fill_interactive_form(self, doc, form_data: Dict[str, str], field_mapping: Dict[str, str]) -> int:
        """Fill interactive PDF form fields using field mapping."""
        filled_count = 0
        
        # Create reverse mapping from PDF field names to semantic names
        reverse_mapping = {pdf_name: semantic_name for semantic_name, pdf_name in field_mapping.items()}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            widgets = list(page.widgets())
            
            for widget in widgets:
                field_name = widget.field_name
                if not field_name:
                    continue
                
                # Use field mapping to find corresponding semantic field
                if field_name in reverse_mapping:
                    semantic_name = reverse_mapping[field_name]
                    if semantic_name in form_data:
                        value = form_data[semantic_name]
                        widget.field_value = str(value)
                        widget.update()
                        filled_count += 1
        
        return filled_count
    
    def _fill_static_form(self, doc, form_data: Dict[str, str], field_mapping: Dict[str, str]) -> int:
        """Create text annotations for static PDF forms."""
        filled_count = 0
        
        # Use the last page by default for annotations
        if len(doc) > 0:
            page = doc[-1]
            
            # Starting position for annotations
            y_position = 100
            x_position = 50
            line_height = 20
            
            for field_name, value in form_data.items():
                if value and str(value).lower() not in ['false', '']:
                    # Create a text annotation
                    rect = fitz.Rect(x_position, y_position, x_position + 200, y_position + line_height)
                    
                    # Create the annotation with the field value
                    text_annot = page.add_freetext_annot(
                        rect,
                        f"{field_name}: {value}",
                        fontsize=10,
                        text_color=(0, 0, 0),
                        fill_color=(1, 1, 1),
                        border_color=(0.8, 0.8, 0.8)
                    )
                    text_annot.set_info(title="Form Field", content=field_name)
                    text_annot.update()
                    
                    filled_count += 1
                    y_position += line_height + 5
                    
                    # Move to next column if needed
                    if y_position > 700:
                        y_position = 100
                        x_position += 250
        
        return filled_count