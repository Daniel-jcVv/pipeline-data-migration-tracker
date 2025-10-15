"""
Simple File Tracker
===================

Simple system to track processed files and avoid reprocessing.
Uses SQLite to keep record of which files have already been migrated.

Intermediate level - direct and easy to understand code.
"""

import sqlite3
from datetime import datetime
import os


def init_tracker(db_path='data/file_tracker.db'):
    """
    Initialize the file tracker database.
    Creates the table if it doesn't exist.

    Args:
        db_path: Path to SQLite file

    Returns:
        connection: Database connection
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_tracker (
            filename TEXT PRIMARY KEY,
            load_date TEXT NOT NULL,
            status TEXT NOT NULL,
            file_size INTEGER,
            record_count INTEGER
        )
    """)

    conn.commit()
    print(f"✓ File tracker initialized: {db_path}")
    return conn


def is_file_processed(conn, filename):
    """
    Check if a file has already been processed.

    Args:
        conn: SQLite connection
        filename: Name of file to check

    Returns:
        bool: True if already processed, False if not
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM file_tracker WHERE filename = ?",
        (filename,)
    )
    count = cursor.fetchone()[0]
    return count > 0


def mark_as_processed(conn, filename, status='LOADED',
                      file_size=None, record_count=None):
    """
    Mark a file as processed in the tracker.

    Args:
        conn: SQLite connection
        filename: Name of file
        status: Status (LOADED, FAILED, etc.)
        file_size: File size in bytes
        record_count: Number of records processed
    """
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO file_tracker
            (filename, load_date, status, file_size, record_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            filename,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            status,
            file_size,
            record_count
        ))

        conn.commit()
        print(f"✓ File marked as {status}: {filename}")

    except sqlite3.IntegrityError:
        print(f"⚠ File already exists in tracker: {filename}")


def get_processed_files(conn):
    """
    Get list of all processed files.

    Args:
        conn: SQLite connection

    Returns:
        list: List of processed file names
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT filename FROM file_tracker WHERE status = 'LOADED'"
    )
    rows = cursor.fetchall()
    return [row[0] for row in rows]


def get_tracker_stats(conn):
    """
    Get tracker statistics.

    Args:
        conn: SQLite connection

    Returns:
        dict: Dictionary with statistics
    """
    cursor = conn.cursor()

    # Total files
    cursor.execute("SELECT COUNT(*) FROM file_tracker")
    total = cursor.fetchone()[0]

    # By status
    cursor.execute("""
        SELECT status, COUNT(*)
        FROM file_tracker
        GROUP BY status
    """)
    by_status = dict(cursor.fetchall())

    return {
        'total_files': total,
        'by_status': by_status
    }


def filter_unprocessed_files(all_files, processed_files):
    """
    Filter files to get only UNPROCESSED ones.

    This is the key logic of the pipeline - compares files
    from source with those already processed.

    Args:
        all_files: List of dictionaries with info of all files
        processed_files: List of names of already processed files

    Returns:
        list: Only files that have NOT been processed
    """
    # Convert to set for fast lookup
    processed_set = set(processed_files)

    # Filter
    unprocessed = [
        f for f in all_files
        if f['name'] not in processed_set
    ]

    print(f"\n📊 Summary:")
    print(f"   Total files: {len(all_files)}")
    print(f"   Already processed: {len(processed_files)}")
    print(f"   To process: {len(unprocessed)}")

    return unprocessed


# ============================================
# Usage example
# ============================================
if __name__ == '__main__':
    # 1. Initialize tracker
    conn = init_tracker()

    # 2. Simulate some files
    test_files = [
        {'name': 'orders_2024_01.csv', 'size': 1024},
        {'name': 'orders_2024_02.csv', 'size': 2048},
        {'name': 'orders_2024_03.csv', 'size': 1536},
    ]

    # 3. Mark first 2 as processed
    mark_as_processed(conn, 'orders_2024_01.csv', file_size=1024)
    mark_as_processed(conn, 'orders_2024_02.csv', file_size=2048)

    # 4. See which files need processing
    processed = get_processed_files(conn)
    remaining = filter_unprocessed_files(test_files, processed)

    print("\nFiles remaining to process:")
    for f in remaining:
        print(f"  - {f['name']}")

    # 5. Statistics
    stats = get_tracker_stats(conn)
    print(f"\nStatistics: {stats}")

    # 6. Close connection
    conn.close()
