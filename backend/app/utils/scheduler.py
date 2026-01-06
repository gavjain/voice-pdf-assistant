"""
Background scheduler for cleanup tasks.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable
from app.utils.file_manager import FileManager
from app.utils.job_tracker import JobTracker

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """Background scheduler for cleanup tasks."""
    
    def __init__(self, file_manager: FileManager, job_tracker: JobTracker):
        self.file_manager = file_manager
        self.job_tracker = job_tracker
        self.is_running = False
        self.cleanup_interval = 3600  # 1 hour in seconds
    
    async def start(self):
        """Start the cleanup scheduler."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Cleanup scheduler started")
        
        # Run cleanup loop in background
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """Stop the cleanup scheduler."""
        self.is_running = False
        logger.info("Cleanup scheduler stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop."""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._run_cleanup()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def _run_cleanup(self):
        """Run all cleanup tasks."""
        logger.info("Running scheduled cleanup...")
        
        # Clean up old files (older than 1 hour)
        try:
            deleted_count = self.file_manager.cleanup_old_files(hours=1)
            logger.info(f"Cleaned up {deleted_count} old files")
        except Exception as e:
            logger.error(f"File cleanup error: {e}")
        
        # Clean up old job records (older than 7 days)
        try:
            deleted_jobs = self.job_tracker.cleanup_old_jobs(days=7)
            logger.info(f"Cleaned up {deleted_jobs} old job records")
        except Exception as e:
            logger.error(f"Job cleanup error: {e}")
