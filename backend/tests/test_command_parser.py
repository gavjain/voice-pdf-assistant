"""
Unit tests for CommandParser service.
"""

import pytest
from app.services.command_parser import CommandParser
from app.models.schemas import OutputFormat


@pytest.fixture
def parser():
    """Create CommandParser instance."""
    return CommandParser()


class TestCommandParser:
    """Test suite for CommandParser."""
    
    def test_convert_to_word(self, parser):
        """Test convert to Word command parsing."""
        command = parser.parse("convert_to_word", {})
        
        assert command.action == "convert_to_word"
        assert command.output_format == OutputFormat.DOCX
        assert "Converting entire PDF" in command.description
    
    def test_extract_single_page(self, parser):
        """Test extracting a single page."""
        command = parser.parse("extract_pages", {"pages": 3, "format": "pdf"})
        
        assert command.action == "extract_pages"
        assert command.pages == [3]
        assert command.output_format == OutputFormat.PDF
        assert "page 3" in command.description.lower()
    
    def test_extract_multiple_pages(self, parser):
        """Test extracting multiple pages."""
        command = parser.parse("extract_pages", {"pages": [1, 3, 5], "format": "docx"})
        
        assert command.action == "extract_pages"
        assert command.pages == [1, 3, 5]
        assert command.output_format == OutputFormat.DOCX
        assert "pages" in command.description.lower()
    
    def test_extract_page_range(self, parser):
        """Test extracting page range."""
        command = parser.parse(
            "extract_page_range",
            {"startPage": 2, "endPage": 5, "format": "pdf"}
        )
        
        assert command.action == "extract_page_range"
        assert command.page_range == {"start": 2, "end": 5}
        assert command.output_format == OutputFormat.PDF
        assert "2 to 5" in command.description
    
    def test_remove_pages(self, parser):
        """Test removing pages."""
        command = parser.parse("remove_pages", {"pages": [1, 3]})
        
        assert command.action == "remove_pages"
        assert command.pages == [1, 3]
        assert command.output_format == OutputFormat.PDF
        assert "Removing" in command.description
    
    def test_merge_pages_with_list(self, parser):
        """Test merging pages with explicit list."""
        command = parser.parse("merge_pages", {"pages": [2, 3, 4]})
        
        assert command.action == "merge_pages"
        assert command.pages == [2, 3, 4]
        assert "Merging 3 pages" in command.description
    
    def test_merge_pages_with_range(self, parser):
        """Test merging pages with range."""
        command = parser.parse("merge_pages", {"startPage": 1, "endPage": 5})
        
        assert command.action == "merge_pages"
        assert command.pages == [1, 2, 3, 4, 5]
        assert "Merging 5 pages" in command.description
    
    def test_extract_to_word(self, parser):
        """Test extract to Word command."""
        command = parser.parse("extract_to_word", {"pages": [2, 3]})
        
        assert command.action == "extract_to_word"
        assert command.pages == [2, 3]
        assert command.output_format == OutputFormat.DOCX
    
    def test_invalid_intent(self, parser):
        """Test handling of invalid intent."""
        with pytest.raises(ValueError, match="Unsupported intent"):
            parser.parse("invalid_intent", {})
    
    def test_missing_pages_parameter(self, parser):
        """Test handling of missing pages parameter."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            parser.parse("extract_pages", {})
    
    def test_invalid_page_range(self, parser):
        """Test handling of invalid page range."""
        with pytest.raises(ValueError, match="Invalid range"):
            parser.parse("extract_page_range", {"startPage": 5, "endPage": 2})
    
    def test_negative_page_number(self, parser):
        """Test handling of negative page numbers."""
        with pytest.raises(ValueError, match="must be positive"):
            parser.parse("extract_pages", {"pages": -1})
    
    def test_invalid_output_format(self, parser):
        """Test handling of invalid output format."""
        with pytest.raises(ValueError, match="Invalid output format"):
            parser.parse("extract_pages", {"pages": 1, "format": "txt"})
