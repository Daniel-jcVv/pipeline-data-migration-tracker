"""
Data Migration Pipeline to Microsoft Fabric

This script implements the complete migration flow:
1. Connect to SFTP (data source)
2. List available files
3. Check which ones have already been processed (file tracker)
4. Download only new files
5. Mark as processed

"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# credentials from .env
config = {
    'sftp': {
        'host': os.getenv('SFTP_HOST'),
        'username': os.getenv('SFTP_USERNAME'),
        'password': os.getenv('SFTP_PASSWORD'),
        'remote_path': os.getenv('SFTP_REMOTE_PATH') 
    },
    'destination': {
        'lakehouse_path': os.getenv('LAKEHOUSE_PATH')
    },
    'tracker': {
        'db_path': os.getenv('TRACKER_DB_PATH')
    }
}



# Import modules
from src.sftp_connector_sv import (
    connect_to_sftp, list_csv_files, download_file, close_connection
)
from src.file_tracker_sv import (
    init_tracker,
    get_processed_files,
    filter_unprocessed_files,
    mark_as_processed,
    get_tracker_stats
)


def print_header():
    """Print program header."""
    print("=" * 70)
    print("  DATA MIGRATION PIPELINE")
    print("  Microsoft Fabric - Data Migration Project")
    print("=" * 70)
    print()


def run_migration_pipeline(config, dry_run=False):
    """
    Execute the complete migration pipeline.

    Args:
        config: Dictionary with configuration (host, username, etc.)
        dry_run: If True, only shows what would be done without executing

    Returns:
        dict: Execution statistics
    """
    stats = {
        'total_files': 0,
        'already_processed': 0,
        'to_process': 0,
        'successfully_processed': 0,
        'failed': 0
    }

    print_header()

    if dry_run:
        print("DRY-RUN MODE: Only showing what would be done\n")

    
    # Step 1: Connect to SFTP
    
    print("STEP 1: Connecting to SFTP server...")
    print("-" * 70)

    sftp = connect_to_sftp(
        host=config['sftp']['host'],
        username=config['sftp']['username'],
        password=config['sftp']['password']
    )

    if not sftp:
        print("Could not connect to SFTP. Aborting.")
        return stats

    print()

    # ========================================
    # STEP 2: List files on SFTP
    # ========================================
    print("STEP 2: Listing files on server...")
    print("-" * 70)

    all_files = list_csv_files(sftp, config['sftp']['remote_path'])
    stats['total_files'] = len(all_files)

    if not all_files:
        print("No CSV files found")
        close_connection(sftp)
        return stats

    print("\nFiles found:")
    for f in all_files:
        print(f"  {f['name']} - {f['size']:,} bytes")

    print()

    # ========================================
    # STEP 3: Check already processed files
    # ========================================
    print("STEP 3: Checking already processed files (File Tracker)...")
    print("-" * 70)

    tracker_conn = init_tracker(config['tracker']['db_path'])
    processed_files = get_processed_files(tracker_conn)
    stats['already_processed'] = len(processed_files)

    if processed_files:
        print("\nAlready processed files:")
        for filename in processed_files:
            print(f"{filename}")
    else:
        print("  (none - first execution)")

    print()

    # ========================================
    # STEP 4: Filter pending files
    # ========================================
    print("STEP 4: Filtering pending files...")
    print("-" * 70)

    files_to_process = filter_unprocessed_files(all_files, processed_files)
    stats['to_process'] = len(files_to_process)

    if not files_to_process:
        print("\nAll files are already processed!")
        print("   Nothing new to migrate.")
        close_connection(sftp)
        tracker_conn.close()
        return stats

    print("\nFiles to be processed:")
    for f in files_to_process:
        print(f" {f['name']}")

    print()

    # If it's dry-run, stop here
    if dry_run:
        print("DRY-RUN: Stopping here. No files were downloaded.")
        close_connection(sftp)
        tracker_conn.close()
        return stats

    # ========================================
    # STEP 5: Process each file
    # ========================================
    print("STEP 5: Processing files...")
    print("-" * 70)

    for idx, file_info in enumerate(files_to_process, 1):
        filename = file_info['name']
        print(f"\n[{idx}/{len(files_to_process)}] Processing: {filename}")

        try:
            # 5a. Download file
            local_path = os.path.join(
                config['destination']['lakehouse_path'], filename
            )
            success = download_file(sftp, file_info['path'], local_path)

            if not success:
                raise Exception("Error downloading file")

            # 5b. Here would go: Load to Warehouse (simulated)
            print("      → Loading to Warehouse... (simulated)")

            # 5c. Mark as processed
            mark_as_processed(
                tracker_conn,
                filename,
                status='LOADED',
                file_size=file_info['size']
            )

            stats['successfully_processed'] += 1
            print(f"      ✓ Completed: {filename}")

        except Exception as e:
            print(f"      ✗ Error: {e}")
            stats['failed'] += 1

            # Mark as failed
            mark_as_processed(
                tracker_conn,
                filename,
                status='FAILED',
                file_size=file_info.get('size')
            )

    print()

    # ========================================
    # STEP 6: Final summary
    # ========================================
    print("=" * 70)
    print("  EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total files at source:       {stats['total_files']}")
    print(f"Already processed before:    {stats['already_processed']}")
    print(f"New files to process:        {stats['to_process']}")
    print(f"Successfully processed:      {stats['successfully_processed']} ✓")
    print(f"Failed:                      {stats['failed']}")
    print()

    # Tracker statistics
    tracker_stats = get_tracker_stats(tracker_conn)
    print("File Tracker Statistics:")
    print(f"  Total tracked files: {tracker_stats['total_files']}")
    print(f"  By status: {tracker_stats['by_status']}")
    print()

    # Close connections
    close_connection(sftp)
    tracker_conn.close()

    return stats


def main():
    """Main function."""

    # Configuration
    config = {
        'sftp': {
            'host': 'localhost',
            'username': 'fabricdata',
            'password': 'FabricMigration2025!',
            'remote_path': '/migration-files/csv/'
        },
        'destination': {
            'lakehouse_path': 'data/lakehouse/bronze/'
        },
        'tracker': {
            'db_path': 'data/file_tracker.db'
        }
    }

    # Check if it's dry-run
    dry_run = '--dry-run' in sys.argv

    # Execute pipeline
    stats = run_migration_pipeline(config, dry_run=dry_run)

    # Exit code
    if stats['failed'] > 0:
        print("Pipeline completed with errors")
        sys.exit(1)
    else:
        print("Pipeline completed successfully")
        sys.exit(0)


if __name__ == '__main__':
    main()
