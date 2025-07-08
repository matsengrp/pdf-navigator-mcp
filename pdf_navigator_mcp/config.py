"""Configuration management for PDF Navigator MCP."""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class Config:
    """Configuration manager for PDF Navigator MCP."""
    
    DEFAULT_CONFIG = {
        "pdf_reader": "skim",  # Default to Skim on macOS
        "reader_path": None,   # Auto-detect if None
        "search_context_chars": 100,  # Characters around search results
        "max_search_results": 10,     # Max results per search
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to config file. Defaults to ~/.pdf-navigator-config.json
        """
        self.config_path = config_path or Path.home() / ".pdf-navigator-config.json"
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file, create with defaults if missing."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            except (json.JSONDecodeError, IOError):
                pass
        
        # Create default config file
        self.save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError:
            pass
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value) -> None:
        """Set configuration value and save."""
        self.config[key] = value
        self.save_config(self.config)
    
    @property
    def pdf_reader(self) -> str:
        """Get configured PDF reader."""
        return self.get("pdf_reader", "skim")
    
    @property
    def reader_path(self) -> Optional[str]:
        """Get configured reader path."""
        return self.get("reader_path")
    
    @property
    def search_context_chars(self) -> int:
        """Get search context character count."""
        return self.get("search_context_chars", 100)
    
    @property
    def max_search_results(self) -> int:
        """Get max search results."""
        return self.get("max_search_results", 10)