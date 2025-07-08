"""Tests for PDF Navigator functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from pdf_navigator_mcp.pdf_navigator import PDFNavigator
from pdf_navigator_mcp.config import Config


class TestPDFNavigator:
    """Test PDF Navigator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Config()
        self.navigator = PDFNavigator(self.config)
    
    def test_init_with_config(self):
        """Test initialization with custom config."""
        custom_config = Config()
        navigator = PDFNavigator(custom_config)
        assert navigator.config == custom_config
    
    def test_init_without_config(self):
        """Test initialization without config creates default."""
        navigator = PDFNavigator()
        assert navigator.config is not None
        assert isinstance(navigator.config, Config)
    
    def test_open_pdf_page_file_not_found(self):
        """Test opening non-existent PDF file."""
        result = self.navigator.open_pdf_page("/nonexistent/file.pdf", 1)
        assert "Error: PDF file not found" in result
    
    def test_open_pdf_page_not_pdf(self):
        """Test opening non-PDF file."""
        result = self.navigator.open_pdf_page("/path/to/file.txt", 1)
        assert "Error: File is not a PDF" in result
    
    def test_search_pdf_text_file_not_found(self):
        """Test searching non-existent PDF file."""
        result = self.navigator.search_pdf_text("/nonexistent/file.pdf", "test")
        assert "Error: PDF file not found" in result
    
    def test_get_pdf_info_file_not_found(self):
        """Test getting info for non-existent PDF file."""
        result = self.navigator.get_pdf_info("/nonexistent/file.pdf")
        assert "Error: PDF file not found" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.subprocess.run')
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_open_with_skim(self, mock_fitz, mock_subprocess):
        """Test opening PDF with Skim."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=10)
        mock_fitz.return_value = mock_doc
        
        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.suffix', '.pdf'):
                self.config.set('pdf_reader', 'skim')
                result = self.navigator.open_pdf_page("/test/file.pdf", 5)
                
                mock_subprocess.assert_called_once()
                assert "Opened file.pdf to page 5" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_search_pdf_text_no_results(self, mock_fitz):
        """Test searching PDF with no results."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_page = Mock()
        mock_page.get_text.return_value = "This is some text without the query"
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.search_pdf_text("/test/file.pdf", "missing")
            assert "No results found" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_search_pdf_text_with_results(self, mock_fitz):
        """Test searching PDF with results."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_page = Mock()
        mock_page.get_text.return_value = "This is some text with the query term in it"
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.search_pdf_text("/test/file.pdf", "query")
            assert "Found 1 results" in result
            assert "Page 1:" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_get_pdf_info(self, mock_fitz):
        """Test getting PDF metadata."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=5)
        mock_doc.metadata = {
            'title': 'Test Document',
            'author': 'Test Author',
            'subject': 'Test Subject'
        }
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.get_pdf_info("/test/file.pdf")
            assert "Pages: 5" in result
            assert "Title: Test Document" in result
            assert "Author: Test Author" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_read_pdf_text(self, mock_fitz):
        """Test reading PDF text from page range."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=5)
        mock_page = Mock()
        mock_page.get_text.return_value = "This is page content"
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.read_pdf_text("/test/file.pdf", 1, 2)
            assert "--- Page 1 ---" in result
            assert "--- Page 2 ---" in result
            assert "This is page content" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_read_pdf_page(self, mock_fitz):
        """Test reading single PDF page."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=5)
        mock_page = Mock()
        mock_page.get_text.return_value = "Single page content"
        mock_doc.__getitem__ = Mock(return_value=mock_page)
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.read_pdf_page("/test/file.pdf", 3)
            assert "--- Page 3 ---" in result
            assert "Single page content" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_get_pdf_structure(self, mock_fitz):
        """Test getting PDF structure."""
        # Mock PDF document
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=3)
        mock_doc.get_toc.return_value = [
            [1, "Introduction", 1],
            [1, "Methods", 2],
            [1, "Results", 3]
        ]
        
        # Mock pages
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "Introduction section\nThis is the intro"
        mock_page2 = Mock()
        mock_page2.get_text.return_value = "Methods section\nOur methodology"
        mock_page3 = Mock()
        mock_page3.get_text.return_value = "Results section\nOur findings"
        
        mock_doc.__getitem__ = Mock(side_effect=[mock_page1, mock_page2, mock_page3])
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.get_pdf_structure("/test/file.pdf")
            assert "Table of Contents:" in result
            assert "Introduction (Page 1)" in result
            assert "Methods (Page 2)" in result
            assert "Results (Page 3)" in result
            assert "Page Summaries:" in result
    
    def test_read_pdf_text_file_not_found(self):
        """Test reading text from non-existent file."""
        result = self.navigator.read_pdf_text("/nonexistent/file.pdf")
        assert "Error: PDF file not found" in result
    
    @patch('pdf_navigator_mcp.pdf_navigator.fitz.open')
    def test_read_pdf_text_invalid_page_range(self, mock_fitz):
        """Test reading with invalid page range."""
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=5)
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.navigator.read_pdf_text("/test/file.pdf", 10, 15)
            assert "Error: Start page 10 out of range" in result