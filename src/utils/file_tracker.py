"""
File Tracker - State management for idempotent data pipeline.

Prevents reprocessing of files during SFTP to Fabric migration.
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Set, Dict, Optional
from enum import Enum
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileStatus(Enum):
    """Pipeline processing states."""
    PENDING = "PENDING"
    DOWNLOADED = "DOWNLOADED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileTracker:
    """
    Manages file processing state with ACID guarantees.
    
    Features:
    - Idempotent operations (safe retries)
    - Granular state tracking per medallion layer
    - Batch status queries for orchestration
    - Audit trail with timestamps
    
    Usage:
        tracker = FileTracker(db_path="data/tracker.db")
        tracker.init_db()
        
        # Filter pending files
        pending = tracker.get_pending_files(all_files)
        
        # Update states
        tracker.update_status("file.csv", FileStatus.BRONZE_LOADED)
    """
    
    def __init__(self, db_path: Path):
        """Initialize tracker with SQLite backend."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """Context manager for DB connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Create tracking table with metadata columns."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_status (
                    file_name TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    load_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER,
                    file_size_bytes INTEGER,
                    error_message TEXT
                )
            """)
            # Index for fast pending queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON file_status(status)
            """)
        logger.info(f"Initialized tracker DB: {self.db_path}")
    
    def update_status(
        self,
        file_name: str,
        status: FileStatus,
        record_count: Optional[int] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """
        Update file processing state.
        
        Args:
            file_name: Source filename
            status: New processing state
            record_count: Number of records processed
            file_size: File size in bytes
            error_message: Error details if status=FAILED
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO file_status (
                    file_name, status, record_count, file_size_bytes, error_message
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_name) DO UPDATE SET
                    status = excluded.status,
                    last_updated = CURRENT_TIMESTAMP,
                    record_count = COALESCE(excluded.record_count, record_count),
                    file_size_bytes = COALESCE(excluded.file_size_bytes, file_size_bytes),
                    error_message = excluded.error_message
            """, (file_name, status.value, record_count, file_size, error_message))
        
        logger.info(f"Updated {file_name}: {status.value}")
    
    def get_status(self, file_name: str) -> Optional[FileStatus]:
        """Get current status of a file."""
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT status FROM file_status WHERE file_name = ?",
                (file_name,)
            ).fetchone()
            
            return FileStatus(result['status']) if result else None
    
    def get_pending_files(self, available_files: List[str]) -> List[str]:
        """
        Filter files that need processing.

        Returns files that are:
        - Not in tracker (new files)
        - Status = PENDING or FAILED
        """
        with self._get_connection() as conn:
            tracked = conn.execute(
                "SELECT file_name FROM file_status WHERE status = ?",
                (FileStatus.COMPLETED.value,)
            ).fetchall()

            completed = {row['file_name'] for row in tracked}

        pending = [f for f in available_files if f not in completed]
        logger.info(f"Pending files: {len(pending)}/{len(available_files)}")
        return pending
    
    def get_files_by_status(self, status: FileStatus) -> List[str]:
        """Get all files with specific status."""
        with self._get_connection() as conn:
            results = conn.execute(
                "SELECT file_name FROM file_status WHERE status = ?",
                (status.value,)
            ).fetchall()
            
            return [row['file_name'] for row in results]
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Get processing statistics for monitoring."""
        with self._get_connection() as conn:
            results = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM file_status
                GROUP BY status
            """).fetchall()
            
            stats = {row['status']: row['count'] for row in results}
        
        return stats
    
    def mark_failed(self, file_name: str, error: str):
        """Mark file as failed with error details."""
        self.update_status(
            file_name,
            FileStatus.FAILED,
            error_message=str(error)
        )
    
    def get_failed_files(self) -> List[Dict]:
        """Get all failed files with error details."""
        with self._get_connection() as conn:
            results = conn.execute("""
                SELECT file_name, error_message, last_updated
                FROM file_status
                WHERE status = ?
                ORDER BY last_updated DESC
            """, (FileStatus.FAILED.value,)).fetchall()
            
            return [dict(row) for row in results]
    
    def reset_file(self, file_name: str):
        """Reset file to PENDING for reprocessing."""
        self.update_status(file_name, FileStatus.PENDING)
        logger.info(f"Reset {file_name} to PENDING")
    
    def delete_file_record(self, file_name: str):
        """Remove file from tracker (use with caution)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM file_status WHERE file_name = ?", (file_name,))
        logger.warning(f"Deleted tracker record: {file_name}")
