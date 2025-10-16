"""Unit tests for ingestion module."""
import pytest
import sqlite3
from pathlib import Path
from src.ingestion import init_tracker_db, get_processed_files, mark_as_processed

def test_tracker_db_creation(tmp_path):
    """Test tracker database initialization."""
    import config
    config.TRACKER_DB_PATH = tmp_path / "test_tracker.db"
    
    init_tracker_db()
    assert config.TRACKER_DB_PATH.exists()
    
    conn = sqlite3.connect(config.TRACKER_DB_PATH)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert 'processed_files' in tables
    conn.close()

def test_mark_and_get_processed_files(tmp_path):
    """Test file tracking operations."""
    import config
    config.TRACKER_DB_PATH = tmp_path / "test_tracker.db"
    
    init_tracker_db()
    
    mark_as_processed("file1.csv")
    mark_as_processed("file2.csv")
    
    processed = get_processed_files()
    assert "file1.csv" in processed
    assert "file2.csv" in processed
    assert len(processed) == 2
