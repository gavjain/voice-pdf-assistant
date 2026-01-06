"""
Minimal job tracking database using SQLite.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class JobTracker:
    """Track PDF processing jobs in SQLite."""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    client_ip TEXT,
                    status TEXT DEFAULT 'processing',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    file_size_mb REAL,
                    page_count INTEGER,
                    error_message TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_id ON jobs(file_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at ON jobs(created_at)
            """)
            conn.commit()
        logger.info(f"Job tracker initialized at {self.db_path}")
    
    def create_job(
        self,
        file_id: str,
        operation: str,
        client_ip: Optional[str] = None,
        file_size_mb: Optional[float] = None,
        page_count: Optional[int] = None
    ) -> int:
        """
        Create a new job record.
        
        Returns:
            Job ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO jobs (file_id, operation, client_ip, file_size_mb, page_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (file_id, operation, client_ip, file_size_mb, page_count)
            )
            job_id = cursor.lastrowid
            conn.commit()
        logger.info(f"Created job {job_id} for {operation} on {file_id}")
        return job_id
    
    def complete_job(self, job_id: int, error: Optional[str] = None):
        """Mark job as completed or failed."""
        status = "failed" if error else "completed"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE jobs 
                SET status = ?, completed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
                """,
                (status, error, job_id)
            )
            conn.commit()
        logger.info(f"Job {job_id} {status}")
    
    def get_stats(self) -> Dict:
        """Get basic usage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
                    AVG(file_size_mb) as avg_file_size,
                    SUM(page_count) as total_pages_processed
                FROM jobs
            """)
            row = cursor.fetchone()
        
        return {
            "total_jobs": row[0] or 0,
            "completed": row[1] or 0,
            "failed": row[2] or 0,
            "processing": row[3] or 0,
            "avg_file_size_mb": round(row[4] or 0, 2),
            "total_pages_processed": row[5] or 0
        }
    
    def cleanup_old_jobs(self, days: int = 7):
        """Delete job records older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM jobs 
                WHERE created_at < datetime('now', '-' || ? || ' days')
                """,
                (days,)
            )
            deleted = cursor.rowcount
            conn.commit()
        logger.info(f"Cleaned up {deleted} old job records")
        return deleted
