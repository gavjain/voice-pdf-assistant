"""
Command parser service to interpret structured voice commands.
Maps frontend command intents to executable PDF operations.
"""

import logging
from typing import Dict, Any, List, Union
from app.models.schemas import PDFCommand, OutputFormat

logger = logging.getLogger(__name__)


class CommandParser:
    """
    Parses structured commands from frontend into PDFCommand objects.
    Validates parameters and provides human-readable descriptions.
    """
    
    def __init__(self):
        """Initialize command parser with supported operations."""
        self.supported_intents = {
            "convert_to_word": self._parse_convert_to_word,
            "extract_pages": self._parse_extract_pages,
            "extract_page_range": self._parse_extract_page_range,
            "remove_pages": self._parse_remove_pages,
            "merge_pages": self._parse_merge_pages,
            "extract_to_word": self._parse_extract_to_word,
        }
    
    def parse(self, intent: str, parameters: Dict[str, Any]) -> PDFCommand:
        """
        Parse command intent and parameters into PDFCommand.
        
        Args:
            intent: Command intent (e.g., "convert_to_word")
            parameters: Command parameters from frontend
            
        Returns:
            PDFCommand: Validated command object
            
        Raises:
            ValueError: If intent is unsupported or parameters invalid
        """
        if intent not in self.supported_intents:
            raise ValueError(f"Unsupported intent: {intent}")
        
        try:
            parser_func = self.supported_intents[intent]
            command = parser_func(parameters)
            logger.info(f"Parsed command: {command.action} - {command.description}")
            return command
        except Exception as e:
            logger.error(f"Command parsing failed: {e}")
            raise ValueError(f"Invalid command parameters: {e}")
    
    def _parse_convert_to_word(self, params: Dict[str, Any]) -> PDFCommand:
        """Parse convert entire PDF to Word command."""
        return PDFCommand(
            action="convert_to_word",
            description="Converting entire PDF to Word document",
            output_format=OutputFormat.DOCX
        )
    
    def _parse_extract_pages(self, params: Dict[str, Any]) -> PDFCommand:
        """
        Parse extract specific pages command.
        
        Expected params:
            - pages: int or List[int] - Page number(s) to extract
            - format: str (optional) - Output format (pdf/docx)
        """
        pages = params.get("pages")
        
        if pages is None:
            raise ValueError("Missing required parameter: pages")
        
        # Normalize pages to list
        if isinstance(pages, int):
            page_list = [pages]
        elif isinstance(pages, str) and pages.isdigit():
            page_list = [int(pages)]
        elif isinstance(pages, list):
            page_list = [int(p) for p in pages]
        else:
            raise ValueError(f"Invalid pages parameter: {pages}")
        
        # Validate page numbers
        if any(p < 1 for p in page_list):
            raise ValueError("Page numbers must be positive")
        
        output_format = params.get("format", "pdf")
        if output_format not in ["pdf", "docx"]:
            raise ValueError(f"Invalid output format: {output_format}")
        
        pages_str = ", ".join(map(str, page_list))
        description = f"Extracting page{'s' if len(page_list) > 1 else ''} {pages_str}"
        
        return PDFCommand(
            action="extract_pages",
            description=description,
            pages=page_list,
            output_format=OutputFormat(output_format)
        )
    
    def _parse_extract_page_range(self, params: Dict[str, Any]) -> PDFCommand:
        """
        Parse extract page range command.
        
        Expected params:
            - startPage: int - First page of range
            - endPage: int - Last page of range
            - format: str (optional) - Output format
        """
        start_page = params.get("startPage") or params.get("start_page")
        end_page = params.get("endPage") or params.get("end_page")
        
        if start_page is None or end_page is None:
            raise ValueError("Missing required parameters: startPage and endPage")
        
        start_page = int(start_page)
        end_page = int(end_page)
        
        if start_page < 1 or end_page < 1:
            raise ValueError("Page numbers must be positive")
        
        if start_page > end_page:
            raise ValueError(f"Invalid range: start ({start_page}) > end ({end_page})")
        
        output_format = params.get("format", "pdf")
        if output_format not in ["pdf", "docx"]:
            raise ValueError(f"Invalid output format: {output_format}")
        
        description = f"Extracting pages {start_page} to {end_page}"
        
        return PDFCommand(
            action="extract_page_range",
            description=description,
            page_range={"start": start_page, "end": end_page},
            output_format=OutputFormat(output_format)
        )
    
    def _parse_remove_pages(self, params: Dict[str, Any]) -> PDFCommand:
        """
        Parse remove pages command.
        
        Expected params:
            - pages: int or List[int] - Page(s) to remove
        """
        pages = params.get("pages")
        
        if pages is None:
            raise ValueError("Missing required parameter: pages")
        
        # Normalize to list
        if isinstance(pages, int):
            page_list = [pages]
        elif isinstance(pages, str) and pages.isdigit():
            page_list = [int(pages)]
        elif isinstance(pages, list):
            page_list = [int(p) for p in pages]
        else:
            raise ValueError(f"Invalid pages parameter: {pages}")
        
        if any(p < 1 for p in page_list):
            raise ValueError("Page numbers must be positive")
        
        pages_str = ", ".join(map(str, page_list))
        description = f"Removing page{'s' if len(page_list) > 1 else ''} {pages_str}"
        
        return PDFCommand(
            action="remove_pages",
            description=description,
            pages=page_list,
            output_format=OutputFormat.PDF
        )
    
    def _parse_merge_pages(self, params: Dict[str, Any]) -> PDFCommand:
        """
        Parse merge pages command.
        
        Expected params:
            - pages: List[int] - Pages to merge
            OR
            - startPage, endPage: int - Range to merge
        """
        pages = params.get("pages")
        start_page = params.get("startPage") or params.get("start_page")
        end_page = params.get("endPage") or params.get("end_page")
        
        if pages:
            # Explicit page list
            if isinstance(pages, list):
                page_list = [int(p) for p in pages]
            else:
                raise ValueError("pages parameter must be a list")
        elif start_page and end_page:
            # Page range
            start = int(start_page)
            end = int(end_page)
            if start < 1 or end < 1:
                raise ValueError("Page numbers must be positive")
            if start > end:
                raise ValueError(f"Invalid range: start ({start}) > end ({end})")
            page_list = list(range(start, end + 1))
        else:
            raise ValueError("Missing required parameters: pages or startPage/endPage")
        
        if any(p < 1 for p in page_list):
            raise ValueError("Page numbers must be positive")
        
        description = f"Merging {len(page_list)} pages into single document"
        
        return PDFCommand(
            action="merge_pages",
            description=description,
            pages=page_list,
            output_format=OutputFormat.PDF
        )
    
    def _parse_extract_to_word(self, params: Dict[str, Any]) -> PDFCommand:
        """
        Parse extract pages and convert to Word command.
        Combines extraction with Word conversion.
        """
        pages = params.get("pages")
        start_page = params.get("startPage") or params.get("start_page")
        end_page = params.get("endPage") or params.get("end_page")
        
        if pages:
            if isinstance(pages, int):
                page_list = [pages]
            elif isinstance(pages, list):
                page_list = [int(p) for p in pages]
            else:
                page_list = [int(pages)]
            pages_str = ", ".join(map(str, page_list))
            description = f"Extracting page{'s' if len(page_list) > 1 else ''} {pages_str} as Word document"
        elif start_page and end_page:
            start = int(start_page)
            end = int(end_page)
            page_list = list(range(start, end + 1))
            description = f"Extracting pages {start} to {end} as Word document"
        else:
            raise ValueError("Missing required parameters: pages or startPage/endPage")
        
        if any(p < 1 for p in page_list):
            raise ValueError("Page numbers must be positive")
        
        return PDFCommand(
            action="extract_to_word",
            description=description,
            pages=page_list,
            output_format=OutputFormat.DOCX
        )
