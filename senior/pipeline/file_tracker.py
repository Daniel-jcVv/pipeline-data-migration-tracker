"""
File Tracker
============

Tracks processed files to ensure idempotent pipeline execution.
This is the core component that prevents reprocessing of already migrated files.

Based on the transcript logic:
1. Maintain a file_tracker table with processed file names
2. Compare source files with processed files
3. Filter out already processed files
4. Only process remaining files
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
import os


class FileTracker:
    """
    File Tracker to maintain state of processed files.

    This class implements the file tracking logic described in the transcript:
    - Store processed file details in a database table
    - Query which files have been processed
    - Mark new files as processed after successful migration

    Example usage:
        tracker = FileTracker('sqlite:///migration.db')
        tracker.initialize()

        # Check if file was processed
        if not tracker.is_processed('orders_data.csv'):
            # Process file...
            tracker.mark_processed('orders_data.csv', status='LOADED')
    """

    def __init__(self, connection_string: str):
        """
        Initialize File Tracker.

        Args:
            connection_string: Database connection string.
                For SQLite: 'sqlite:///path/to/file.db'
                For Fabric Warehouse: Use appropriate connection string
        """
        self.connection_string = connection_string
        self.conn = None

        # Parse connection string
        if connection_string.startswith('sqlite://'):
            self.db_type = 'sqlite'
            self.db_path = connection_string.replace('sqlite:///', '')
        else:
            # For future: support Fabric Warehouse connection
            self.db_type = 'warehouse'
            raise NotImplementedError("Warehouse connection not yet implemented")

    def initialize(self) -> bool:
        """
        Initialize the file_tracker table.

        Creates the table if it doesn't exist with schema:
        - filename: VARCHAR(255) PRIMARY KEY
        - load_date: DATETIME
        - status: VARCHAR(50)
        - record_count: INT
        - file_size_bytes: BIGINT
        - source_path: VARCHAR(500)

        Returns:
            bool: True if initialization successful
        """
        try:
            self._connect()

            # Create file_tracker table
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS file_tracker (
                filename VARCHAR(255) PRIMARY KEY,
                load_date DATETIME NOT NULL,
                status VARCHAR(50) NOT NULL,
                record_count INTEGER,
                file_size_bytes INTEGER,
                source_path VARCHAR(500),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """

            cursor = self.conn.cursor()
            cursor.execute(create_table_sql)
            self.conn.commit()

            print("✓ File tracker table initialized successfully")
            return True

        except Exception as e:
            print(f"✗ Error initializing file tracker: {e}")
            return False

    def is_processed(self, filename: str) -> bool:
        """
        Check if a file has been processed.

        Args:
            filename: Name of the file to check

        Returns:
            bool: True if file has been processed, False otherwise
        """
        try:
            self._connect()

            query = """
            SELECT COUNT(*) FROM file_tracker
            WHERE filename = ?
            """

            cursor = self.conn.cursor()
            cursor.execute(query, (filename,))
            count = cursor.fetchone()[0]

            return count > 0

        except Exception as e:
            print(f"Error checking if file is processed: {e}")
            return False

    def get_processed_files(self) -> List[str]:
        """
        Get list of all processed filenames.

        This is equivalent to the Lookup activity in Fabric pipeline.

        Returns:
            List of processed filenames
        """
        try:
            self._connect()

            query = """
            SELECT filename FROM file_tracker
            ORDER BY load_date DESC
            """

            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            return [row[0] for row in results]

        except Exception as e:
            print(f"Error getting processed files: {e}")
            return []

    def mark_processed(
        self,
        filename: str,
        status: str = 'LOADED',
        record_count: Optional[int] = None,
        file_size_bytes: Optional[int] = None,
        source_path: Optional[str] = None
    ) -> bool:
        """
        Mark a file as processed.

        This should be called AFTER both copies (Lakehouse + Warehouse) succeed.

        Args:
            filename: Name of the processed file
            status: Status ('LOADED', 'FAILED', 'PROCESSING')
            record_count: Number of records processed
            file_size_bytes: Size of file in bytes
            source_path: Original source path of file

        Returns:
            bool: True if marking successful
        """
        try:
            self._connect()

            insert_sql = """
            INSERT INTO file_tracker
            (filename, load_date, status, record_count, file_size_bytes, source_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            cursor = self.conn.cursor()
            cursor.execute(insert_sql, (
                filename,
                datetime.now(),
                status,
                record_count,
                file_size_bytes,
                source_path
            ))
            self.conn.commit()

            print(f"✓ Marked file as processed: {filename}")
            return True

        except Exception as e:
            print(f"✗ Error marking file as processed: {e}")
            return False

    def update_status(self, filename: str, status: str) -> bool:
        """
        Update the status of a processed file.

        Args:
            filename: Name of the file
            status: New status

        Returns:
            bool: True if update successful
        """
        try:
            self._connect()

            update_sql = """
            UPDATE file_tracker
            SET status = ?, load_date = ?
            WHERE filename = ?
            """

            cursor = self.conn.cursor()
            cursor.execute(update_sql, (status, datetime.now(), filename))
            self.conn.commit()

            return True

        except Exception as e:
            print(f"Error updating file status: {e}")
            return False

    def get_file_status(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get complete status information for a file.

        Args:
            filename: Name of the file

        Returns:
            Dictionary with file tracking info, or None if not found
        """
        try:
            self._connect()

            query = """
            SELECT filename, load_date, status, record_count,
                   file_size_bytes, source_path, created_at
            FROM file_tracker
            WHERE filename = ?
            """

            cursor = self.conn.cursor()
            cursor.execute(query, (filename,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'filename': row[0],
                'load_date': row[1],
                'status': row[2],
                'record_count': row[3],
                'file_size_bytes': row[4],
                'source_path': row[5],
                'created_at': row[6]
            }

        except Exception as e:
            print(f"Error getting file status: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about processed files.

        Returns:
            Dictionary with statistics (total files, by status, etc.)
        """
        try:
            self._connect()

            stats_query = """
            SELECT
                COUNT(*) as total_files,
                SUM(CASE WHEN status = 'LOADED' THEN 1 ELSE 0 END) as loaded,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(record_count) as total_records,
                SUM(file_size_bytes) as total_bytes
            FROM file_tracker
            """

            cursor = self.conn.cursor()
            cursor.execute(stats_query)
            row = cursor.fetchone()

            return {
                'total_files': row[0] or 0,
                'loaded': row[1] or 0,
                'failed': row[2] or 0,
                'total_records': row[3] or 0,
                'total_bytes': row[4] or 0
            }

        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}

    def reset(self) -> bool:
        """
        Reset the file tracker (delete all records).

        WARNING: Use with caution! This will remove all tracking history.

        Returns:
            bool: True if reset successful
        """
        try:
            self._connect()

            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM file_tracker")
            self.conn.commit()

            print("✓ File tracker reset successfully")
            return True

        except Exception as e:
            print(f"✗ Error resetting file tracker: {e}")
            return False

    def _connect(self):
        """Establish database connection if not already connected."""
        if self.conn is None:
            if self.db_type == 'sqlite':
                # Create directory if needed
                os.makedirs(os.path.dirname(self.db_path) or '.', exist_ok=True)
                self.conn = sqlite3.connect(self.db_path)

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
