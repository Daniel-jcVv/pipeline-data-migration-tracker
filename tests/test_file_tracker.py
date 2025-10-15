"""
Unit tests for file_tracker_sv module.

Tests the core idempotency functionality of the data migration pipeline.
"""

import pytest
import sqlite3
import tempfile
import os
from src.services.file_tracker import (
    init_tracker,
    mark_as_processed,
    get_processed_files,
    filter_unprocessed_files,
    is_file_processed
)


class TestFileTracker:
    """Test suite for file tracking functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
    
    def test_init_tracker_creates_table(self, temp_db):
        """Test that init_tracker creates the file_tracker table."""
        conn = init_tracker(temp_db)
        
        # Verify table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='file_tracker'"
        )
        result = cursor.fetchone()
        
        assert result is not None
        conn.close()
    
    def test_mark_as_processed(self, temp_db):
        """Test marking a file as processed."""
        conn = init_tracker(temp_db)
        
        # Mark file as processed
        mark_as_processed(conn, 'test.csv', status='LOADED', file_size=1024)
        
        # Verify it was inserted
        cursor = conn.cursor()
        cursor.execute("SELECT filename, status FROM file_tracker WHERE filename = ?", ('test.csv',))
        result = cursor.fetchone()
        
        assert result[0] == 'test.csv'
        assert result[1] == 'LOADED'
        conn.close()
    
    def test_get_processed_files(self, temp_db):
        """Test retrieving list of processed files."""
        conn = init_tracker(temp_db)
        
        # Mark multiple files as processed
        mark_as_processed(conn, 'file1.csv', status='LOADED')
        mark_as_processed(conn, 'file2.csv', status='LOADED')
        mark_as_processed(conn, 'file3.csv', status='FAILED')  # Should not be included
        
        # Get processed files (LOADED only)
        processed = get_processed_files(conn)
        
        assert len(processed) == 2
        assert 'file1.csv' in processed
        assert 'file2.csv' in processed
        assert 'file3.csv' not in processed
        conn.close()
    
    def test_filter_unprocessed_files(self, temp_db):
        """Test filtering out already-processed files."""
        all_files = [
            {'name': 'file1.csv', 'size': 100},
            {'name': 'file2.csv', 'size': 200},
            {'name': 'file3.csv', 'size': 300}
        ]
        
        processed_files = ['file1.csv']
        
        result = filter_unprocessed_files(all_files, processed_files)
        
        assert len(result) == 2
        assert result[0]['name'] == 'file2.csv'
        assert result[1]['name'] == 'file3.csv'
    
    def test_is_file_processed(self, temp_db):
        """Test checking if a specific file was processed."""
        conn = init_tracker(temp_db)
        
        # Mark one file as processed
        mark_as_processed(conn, 'processed.csv', status='LOADED')
        
        # Check status
        assert is_file_processed(conn, 'processed.csv') is True
        assert is_file_processed(conn, 'not_processed.csv') is False
        
        conn.close()
    
    def test_idempotency_on_retry(self, temp_db):
        """Test that re-running pipeline skips processed files."""
        conn = init_tracker(temp_db)
        
        # First run: Process 3 files
        all_files = [
            {'name': 'file1.csv', 'size': 100},
            {'name': 'file2.csv', 'size': 200},
            {'name': 'file3.csv', 'size': 300}
        ]
        
        mark_as_processed(conn, 'file1.csv', status='LOADED')
        mark_as_processed(conn, 'file2.csv', status='LOADED')
        # file3.csv failed
        
        # Second run: Should only get file3
        processed = get_processed_files(conn)
        to_process = filter_unprocessed_files(all_files, processed)
        
        assert len(to_process) == 1
        assert to_process[0]['name'] == 'file3.csv'
        
        conn.close()
