"""
Unit Tests for File Tracker
============================

Tests for the FileTracker class.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.pipeline.file_tracker import FileTracker


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    yield f'sqlite:///{db_path}'

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


def test_file_tracker_initialization(temp_db):
    """Test file tracker initialization."""
    tracker = FileTracker(temp_db)
    assert tracker.initialize() == True
    tracker.close()


def test_mark_file_as_processed(temp_db):
    """Test marking a file as processed."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    # Mark a file as processed
    result = tracker.mark_processed(
        filename='test_file.csv',
        status='LOADED',
        record_count=100,
        file_size_bytes=1024
    )

    assert result == True
    assert tracker.is_processed('test_file.csv') == True

    tracker.close()


def test_get_processed_files(temp_db):
    """Test getting list of processed files."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    # Add multiple files
    files = ['file1.csv', 'file2.csv', 'file3.csv']
    for filename in files:
        tracker.mark_processed(filename, status='LOADED')

    # Get processed files
    processed = tracker.get_processed_files()

    assert len(processed) == 3
    assert set(processed) == set(files)

    tracker.close()


def test_is_not_processed(temp_db):
    """Test checking if a file is not processed."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    assert tracker.is_processed('nonexistent.csv') == False

    tracker.close()


def test_get_file_status(temp_db):
    """Test getting file status."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    # Mark a file
    tracker.mark_processed(
        filename='test.csv',
        status='LOADED',
        record_count=500,
        file_size_bytes=2048
    )

    # Get status
    status = tracker.get_file_status('test.csv')

    assert status is not None
    assert status['filename'] == 'test.csv'
    assert status['status'] == 'LOADED'
    assert status['record_count'] == 500
    assert status['file_size_bytes'] == 2048

    tracker.close()


def test_update_status(temp_db):
    """Test updating file status."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    # Mark a file as processing
    tracker.mark_processed('test.csv', status='PROCESSING')

    # Update to loaded
    tracker.update_status('test.csv', status='LOADED')

    # Verify update
    status = tracker.get_file_status('test.csv')
    assert status['status'] == 'LOADED'

    tracker.close()


def test_get_statistics(temp_db):
    """Test getting tracker statistics."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    # Add some files with different statuses
    tracker.mark_processed('file1.csv', status='LOADED', record_count=100)
    tracker.mark_processed('file2.csv', status='LOADED', record_count=200)
    tracker.mark_processed('file3.csv', status='FAILED')

    # Get statistics
    stats = tracker.get_statistics()

    assert stats['total_files'] == 3
    assert stats['loaded'] == 2
    assert stats['failed'] == 1
    assert stats['total_records'] == 300

    tracker.close()


def test_reset_tracker(temp_db):
    """Test resetting the tracker."""
    tracker = FileTracker(temp_db)
    tracker.initialize()

    # Add files
    tracker.mark_processed('file1.csv', status='LOADED')
    tracker.mark_processed('file2.csv', status='LOADED')

    # Reset
    assert tracker.reset() == True

    # Verify empty
    stats = tracker.get_statistics()
    assert stats['total_files'] == 0

    tracker.close()


def test_context_manager(temp_db):
    """Test using file tracker as context manager."""
    with FileTracker(temp_db) as tracker:
        tracker.initialize()
        tracker.mark_processed('test.csv', status='LOADED')
        assert tracker.is_processed('test.csv') == True
