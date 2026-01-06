"""
Pydantic models for request/response validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from enum import Enum


class Intent(str, Enum):
    """Supported command intents."""
    CONVERT_TO_WORD = "convert_to_word"
    EXTRACT_PAGES = "extract_pages"
    EXTRACT_PAGE_RANGE = "extract_page_range"
    REMOVE_PAGES = "remove_pages"
    MERGE_PAGES = "merge_pages"
    EXTRACT_TO_WORD = "extract_to_word"


class OutputFormat(str, Enum):
    """Supported output formats."""
    PDF = "pdf"
    DOCX = "docx"


# Request Models
class ProcessRequest(BaseModel):
    """Request model for processing PDF commands."""
    file_id: str = Field(..., description="Unique identifier of uploaded PDF")
    intent: str = Field(..., description="Command intent (e.g., 'convert_to_word')")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Command parameters (pages, format, etc.)"
    )
    
    @field_validator('file_id')
    @classmethod
    def validate_file_id(cls, v: str) -> str:
        """Validate file_id format."""
        if not v or len(v) < 10:
            raise ValueError("Invalid file_id")
        return v
    
    @field_validator('intent')
    @classmethod
    def validate_intent(cls, v: str) -> str:
        """Validate intent is recognized."""
        valid_intents = [
            "convert_to_word",
            "extract_pages",
            "extract_page_range",
            "remove_pages",
            "merge_pages",
            "extract_to_word"
        ]
        if v not in valid_intents:
            raise ValueError(f"Unsupported intent: {v}")
        return v


# Response Models
class UploadResponse(BaseModel):
    """Response model for file upload."""
    file_id: str = Field(..., description="Unique identifier for uploaded file")
    filename: str = Field(..., description="Original filename")
    page_count: int = Field(..., description="Number of pages in PDF")
    size_mb: float = Field(..., description="File size in megabytes")


class ProcessResponse(BaseModel):
    """Response model for processing result."""
    result_file_id: str = Field(..., description="ID of processed file")
    filename: str = Field(..., description="Filename of processed file")
    message: str = Field(..., description="Success message")
    operation: str = Field(..., description="Operation performed")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")


# Internal Models
class PDFCommand(BaseModel):
    """Internal model representing a parsed command."""
    action: str = Field(..., description="Action to perform")
    description: str = Field(..., description="Human-readable description")
    pages: Optional[Union[int, List[int], str]] = Field(
        None,
        description="Page(s) to operate on"
    )
    page_range: Optional[Dict[str, int]] = Field(
        None,
        description="Page range with start and end"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.PDF,
        description="Output file format"
    )
    
    class Config:
        use_enum_values = True


class FileMetadata(BaseModel):
    """Metadata for stored files."""
    file_id: str
    filename: str
    mime_type: str
    size_bytes: int
    created_at: str
    expires_at: Optional[str] = None
