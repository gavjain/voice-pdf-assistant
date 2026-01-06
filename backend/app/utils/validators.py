"""
Validators for file uploads and PDF processing.
"""

from fastapi import UploadFile, HTTPException
import fitz  # PyMuPDF
import io
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DEFAULT_PAGE_LIMIT = 50
HARD_PAGE_LIMIT = 100


async def validate_file_size(file: UploadFile, max_size: int = MAX_FILE_SIZE) -> bytes:
    """
    Validate file size and return file contents.
    
    Args:
        file: Uploaded file
        max_size: Maximum allowed size in bytes
        
    Returns:
        File contents as bytes
        
    Raises:
        HTTPException: If file exceeds size limit
    """
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        logger.warning(f"File too large: {size_mb:.2f}MB (max: {max_mb}MB)")
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_mb}MB. Your file is {size_mb:.2f}MB."
        )
    
    return contents


def validate_pdf_pages(pdf_path: str, default_limit: int = DEFAULT_PAGE_LIMIT) -> dict:
    """
    Validate PDF page count and return metadata.
    
    Args:
        pdf_path: Path to PDF file
        default_limit: Default page limit for warnings
        
    Returns:
        dict with page_count, is_within_default, is_within_hard_limit
        
    Raises:
        HTTPException: If PDF exceeds hard page limit
    """
    try:
        doc = fitz.open(pdf_path)
        page_count = doc.page_count
        doc.close()
        
        if page_count > HARD_PAGE_LIMIT:
            logger.warning(f"PDF exceeds hard limit: {page_count} pages (max: {HARD_PAGE_LIMIT})")
            raise HTTPException(
                status_code=413,
                detail=f"PDF has too many pages. Maximum is {HARD_PAGE_LIMIT} pages. Your PDF has {page_count} pages."
            )
        
        return {
            "page_count": page_count,
            "is_within_default": page_count <= default_limit,
            "is_within_hard_limit": page_count <= HARD_PAGE_LIMIT,
            "warning": None if page_count <= default_limit else f"PDF has {page_count} pages. Processing may be slower for large documents."
        }
    
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error validating PDF: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file. Unable to read document."
        )


def validate_page_range(page_count: int, page_range: str) -> list:
    """
    Validate and parse page range.
    
    Args:
        page_count: Total pages in PDF
        page_range: Page range string (e.g., "1-5", "1,3,5", "1-3,5-7")
        
    Returns:
        List of valid page numbers (0-indexed)
        
    Raises:
        HTTPException: If page range is invalid
    """
    try:
        pages = set()
        parts = page_range.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                start, end = int(start), int(end)
                if start < 1 or end > page_count or start > end:
                    raise ValueError(f"Invalid range: {part}")
                pages.update(range(start - 1, end))
            else:
                page_num = int(part)
                if page_num < 1 or page_num > page_count:
                    raise ValueError(f"Invalid page: {page_num}")
                pages.add(page_num - 1)
        
        return sorted(list(pages))
    
    except Exception as e:
        logger.error(f"Error parsing page range: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid page range. Use format like '1-5' or '1,3,5'. Error: {str(e)}"
        )
