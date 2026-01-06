"""
FastAPI Backend for Voice-Controlled PDF Assistant
Handles PDF uploads, processing, and downloads based on voice commands.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict

from app.models.schemas import (
    ProcessRequest,
    ProcessResponse,
    UploadResponse,
    ErrorResponse,
    HealthResponse
)
from app.services.pdf_service import PDFService
from app.services.command_parser import CommandParser
from app.utils.file_manager import FileManager
from app.utils.validators import validate_file_size, validate_pdf_pages
from app.utils.job_tracker import JobTracker
from app.utils.scheduler import CleanupScheduler
from app.middleware.rate_limiter import RateLimiter, RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
file_manager = FileManager()
pdf_service = PDFService(file_manager)
command_parser = CommandParser()
rate_limiter = RateLimiter()
job_tracker = JobTracker()
scheduler = CleanupScheduler(file_manager, job_tracker)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    logger.info("Starting Voice PDF Assistant Backend")
    file_manager.initialize()
    await scheduler.start()
    yield
    logger.info("Shutting down Voice PDF Assistant Backend")
    await scheduler.stop()
    file_manager.cleanup_all()


# Initialize FastAPI app
app = FastAPI(
    title="Voice PDF Assistant API",
    description="Backend API for voice-controlled PDF document processing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://voice-pdf-assistant.vercel.app",
        "https://voice-pdf-assistant-gavjain.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app"
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        JSON with API info and available endpoints
    """
    return {
        "service": "Voice PDF Assistant API",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "upload": "/api/upload",
            "process": "/api/process",
            "download": "/api/download/{file_id}"
        },
        "frontend": "http://localhost:3000"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify backend status.
    
    Returns:
        HealthResponse: Status of the service
    """
    return HealthResponse(
        status="healthy",
        message="Voice PDF Assistant Backend is running",
        version="1.0.0"
    )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> UploadResponse:
    """
    Upload a PDF file and return a unique file ID.
    
    Args:
        file: PDF file uploaded from frontend
        background_tasks: Background tasks for cleanup
        
    Returns:
        UploadResponse: Contains file_id and metadata
        
    Raises:
        HTTPException: If file validation fails
    """
    try:
        # Validate file type
        if not file.content_type == "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF files are accepted."
            )
        
        # Validate file size (max 50MB)
        content = await validate_file_size(file)
        file_size_mb = len(content) / (1024 * 1024)
        
        # Save file and get metadata
        file_id = file_manager.save_upload(content, file.filename)
        file_path = file_manager.get_file_path(file_id)
        
        # Validate PDF pages
        pdf_validation = validate_pdf_pages(str(file_path))
        page_count = pdf_validation["page_count"]
        
        logger.info(f"Uploaded PDF: {file.filename} (ID: {file_id}, Pages: {page_count})")
        
        # Schedule cleanup after 1 hour
        if background_tasks:
            background_tasks.add_task(
                file_manager.schedule_cleanup,
                file_id,
                delay_seconds=3600
            )
        
        response = UploadResponse(
            file_id=file_id,
            filename=file.filename,
            page_count=page_count,
            size_mb=round(file_size_mb, 2)
        )
        
        # Add warning if PDF is large
        if pdf_validation.get("warning"):
            logger.warning(pdf_validation["warning"])
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload PDF: {str(e)}"
        )


@app.post("/api/process", response_model=ProcessResponse)
async def process_pdf(
    request: ProcessRequest,
    background_tasks: BackgroundTasks = None
) -> ProcessResponse:
    """
    Process PDF based on detected voice command.
    
    Args:
        request: ProcessRequest containing file_id and command intent
        background_tasks: Background tasks for cleanup
        
    Returns:
        ProcessResponse: Contains result_file_id for download
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        # Validate file exists
        if not file_manager.file_exists(request.file_id):
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {request.file_id}"
            )
        
        # Parse and validate command
        command = command_parser.parse(request.intent, request.parameters)
        logger.info(f"Processing command: {command.action} for file {request.file_id}")
        
        # Execute PDF operation
        result_file_id = pdf_service.process_command(
            file_id=request.file_id,
            command=command
        )
        
        # Get result file metadata
        result_info = file_manager.get_file_info(result_file_id)
        
        logger.info(f"Processing complete: {result_file_id}")
        
        # Schedule cleanup for result file after 30 minutes
        if background_tasks:
            background_tasks.add_task(
                file_manager.schedule_cleanup,
                result_file_id,
                delay_seconds=1800
            )
        
        return ProcessResponse(
            result_file_id=result_file_id,
            filename=result_info['filename'],
            message=f"Successfully processed: {command.description}",
            operation=command.action
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )


@app.get("/api/download/{file_id}")
async def download_file(file_id: str) -> FileResponse:
    """
    Download processed PDF or DOCX file.
    
    Args:
        file_id: Unique identifier for the file
        
    Returns:
        FileResponse: File ready for download
        
    Raises:
        HTTPException: If file not found
    """
    try:
        file_path = file_manager.get_file_path(file_id)
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found or has expired: {file_id}"
            )
        
        file_info = file_manager.get_file_info(file_id)
        
        logger.info(f"Downloading file: {file_id}")
        
        return FileResponse(
            path=str(file_path),
            filename=file_info['filename'],
            media_type=file_info['mime_type']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )


@app.delete("/api/file/{file_id}")
async def delete_file(file_id: str) -> Dict[str, str]:
    """
    Manually delete a temporary file.
    
    Args:
        file_id: Unique identifier for the file
        
    Returns:
        Success message
    """
    try:
        file_manager.delete_file(file_id)
        logger.info(f"Deleted file: {file_id}")
        return {"message": f"File {file_id} deleted successfully"}
    except Exception as e:
        logger.warning(f"Delete failed: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {file_id}"
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred. Please try again."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
