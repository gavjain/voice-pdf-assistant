"""
File management utility for handling temporary PDF storage.
Implements secure file storage, retrieval, and automatic cleanup.
"""

import os
import uuid
import shutil
import tempfile
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages temporary file storage with automatic cleanup.
    Thread-safe operations for concurrent requests.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize FileManager.
        
        Args:
            base_dir: Base directory for file storage (optional)
        """
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "voice_pdf_assistant"
        self.uploads_dir = self.base_dir / "uploads"
        self.results_dir = self.base_dir / "results"
        self.metadata: Dict[str, Dict] = {}
        self.lock = Lock()
        
    def initialize(self):
        """Create necessary directories."""
        try:
            self.uploads_dir.mkdir(parents=True, exist_ok=True)
            self.results_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"FileManager initialized at {self.base_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize FileManager: {e}")
            raise
    
    def save_upload(self, content: bytes, original_filename: str) -> str:
        """
        Save uploaded PDF file.
        
        Args:
            content: File content as bytes
            original_filename: Original filename from upload
            
        Returns:
            str: Unique file_id
            
        Raises:
            ValueError: If file operations fail
        """
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Sanitize filename
            safe_filename = self._sanitize_filename(original_filename)
            file_extension = Path(safe_filename).suffix or ".pdf"
            
            # Create file path
            file_path = self.uploads_dir / f"{file_id}{file_extension}"
            
            # Write file
            file_path.write_bytes(content)
            
            # Store metadata
            with self.lock:
                self.metadata[file_id] = {
                    'filename': safe_filename,
                    'path': str(file_path),
                    'mime_type': 'application/pdf',
                    'size_bytes': len(content),
                    'created_at': datetime.utcnow().isoformat(),
                    'type': 'upload'
                }
            
            logger.info(f"Saved upload: {file_id} ({safe_filename})")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to save upload: {e}")
            raise ValueError(f"Failed to save file: {e}")
    
    def save_result(self, source_path: Path, original_filename: str, 
                   mime_type: str = "application/pdf") -> str:
        """
        Save processed result file.
        
        Args:
            source_path: Path to the processed file
            original_filename: Base filename for the result
            mime_type: MIME type of the result file
            
        Returns:
            str: Unique file_id for the result
        """
        try:
            file_id = str(uuid.uuid4())
            safe_filename = self._sanitize_filename(original_filename)
            file_extension = Path(safe_filename).suffix
            
            result_path = self.results_dir / f"{file_id}{file_extension}"
            
            # Copy processed file to results directory
            shutil.copy2(source_path, result_path)
            
            with self.lock:
                self.metadata[file_id] = {
                    'filename': safe_filename,
                    'path': str(result_path),
                    'mime_type': mime_type,
                    'size_bytes': result_path.stat().st_size,
                    'created_at': datetime.utcnow().isoformat(),
                    'type': 'result'
                }
            
            logger.info(f"Saved result: {file_id} ({safe_filename})")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
            raise ValueError(f"Failed to save result: {e}")
    
    def get_file_path(self, file_id: str) -> Path:
        """
        Get file path for a given file_id.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Path: File path
            
        Raises:
            ValueError: If file not found
        """
        with self.lock:
            if file_id not in self.metadata:
                raise ValueError(f"File not found: {file_id}")
            return Path(self.metadata[file_id]['path'])
    
    def get_file_info(self, file_id: str) -> Dict:
        """
        Get file metadata.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            Dict: File metadata
        """
        with self.lock:
            if file_id not in self.metadata:
                raise ValueError(f"File not found: {file_id}")
            return self.metadata[file_id].copy()
    
    def file_exists(self, file_id: str) -> bool:
        """
        Check if file exists.
        
        Args:
            file_id: Unique file identifier
            
        Returns:
            bool: True if file exists
        """
        with self.lock:
            if file_id not in self.metadata:
                return False
            path = Path(self.metadata[file_id]['path'])
            return path.exists()
    
    def delete_file(self, file_id: str):
        """
        Delete a file and its metadata.
        
        Args:
            file_id: Unique file identifier
        """
        try:
            with self.lock:
                if file_id in self.metadata:
                    file_path = Path(self.metadata[file_id]['path'])
                    if file_path.exists():
                        file_path.unlink()
                    del self.metadata[file_id]
                    logger.info(f"Deleted file: {file_id}")
        except Exception as e:
            logger.warning(f"Failed to delete file {file_id}: {e}")
    
    async def schedule_cleanup(self, file_id: str, delay_seconds: int = 1800):
        """
        Schedule automatic file cleanup after delay.
        
        Args:
            file_id: File to cleanup
            delay_seconds: Delay before cleanup (default 30 minutes)
        """
        await asyncio.sleep(delay_seconds)
        self.delete_file(file_id)
    
    def cleanup_all(self):
        """Clean up all temporary files."""
        try:
            file_ids = list(self.metadata.keys())
            for file_id in file_ids:
                self.delete_file(file_id)
            
            # Remove directories if empty
            for directory in [self.uploads_dir, self.results_dir]:
                if directory.exists() and not any(directory.iterdir()):
                    directory.rmdir()
            
            logger.info("Cleaned up all temporary files")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def cleanup_old_files(self, hours: int = 1) -> int:
        """
        Clean up files older than specified hours.
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            deleted_count = 0
            
            file_ids = list(self.metadata.keys())
            for file_id in file_ids:
                metadata = self.metadata.get(file_id)
                if metadata:
                    created_at = metadata.get('created_at')
                    if created_at and created_at < cutoff_time:
                        self.delete_file(file_id)
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old files")
            return deleted_count
        except Exception as e:
            logger.error(f"Old file cleanup failed: {e}")
            return 0
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name
        
        # Remove potentially dangerous characters
        dangerous_chars = ['..', '/', '\\', '\x00']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        return filename or "document.pdf"
    
    def get_temp_path(self, suffix: str = ".pdf") -> Path:
        """
        Get a temporary file path for intermediate processing.
        
        Args:
            suffix: File extension
            
        Returns:
            Path: Temporary file path
        """
        temp_id = str(uuid.uuid4())
        return self.results_dir / f"temp_{temp_id}{suffix}"
