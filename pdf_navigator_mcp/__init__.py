"""PDF Navigator MCP: PDF navigation and text search via MCP."""

__version__ = "0.1.0"

from .server import main
from .pdf_navigator import PDFNavigator
from .config import Config

__all__ = ["main", "PDFNavigator", "Config"]