"""Tests for configuration management."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from pdf_navigator_mcp.config import Config


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', mock_open()):
                config = Config()
                assert config.pdf_reader == "skim"
                assert config.reader_path is None
                assert config.search_context_chars == 100
                assert config.max_search_results == 10
    
    def test_load_existing_config(self):
        """Test loading existing configuration file."""
        mock_config = {
            "pdf_reader": "zathura",
            "reader_path": "/usr/bin/zathura",
            "search_context_chars": 150
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))):
                config = Config()
                assert config.pdf_reader == "zathura"
                assert config.reader_path == "/usr/bin/zathura"
                assert config.search_context_chars == 150
                assert config.max_search_results == 10  # Default value
    
    def test_load_invalid_config(self):
        """Test loading invalid configuration file."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                config = Config()
                # Should fall back to defaults
                assert config.pdf_reader == "skim"
    
    def test_get_set_config_value(self):
        """Test getting and setting configuration values."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', mock_open()):
                config = Config()
                
                # Test get
                assert config.get("pdf_reader") == "skim"
                assert config.get("nonexistent", "default") == "default"
                
                # Test set
                config.set("pdf_reader", "evince")
                assert config.get("pdf_reader") == "evince"
    
    def test_save_config(self):
        """Test saving configuration to file."""
        test_config = {"pdf_reader": "test"}
        
        with patch('pathlib.Path.exists', return_value=False):
            mock_file = mock_open()
            with patch('builtins.open', mock_file):
                config = Config()
                config.save_config(test_config)
                
                # Check that file was written
                mock_file.assert_called()
                handle = mock_file()
                written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
                assert '"pdf_reader": "test"' in written_data
    
    def test_custom_config_path(self):
        """Test using custom configuration path."""
        custom_path = Path("/tmp/custom-config.json")
        
        with patch('pathlib.Path.exists', return_value=False):
            with patch('builtins.open', mock_open()):
                config = Config(custom_path)
                assert config.config_path == custom_path