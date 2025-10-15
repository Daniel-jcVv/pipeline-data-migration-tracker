-- 
-- File Tracker Schema for SQLite
-- 
-- Purpose: Maintains state of file processing for idempotent ETL pipeline




-- Main tracking table
CREATE TABLE IF NOT EXISTS file_tracker (
    -- Primary key: unique filename
    filename TEXT PRIMARY KEY,
    
    -- Timestamp when file was loaded
    load_date TEXT NOT NULL DEFAULT (datetime('now')),
    
    -- Processing status: LOADED_TO_FABRIC, FAILED, PROCESSING
    status TEXT NOT NULL CHECK (status IN ('LOADED_TO_FABRIC', 'FAILED', 'PROCESSING')),
    
    -- File metadata for validation
    file_size INTEGER,
    record_count INTEGER,
    
    -- Audit fields
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_status 
ON file_tracker(status);

CREATE INDEX IF NOT EXISTS idx_load_date 
ON file_tracker(load_date DESC);

CREATE INDEX IF NOT EXISTS idx_status_date 
ON file_tracker(status, load_date DESC);

-- ============================================================================
-- Query Examples
-- ============================================================================

-- Get all successfully processed files
-- SELECT filename, load_date FROM file_tracker WHERE status = 'LOADED_TO_FABRIC' ORDER BY load_date DESC;

-- Get processing statistics
-- SELECT status, COUNT(*) as count FROM file_tracker GROUP BY status;

-- Find files that failed
-- SELECT filename, load_date FROM file_tracker WHERE status = 'FAILED';

-- Check if specific file was processed
-- SELECT COUNT(*) FROM file_tracker WHERE filename = 'orders_2024.csv' AND status = 'LOADED_TO_FABRIC';

-- Get processing summary
-- SELECT 
--     COUNT(*) as total_files,
--     SUM(CASE WHEN status = 'LOADED_TO_FABRIC' THEN 1 ELSE 0 END) as loaded,
--     SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
--     SUM(file_size) as total_size_bytes
-- FROM file_tracker;
