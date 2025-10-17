"""
Demo script showing idempotent pipeline behavior.

scenario:
- run 1: process 40 files successfully, 8 fail
- run 2: only retry 8 failed files (40 skipped)
"""
import sys
import os
import sqlite3
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

import config

def simulate_partial_failure():
    """simulate first run with partial failures."""
    print("\nDemo: simulating partial pipeline failure...")
    print(f"Using DB: {config.TRACKER_DB_PATH}")

    # Connect to DB and mark some files as FAILED
    conn = sqlite3.connect(str(config.TRACKER_DB_PATH))
    cursor = conn.cursor()

    # Get current stats before modification
    cursor.execute("SELECT status, COUNT(*) FROM file_status GROUP BY status")
    print("\nCurrent state:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count}")

    # Count completed
    cursor.execute("SELECT COUNT(*) FROM file_status WHERE status='COMPLETED'")
    completed = cursor.fetchone()[0] # number of completed files

    # Ensure at least 40 completed files exist
    if completed < 40:
        print(f"\nNeed at least 40 completed files. Current: {completed}")
        print("Run pipeline first: python run_pipeline.py")
        return

    # Mark 8 files as FAILED to simulate partial failure
    # Update only files with COMPLETED status
    cursor.execute("""
        UPDATE file_status
        SET status = 'FAILED',
            error_message = 'simulated network timeout',
            last_updated = CURRENT_TIMESTAMP
        WHERE file_name IN (
            SELECT file_name FROM file_status
            WHERE status = 'COMPLETED'
            LIMIT 8
        )
    """)
    conn.commit()

    affected = cursor.rowcount
    print(f"\nSimulated failure: {affected} files marked as FAILED")

    # Show new stats
    cursor.execute("SELECT status, COUNT(*) FROM file_status GROUP BY status")
    print("\nAfter simulation:")
    for status, count in cursor.fetchall():
        print(f"  {status}: {count}")

    conn.close()

    print("\nNext step: run pipeline again to retry failed files")
    print(" python run_pipeline.py")
    print("\nExpected behavior:")
    print(f"  - Skip {completed - affected} completed files")
    print(f"  - Retry {affected} failed files only")


if __name__ == "__main__":
    simulate_partial_failure()
